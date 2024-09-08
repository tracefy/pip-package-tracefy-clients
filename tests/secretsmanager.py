import os
import re
import pytest
import random
import string
import json
import botocore.session
from botocore.stub import Stubber
import TracefyClients.secretsmanager as sm


def response_value(name: str, value: str) -> any:
    return {
        "ARN": f"arn:aws:secretsmanager:region:account-id:secret:{name}-a1b2c3",
        "Name": name,
        "VersionId": "a1b2c3d4-5678-90ab-cdef-EXAMPLEaaaaa",
        "SecretString": value,
        "VersionStages": ["AWSCURRENT"],
        "CreatedDate": 0,
    }


@pytest.fixture
def setup_client():
    client = botocore.session.get_session().create_client("secretsmanager", region_name="test")
    stubber = Stubber(client)
    return (client, stubber)


@pytest.fixture
def secret_fixture() -> (str, any):
    return ("test", response_value("test", '{"host":"localhost","region":"eu"}'))


def test_secretsmanager_multiple_secrets_uses_batch(setup_client):
    (client, stubber) = setup_client
    response = {
        "Errors": [],
        "SecretValues": [
            response_value("secret", '{"username":"john","password":"pass"}'),
            response_value("test", '{"host":"localhost","region":"eu"}'),
        ],
    }

    expected_params = {"SecretIdList": ["secret", "test"]}
    stubber.add_response("batch_get_secret_value", response, expected_params)
    with stubber:
        result = sm.get_values_from_secrets(client, ["secret", "test"])

    expected = {
        "username": "john",
        "password": "pass",
        "host": "localhost",
        "region": "eu",
    }
    assert result == expected


def test_secretsmanager_batch_error(setup_client):
    (client, stubber) = setup_client
    error = {"SecretId": "secret", "ErrorCode": "error_code", "Message": "message"}
    response = {
        "Errors": [error],
        "SecretValues": [response_value("test", '{"host":"localhost"}')],
    }

    secrets = ["secret", "test"]
    expected_params = {"SecretIdList": secrets}
    stubber.add_response("batch_get_secret_value", response, expected_params)

    error_string = '"[{\\"SecretId\\": \\"secret\\", \\"ErrorCode\\": \\"error_code\\", \\"Message\\": \\"message\\"}]"'
    with pytest.raises(
        sm.BatchGetSecretValueError,
        match=re.escape(f"batch_get_secret_value errors: {error_string}"),
    ):
        with stubber:
            result = sm.get_values_from_secrets(client, secrets)


def test_secretsmanager_single_secret_request_use_single_get(setup_client, secret_fixture):
    (client, stubber) = setup_client
    (name, response) = secret_fixture
    expected_params = {"SecretId": name}
    stubber.add_response("get_secret_value", response, expected_params)

    with stubber:
        result = sm.get_values_from_secrets(client, [name])
    assert result == {"host": "localhost", "region": "eu"}


def test_secretsmanager_secret_is_not_json(setup_client, secret_fixture):
    (client, stubber) = setup_client
    (name, response) = secret_fixture
    response["SecretString"] = "bad"
    expected_params = {"SecretId": name}
    stubber.add_response("get_secret_value", response, expected_params)

    with pytest.raises(sm.InvalidSecretValueError):
        with stubber:
            result = sm.get_values_from_secrets(client, [name])


def test_secretsmanager_secret_contains_non_string_value(setup_client, secret_fixture):
    (client, stubber) = setup_client
    (name, response) = secret_fixture
    response["SecretString"] = '{"host": ["localhost"]}'
    expected_params = {"SecretId": name}
    stubber.add_response("get_secret_value", response, expected_params)

    with pytest.raises(sm.InvalidSecretValueError):
        with stubber:
            result = sm.get_values_from_secrets(client, [name])


def test_secretsmanager_loadenv(setup_client, secret_fixture):
    (client, stubber) = setup_client
    (name, response) = secret_fixture
    expected_params = {"SecretId": name}
    stubber.add_response("get_secret_value", response, expected_params)

    # might need to also validate that keys are SCREAM_CASE
    os.environ["host"] = "127.0.0.1"
    assert "region" not in os.environ

    with stubber:
        result = sm.get_values_from_secrets(client, [name])
        sm.load_dictionary_as_env(result, False)
    assert os.environ["host"] == "127.0.0.1"
    assert os.environ["region"] == "eu"

    stubber.add_response("get_secret_value", response, expected_params)
    with stubber:
        result = sm.get_values_from_secrets(client, [name])
        sm.load_dictionary_as_env(result, True)
    assert os.environ["host"] == "localhost"
    assert os.environ["region"] == "eu"


def test_secretsmanager_batch_splitting(setup_client):
    (client, stubber) = setup_client
    secrets = ["".join(random.choice(string.ascii_letters) for _ in range(6)) for _ in range(25)]
    response = [
        {
            "Errors": [],
            "SecretValues": [
                response_value(n, '{{"{0}": "{0}"}}'.format(n))
                for n in secrets[0 : sm.BATCH_SIZE_LIMIT]
            ],
        },
        {
            "Errors": [],
            "SecretValues": [
                response_value(n, '{{"{0}": "{0}"}}'.format(n))
                for n in secrets[sm.BATCH_SIZE_LIMIT :]
            ],
        },
    ]
    expected_params = [
        {"SecretIdList": secrets[0 : sm.BATCH_SIZE_LIMIT]},
        {"SecretIdList": secrets[sm.BATCH_SIZE_LIMIT :]},
    ]
    stubber.add_response("batch_get_secret_value", response[0], expected_params[0])
    stubber.add_response("batch_get_secret_value", response[1], expected_params[1])
    with stubber:
        result = sm.get_values_from_secrets(client, secrets)

    expected = {k: k for k in secrets}
    assert result == expected
