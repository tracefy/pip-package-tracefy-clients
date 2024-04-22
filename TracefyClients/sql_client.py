import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector.abstracts import MySQLCursorAbstract
import threading
import time
import random
from TracefyClients.util import get_logger

load_dotenv()
logger = get_logger("sql_client")


class SQLClient:

    def __init__(self):
        #self.db = mysql.connector.connect(
        #    host=self.get_host(),
        #    user=self.get_user(),
        #    password=self.get_password(),
        #    database=self.get_database(),
        #    port=self.get_port(),
        #    connection_timeout=self.get_connection_timeout(),
        #)

        db_config = {
            "database": self.get_database(),
            "host": self.get_host(),
            "user": self.get_user(),
            "password": self.get_password(),

        }
        pool_name = f"pool_{random.randint(1,100)}"


        self.pool = mysql.connector.pooling.MySQLConnectionPool(
            pool_name=pool_name,
            pool_size=self.get_pool_size(),
            **db_config
        )
        self.pool.get_connection()

        #self.cursor = self.db.cursor(
        #    buffered=True,
        #    dictionary=True
        #)
        #self.cursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")

    def get_connection(self):
        connection = self.pool.get_connection()
        cursor: MySQLCursorAbstract = connection.cursor(buffered=True, dictionary=True)
        cursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED")
        return connection, cursor

    def get_connection_timeout(self) -> int:
        return int(os.getenv("MYSQL_CONNECTION_TIMEOUT", 180))

    def get_port(self) -> int:
        return int(os.getenv("MYSQL_PORT", "3306"))

    def get_user(self) -> str:
        return os.getenv("MYSQL_USER", "mysql")

    def get_password(self) -> str:
        return os.getenv("MYSQL_PASSWORD", "mysql")

    def get_database(self) -> str:
        return os.getenv("MYSQL_DATABASE", "api")

    def get_host(self) -> str:
        return os.getenv("MYSQL_HOST", "localhost")

    def get_pool_size(self) -> int:
        return int(os.getenv("MYSQL_POOL_SIZE", "5"))

    #def start_keep_alive(self, interval=300):
    #    self.keep_alive_thread = threading.Thread(target=self._keep_alive, args=(interval,), daemon=True)
    #    self.keep_alive_thread.start()

    #def _keep_alive(self, interval):
    #    while True:
    #        try:
    #            self.db.ping(reconnect=True, attempts=3, delay=5)
    #            logger.info("Database pinged to keep the connection alive.")
    #        except Exception as e:
    #            logger.error(f"Error keeping the database alive: {e}")

    #        time.sleep(interval)

    def log(self, cursor: MySQLCursorAbstract):
        logger.info("Query {}".format(cursor.statement))
        logger.info("Affected rows: {}".format(cursor.rowcount))

    def update(self, query: str, params: tuple):
        connection, cursor = self.get_connection()

        cursor.execute(query, params)
        connection.commit()
        self.log(cursor)

        cursor.close()
        connection.close()

    def execute(self, query: str, multi=False):
        connection, cursor = self.get_connection()

        cursor.execute(query, multi=multi)
        connection.commit()
        self.log(cursor)

        cursor.close()
        connection.close()

    def fetch_all(self, query: str, params=()) -> dict:
        connection, cursor = self.get_connection()

        cursor.execute(query, params)
        data = cursor.fetchall()

        cursor.close()
        connection.close()

        return data

    def insert(self, keys: tuple, values: tuple, table: str):
        connection, cursor = self.get_connection()

        key_str = ", ".join([f"`{key}`" for key in keys])  
        val_str = ", ".join(["%s"] * len(keys))
        q = f"INSERT INTO {table} ({key_str}) VALUES ({val_str})"
        cursor.execute(q, values)
        connection.commit()
        self.log(cursor)

        cursor.close()
        connection.close()

    def fetch_one(self, query: str, params=None) -> dict:
        connection, cursor = self.get_connection()

        cursor.execute(query, params)
        data = cursor.fetchone()

        cursor.close()
        connection.close()
        return data

    def get_tables(self) -> list:
        connection, cursor = self.get_connection()

        cursor.execute("SHOW TABLES")
        tables = [table['Tables_in_' + os.getenv("REMOTE_MYSQL_DATABASE", "api")] for table in cursor.fetchall()]

        tables = [b.decode() for b in tables]

        cursor.close()
        connection.close()

        return tables

    def get_create_table_sql(self, table_name: str) -> str | None:
        query = f"DESCRIBE {table_name}"
        columns_info = self.fetch_all(query)

        if not columns_info:
            return None

        column_definitions = []
        for column_info in columns_info:
            column_name = column_info['Field']
            column_type = column_info['Type']
            if isinstance(column_type, bytes):
                column_type = column_type.decode()
            column_definitions.append(f"{column_name} {column_type}")

        drop_table_sql = f"DROP TABLE IF EXISTS {table_name};\n"
        create_table_sql = f"CREATE TABLE {table_name} (\n"
        create_table_sql += ",\n".join(column_definitions)
        create_table_sql += "\n);"

        return drop_table_sql + create_table_sql

    def update(self, keys: tuple, values: tuple, table: str, condition: str):
        connection, cursor = self.get_connection()

        key_val_pairs = [f"{key} = %s" for key in keys]
        set_clause = ", ".join(key_val_pairs)
        q = f"UPDATE {table} SET {set_clause} WHERE {condition}"
        update_values = values + condition_values  # Add condition values to the update values
        cursor.execute(q, update_values)
        connection.commit()
        self.log(cursor)

        cursor.close()
        connection.close()

