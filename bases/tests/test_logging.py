from bases.helpers import AsyncTestCase
from bases.logging import TRACE, logger


class TestLogger(AsyncTestCase):
    def test_log(self):
        with self.assertLogs(logger=logger, level=TRACE) as logger_context:
            logger.trace(msg="TESTING TRACE")
            logger.debug(msg="TESTING DEBUG")
            logger.success(msg="TESTING SUCCESS")
            logger.info(msg="TESTING INFO")
            logger.warning(msg="TESTING WARNING")
            logger.error(msg="TESTING ERROR")
            logger.critical(msg="TESTING CRITICAL")
        self.assertEqual(
            [
                f"TRACE:{logger.name}:TESTING TRACE",
                f"DEBUG:{logger.name}:TESTING DEBUG",
                f"SUCCESS:{logger.name}:TESTING SUCCESS",
                f"INFO:{logger.name}:TESTING INFO",
                f"WARNING:{logger.name}:TESTING WARNING",
                f"ERROR:{logger.name}:TESTING ERROR",
                f"CRITICAL:{logger.name}:TESTING CRITICAL",
            ],
            logger_context.output,
        )
