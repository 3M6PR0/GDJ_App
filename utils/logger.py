import logging

def setup_logger(name=__name__, level=logging.DEBUG):
    logger = logging.getLogger(name)
    if not logger.handlers:
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    logger.setLevel(level)
    return logger
