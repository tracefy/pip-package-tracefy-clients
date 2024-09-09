import json
import os
import re
from base64 import b64decode
from typing import Any, Dict, List, Optional, final

import boto3
from mypy_boto3_secretsmanager.client import SecretsManagerClient
from mypy_boto3_secretsmanager.type_defs import (
    APIErrorTypeTypeDef,
    BatchGetSecretValueResponseTypeDef,
    GetSecretValueResponseTypeDef,
    SecretValueEntryTypeDef,
)

BATCH_SIZE_LIMIT = 20
DEFAULT_ENVKEY = "AWS_SECRETSMANAGER_SECRET_IDS"

@final
class InvalidSecretValueError(ValueError):
    def __init__(self, secret_arn: str):
        msg = f"secret {secret_arn} contains a value that is not a string or is not a valid json object"
        return super(InvalidSecretValueError, self).__init__(msg)

@final
class BatchGetSecretValueError(RuntimeError):
    def __init__(self, errors: List[APIErrorTypeTypeDef]):
        msg = f"batch_get_secret_value errors: {json.dumps(json.dumps(errors))}"
        return super(BatchGetSecretValueError, self).__init__(msg)


# might use pydantic for this in the future
def is_valid_secret_value(value: Dict[str, Any]) -> bool:
    if not isinstance(value, dict):
        return False
    return all(isinstance(v, str) for v in value.values())


def parse_secret_value(
    value: SecretValueEntryTypeDef | GetSecretValueResponseTypeDef,
) -> Dict[str, str]:
    """
    Returns a decoded dictionary of the key value pairs contained inside a secret
    Raises exceptions if the value is not valid json object or if the dictionary contains
    non-string values
    """

    try:
        is_string = "SecretString" in value
        data: str | bytes = value["SecretString"] if is_string else b64decode(value["SecretBinary"])
        ret = json.loads(data)
    except ValueError:
        raise InvalidSecretValueError(value["ARN"])
    if not is_valid_secret_value(ret):
        raise InvalidSecretValueError(value["ARN"])
    return ret


def parse_batch_response(
    response: BatchGetSecretValueResponseTypeDef,
) -> Dict[str, str]:
    result = {}
    for value in response.get("SecretValues", []):
        result.update(parse_secret_value(value))
    errors = response.get("Errors", [])
    if len(errors) > 0:
        raise BatchGetSecretValueError(errors)
    return result


def get_secret_value(client: SecretsManagerClient, secret: str) -> Dict[str, str]:
    response = client.get_secret_value(SecretId=secret)
    return parse_secret_value(response)


def batch_get_secret_value(client: SecretsManagerClient, secrets: List[str]) -> Dict[str, str]:
    response = client.batch_get_secret_value(SecretIdList=secrets)
    return parse_batch_response(response)


def get_values_from_secrets(client: SecretsManagerClient, secrets: List[str]) -> Dict[str, str]:
    """
    Only support for aws/secretsmanager encrypted secrets
    Required permissions
      secretsmanager:BatchGetSecretValue
      secretsmanager:GetSecretValue (for each secret)

    If two secrets have the same key they will overwrite each other.
    The order of overwrites are may not be in the same order that the secrets occur in the list
    so make sure there are no conflicting keys between two secrets
    """

    if len(secrets) == 1:
        return get_secret_value(client, secrets[0])

    chunks = (secrets[x : x + BATCH_SIZE_LIMIT] for x in range(0, len(secrets), BATCH_SIZE_LIMIT))
    results = (batch_get_secret_value(client, chunk) for chunk in chunks)
    return {k: v for r in results for k, v in r.items()}


def load_dictionary_as_env(env: Dict[str, str], overwrite_existing_keys: bool):
    """Set environment values from envmap dictionary"""

    if overwrite_existing_keys:
        for key, value in env.items():
            os.environ[key] = value
        return

    for key, value in env.items():
        if key in os.environ:
            continue
        os.environ[key] = value


def secretsmanager_values(secrets: Optional[List[str]] = None, region_name: Optional[str] = None):
    """
    Returns a dictionary of the merged secret values found inside the comma separated
    environment variable (default is AWS_SECRETSMANAGER_SECRET_IDS)

    Call secretsmanager_values at the start of your application to use the secrets to configure
    other for example other API clients
    """

    if secrets is None:
        if DEFAULT_ENVKEY not in os.environ:
            raise RuntimeError(f"parameter secrets and {DEFAULT_ENVKEY} not set")
        secret_id = os.environ[DEFAULT_ENVKEY]
        secrets = [e.strip() for e in secret_id.split(",")]

    client = boto3.client("secretsmanager", region_name=region_name)
    return get_values_from_secrets(client, secrets)


def secretsmanager_loadenv(
    secrets: Optional[List[str]] = None,
    region_name: Optional[str] = None,
    overwrite_existing_keys: bool = False,
):
    """
    Loads key value pairs defined in the secret ids inside the comma separated
    environment variable (default is AWS_SECRETSMANAGER_SECRET_IDS)

    Call secretsmanager_loadenv at the start of your application
    """

    env = secretsmanager_values(secrets, region_name)
    load_dictionary_as_env(env, overwrite_existing_keys)
