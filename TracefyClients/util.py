import logging

def get_logger(name: str) -> logging.LoggerAdapter:
    extra = {'app_name': name}
    logger = logging.getLogger(__name__)
    syslog = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s %(app_name)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    syslog.setFormatter(formatter)
    logger.setLevel(logging.INFO)
    logger.addHandler(syslog)
    logger = logging.LoggerAdapter(logger, extra)
    return logger