from fastapi_mongodb.logging import logger


def test_logging():
    logger.trace(msg="TRACE MESSAGE")
    logger.debug(msg="DEBUG MESSAGE")
    logger.info(msg="INFO MESSAGE")
    logger.success(msg="SUCCESS MESSAGE")
    logger.warning(msg="WARNING MESSAGE")
    logger.error(msg="ERROR MESSAGE")
    logger.critical(msg="CRITICAL MESSAGE")
