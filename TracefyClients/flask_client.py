import logging
from flask import Flask, request

import sentry_sdk
import os
from flask_cors import CORS
from sentry_sdk.integrations.flask import FlaskIntegration

from werkzeug.middleware.proxy_fix import ProxyFix

from dotenv import load_dotenv

load_dotenv()


class FlaskClient:
    debug = None

    def __init__(self):
        self._setup_sentry()

    def _setup_sentry(self):
        sentry_dsn = os.getenv("SENTRY_DSN")
        sentry_rate = os.getenv("SENTRY_RATE", 1.0)
        if sentry_dsn:
            sentry_sdk.init(
                dsn=sentry_dsn,
                integrations=[
                    FlaskIntegration(),
                ],

                # Set traces_sample_rate to 1.0 to capture 100%
                # of transactions for performance monitoring.
                # We recommend adjusting this value in production.
                traces_sample_rate=sentry_rate,
            )

    def get_client(self):
        if not self.get_debug():
            log = logging.getLogger('werkzeug')
            log.setLevel(logging.ERROR)
        app = Flask(__name__)
        CORS(app)
        if not self.get_debug():
            app.wsgi_app = ProxyFix(
                app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
            )

        if not self.get_debug():
            print("Disabling favicon log")

            @app.before_request
            def suppress_favicon_log():
                if request.path == '/favicon.ico':
                    log = logging.getLogger('werkzeug')
                    log.disabled = True

            @app.after_request
            def enable_favicon_log(response):
                if request.path == '/favicon.ico':
                    log = logging.getLogger('werkzeug')
                    log.disabled = False
                return response

        return app

    def get_port(self) -> int:
        return int(os.getenv("PORT", "5033"))

    def get_host(self) -> int:
        return os.getenv("HOST", '0.0.0.0')

    def get_base_url(self) -> str:
        return f"http://{self.get_host()}:{self.get_port()}"

    def get_debug(self) -> bool:
        if self.debug == None:
            self.debug = False
            try:
                debug = os.getenv("DEBUG", "False") == "True"
                if debug:
                    print("Debugging enabled")
                    self.debug = bool(debug)
            except ValueError:
                self.debug = False
        return self.debug
