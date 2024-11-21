import os
import logging
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration


class Logging:
    def __init__(self, name: str = "Logger"):
        """
        Initialize a logger with a given name and configuration.
        :param name: Name of the logger.
        """
        debug = os.getenv("DEBUG", False).lower() == "true"
        self.is_testing = os.environ.get("TESTING", False).lower() == "true"
        self.log_level = logging.DEBUG if debug else logging.INFO

        if not self.is_testing:
            try:
                sentry_dsn = os.getenv("SENTRY_DSN")
                if sentry_dsn:
                    sentry_sdk.init(
                        dsn=sentry_dsn,
                        integrations=[
                            LoggingIntegration(level=logging.INFO, event_level=logging.ERROR)
                        ],
                    )
            except Exception as e:
                print(f"Sentry initialization error: {e}")

        self.logger = logging.getLogger(name)
        self.logger.setLevel(self.log_level)
        self.logger.propagate = False
        self.add_console_handler()

    def add_console_handler(self, level=None):
        """
        Add a console handler to the logger.
        :param level: Logging level for the console handler.
        """
        log_level = level if level else self.log_level
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S"
        )

        if self.is_testing:
            formatter = logging.Formatter(
                "TESTING - %(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )

        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def get_logger(self):
        return self.logger

