import os
from dotenv import load_dotenv
import mysql.connector
import threading
import time

load_dotenv()


class SQLClient:

    def __init__(self):
        self.db = mysql.connector.connect(
            host=self.get_host(),
            user=self.get_user(),
            password=self.get_password(),
            database=self.get_database(),
            port=self.get_port(),
            connection_timeout=self.get_connection_timeout(),
        )
        self.cursor = self.db.cursor(
            buffered=True,
            dictionary=True
        )

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

    def start_keep_alive(self, interval=300):
        self.keep_alive_thread = threading.Thread(target=self._keep_alive, args=(interval,), daemon=True)
        self.keep_alive_thread.start()

    def _keep_alive(self, interval):
        while True:
            try:
                self.db.ping(reconnect=True, attempts=3, delay=5)
                print("Database pinged to keep the connection alive.")
            except Exception as e:
                print(f"Error keeping the database alive: {e}")

            time.sleep(interval)

    def log(self):
        print("Query {}".format(self.cursor.statement))
        print("Affected rows: {}".format(self.cursor.rowcount))

    def update(self, query: str, params: tuple):
        self.cursor.execute(query, params)
        self.db.commit()
        self.log()

    def execute(self, query: str, multi=False):
        self.cursor.execute(query, multi=multi)
        self.db.commit()
        self.log()

    def fetch_all(self, query: str, params=None) -> dict:
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def insert(self, keys: tuple, values: tuple, table: str):
        key_str = ", ".join(keys)
        val_str = ", ".join(["%s"] * len(keys))
        q = f"INSERT INTO {table} ({key_str}) VALUES ({val_str})"
        self.cursor.execute(q, values)
        self.db.commit()
        self.log()

    def fetch_one(self, query: str, params=None) -> dict:
        self.cursor.execute(query, params)
        return self.cursor.fetchone()

    def get_tables(self) -> list:
        self.cursor.execute("SHOW TABLES")
        tables = [table['Tables_in_' + os.getenv("REMOTE_MYSQL_DATABASE", "api")] for table in self.cursor.fetchall()]

        tables = [b.decode() for b in tables]

        return tables

    def get_create_table_sql(self, table_name: str) -> str:
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
