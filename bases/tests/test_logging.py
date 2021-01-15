import bases


class TestLogger(bases.helpers.AsyncTestCaseWithPathing):
    def test_log(self):
        logger = bases.logging.logger
        logger.trace(msg="TESTING LOGGER")
        logger.debug(msg="TESTING LOGGER")
        logger.success(msg="TESTING LOGGER")
        logger.info(msg="TESTING LOGGER")
        logger.warning(msg="TESTING LOGGER")
        logger.error(msg="TESTING LOGGER")
        logger.critical(msg="TESTING LOGGER")
