import logging

LOG_FORMAT = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"


def configure_logging(level: str) -> None:
    # Configures only the application's "src" logger tree: uvicorn keeps its own
    # access/error loggers, and the root logger is left alone for tools such as pytest.
    app_logger = logging.getLogger("src")
    app_logger.setLevel(level)
    if not app_logger.handlers:  # create_app may run more than once (tests, reload)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        app_logger.addHandler(handler)
