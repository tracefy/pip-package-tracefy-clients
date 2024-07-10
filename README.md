# TracefyClients

TracefyClients is a Python package that provides client implementations for various backend services commonly used in
web applications. It includes clients for interacting with AWS DynamoDB, MySQL databases, and integrates with the Flask
web framework.

## Installation

You can install TracefyClients using pip:

```bash
pip install TracefyClients
``` 

Make sure to have the required dependencies listed in requirements.txt installed as well.

## Usage

### DynamoDB Client

The DynamoDBClient class allows you to interact with AWS DynamoDB. You can initialize it with your AWS credentials and
other configurations:

```python
from TracefyClients.dynamo_db_client import DynamoDBClient

# Initialize the client
db_client = DynamoDBClient()

# Put an item into the DynamoDB table
waypoint = {"id": "123", "name": "Sample Waypoint"}
db_client.put_item(waypoint)
```

### Flask Client

The FlaskClient class sets up a Flask application with CORS support and integrates with Sentry for error monitoring. You
can create an instance and configure the Flask app:

```python
from TracefyClients.flask_client import FlaskClient

# Initialize the Flask app
flask_client = FlaskClient()
app = flask_client.get_client()

# Define your routes and application logic here
```

### SQL Client

The SQLClient class provides a client for MySQL databases. You can use it to execute SQL queries and fetch data:

```python
from TracefyClients.sql_client import SQLClient

# Initialize the SQL client
sql_client = SQLClient()

# Execute a SQL query
query = "SELECT * FROM users WHERE username = %s"
params = ("john_doe",)
result = sql_client.fetch_one(query, params)
```

### SQS Client
the SQSClient class creates a boto3 resource and a queue object that is used to receive and send messages to SQS
#### SQS variables
* AWS_SQS_ENDPOINT_URL
* AWS_REGION
* AWS_ACCESS_KEY_ID
* AWS_SECRET_ACCESS_KEY
```python
from TracefyClients.sql_client import SQSClient

# Initialize the SQS client
sqs_client = SQSClient()

# get amount of messsages in the queue
num_messages = sqs_client.messages_in_queue()
# Loop through the amount of messages in the queue and decompress_message
for _ in range(num_messages):
    msg = sqs_client.get_messages()[0]
    data = sqs_client.decompress_message(msg)
    do_something_special_with_msg(data)

    #Be sure to remove the message when done
    msg.delete()

```


## Configuration

You can configure the clients by setting environment variables or using a .env file. Refer to the respective client
files for available configuration options.

### SQL variables
* MYSQL_DATABASE
* MYSQL_HOST
* MYSQL_PORT
* MYSQL_USER
* MYSQL_PASSWORD
* MYSQL_POOL_SIZE           The size of the connection pool used, default 5 connections
* MYSQL_POOL_RETRIES        The amount of retries when getting a connection from the pool fails, default 5 retries
* MYSQL_POOL_WAIT_INTERVAL  The time between the retries, default 0.5 seconds

## License

This project is licensed under the MIT License.
