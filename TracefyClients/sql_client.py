import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector.abstracts import MySQLCursorAbstract
import random
from TracefyClients.util import get_logger

load_dotenv()
logger = get_logger("sql_client")


class SQLClient:

    def __init__(self):

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
            pool_size=int(os.getenv("MYSQL_POOL_SIZE", "5")),
            **db_config
        )
        self.pool.get_connection()
    
    def __enter__(self):
        # Get a connection from the pool
        self.connection = self.pool.get_connection()
        self.cursor: MySQLCursorAbstract = self.connection.cursor()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # Commit transactions if no exceptions, otherwise rollback
        if exc_type is None:
            self.connection.commit()
        else:
            self.connection.rollback()
        
        # Close the cursor and connection
        self.cursor.close()
        self.connection.close()


    def log(self):
        logger.info("Query {}".format(self.cursor.statement))
        logger.info("Affected rows: {}".format(self.cursor.rowcount))

    def update(self, query: str, params: tuple):

        self.cursor.execute(query, params)
        self.connection.commit()
        self.log()

    def execute(self, query: str, multi=False):
        self.cursor.execute(query, multi=multi)
        self.connection.commit()
        self.log()


    def fetch_all(self, query: str, params=()) -> dict:
        self.cursor.execute(query, params)
        return self.cursor.fetchall()


    def insert(self, keys: tuple, values: tuple, table: str):
        key_str = ", ".join([f"`{key}`" for key in keys])  
        val_str = ", ".join(["%s"] * len(keys))
        q = f"INSERT INTO {table} ({key_str}) VALUES ({val_str})"
        self.cursor.execute(q, values)
        self.connection.commit()
        self.log()

    def fetch_one(self, query: str, params=()) -> dict:
        self.cursor.execute(query, params)
        return self.cursor.fetchone()


    def get_tables(self) -> list:
        self.cursor.execute("SHOW TABLES")
        tables = [table['Tables_in_' + os.getenv("REMOTE_MYSQL_DATABASE", "api")] for table in self.cursor.fetchall()]

        tables = [b.decode() for b in tables]
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

