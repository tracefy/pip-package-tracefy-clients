import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector.abstracts import MySQLCursorAbstract
import random
import time

from mysql.connector.pooling import PooledMySQLConnection
from TracefyClients.logging import Logging

load_dotenv()
logger = Logging("sql_client").get_logger()


class SQLClient:

    def __init__(self, db_config: dict|None=None):

        if not db_config: 
            db_config = {
                "database": os.getenv("MYSQL_DATABASE", "api"),
                "host": os.getenv("MYSQL_HOST", "localhost"),
                "port": int(os.getenv("MYSQL_PORT", "3306")),
                "user": os.getenv("MYSQL_USER", "mysql"),
                "password": os.getenv("MYSQL_PASSWORD", "mysql"),
            }

        pool_name = f"pool_{random.randint(1,100)}" # get a random name

        self.pool = mysql.connector.pooling.MySQLConnectionPool(
            pool_name=pool_name,
            pool_size=int(os.getenv("MYSQL_POOL_SIZE", "3")),
            **db_config
        )

        self.max_retries = int(os.getenv("MYSQL_POOL_RETRIES", "5"))
        self.wait_interval = float(os.getenv("MYSQL_POOL_WAIT_INTERVAL", "0.5"))
    
    def get_connection(self):
        """
        Get a connection from the connection pool
        """
        retries = 0
        while retries < self.max_retries:
            try:
                connection = self.pool.get_connection()
                break
            except mysql.connector.errors.PoolError:
                retries += 1
                time.sleep(self.wait_interval)
                print(f"connection pool exausted! Retries: {retries} with timeout: {self.wait_interval} sec")

        cursor: MySQLCursorAbstract = connection.cursor(buffered=True, dictionary=True)
        return connection, cursor

    def close_connection(self, connection: PooledMySQLConnection, cursor: MySQLCursorAbstract):
        """
        Give back the cursor and connection tool the pool
        """

        cursor.close()
        connection.close()


    def log(self, cursor: MySQLCursorAbstract):
        logger.info("Query {}".format(cursor.statement))
        logger.info("Affected rows: {}".format(cursor.rowcount))

    def update(self, query: str, params: tuple):
        connection, cursor = self.get_connection()

        cursor.execute(query, params)
        connection.commit()
        self.log(cursor)

        self.close_connection(connection, cursor)

    def execute(self, query: str, params=(), multi=False):
        connection, cursor = self.get_connection()

        cursor.execute(query, params=params, multi=multi)
        connection.commit()
        self.log(cursor)

        self.close_connection(connection, cursor)

    def execute_transaction(self, query_list: list[str], params: list[tuple]):
        connection, cursor = self.get_connection()
        results = []
        try:
            for query, param in zip(query_list, params):
                result = cursor.execute(query, param)
                results.append(result)
            connection.commit()
            self.log(cursor)
        except mysql.connector.Error as e:
            connection.rollback()
            raise e
        finally:
            self.close_connection(connection, cursor)
        return results

    def fetch_all(self, query: str, params=()):
        connection, cursor = self.get_connection()

        cursor.execute(query, params)
        data = cursor.fetchall()

        self.close_connection(connection, cursor)
        return data

    def insert(self, keys: tuple, values: tuple, table: str):
        key_str = ", ".join([f"`{key}`" for key in keys])  
        val_str = ", ".join(["%s"] * len(keys))
        q = f"INSERT INTO {table} ({key_str}) VALUES ({val_str})"
        connection, cursor = self.get_connection()

        cursor.execute(q, values)
        connection.commit()
        self.log(cursor)

        self.close_connection(connection, cursor)

    def fetch_one(self, query: str, params=()):
        connection, cursor = self.get_connection()
        cursor.execute(query, params)

        data = cursor.fetchone()

        self.close_connection(connection, cursor)
        return data


    def get_tables(self) -> list:
        connection, cursor = self.get_connection()

        cursor.execute("SHOW TABLES")
        tables = [table['Tables_in_' + os.getenv("REMOTE_MYSQL_DATABASE", "api")] for table in cursor.fetchall()]

        tables = [b.decode() for b in tables]

        self.close_connection(connection, cursor)
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

