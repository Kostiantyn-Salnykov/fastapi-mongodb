import bases


class TestLogger(bases.helpers.AsyncTestCaseWithPathing):
    def test_log(self):
        logger = bases.logging.logger
        logger.trace(msg="TESTING LOGGER")
        logger.debug("TESTING LOGGER")
        logger.success(msg="TESTING LOGGER")
        logger.info("TESTING LOGGER")
        logger.warning("TESTING LOGGER")
        logger.error("TESTING LOGGER")
        logger.critical("TESTING LOGGER")
