import copy
import functools
import logging

import click

import settings

__all__ = ["logger"]

TRACE = 5
SUCCESS = 25


COLORS = {
    TRACE: lambda data: click.style(text=str(data), fg="blue"),
    logging.DEBUG: lambda data: click.style(text=str(data), fg="white"),
    logging.INFO: lambda data: click.style(text=str(data), fg="bright_blue"),
    SUCCESS: lambda data: click.style(text=str(data), fg="green"),
    logging.WARNING: lambda data: click.style(text=str(data), fg="bright_yellow"),
    logging.ERROR: lambda data: click.style(text=str(data), fg="bright_red"),
    logging.CRITICAL: lambda data: click.style(text=str(data), fg="magenta", bold=True, underline=True),
}


class DebugFormatter(logging.Formatter):
    def formatMessage(self, record: logging.LogRecord) -> str:
        record_copy = copy.copy(record)
        record_copy.__dict__["message"] = COLORS[record_copy.levelno](record_copy.__dict__["message"])
        record_copy.__dict__["filename"] = click.style(text=str(record_copy.__dict__["filename"]), fg="cyan")
        record_copy.__dict__["lineno"] = click.style(
            text=str(record_copy.__dict__["lineno"]), fg="blue", underline=True
        )
        record_copy.__dict__["created"] = click.style(text=str(record_copy.__dict__["created"]), fg="cyan")
        record_copy.__dict__["asctime"] = click.style(text=str(record_copy.__dict__["asctime"]), fg="cyan")
        separator = " " * (8 - len(record_copy.__dict__["levelname"]))
        record_copy.__dict__["levelname"] = (
            COLORS[record_copy.__dict__["levelno"]](record_copy.__dict__["levelname"])
            + click.style(text=":", fg="cyan")
            + separator
        )
        return super().formatMessage(record=record_copy)


@functools.lru_cache()
def setup_logging():
    """Setup logging formatter"""
    raw_format = "%(levelname)s %(message)s (%(created)s | %(asctime)s)"
    debug_format = "{raw_format}\n{file_format}%(pathname)s{line_format}%(lineno)s".format(
        raw_format=raw_format,
        file_format=click.style(text='╰───📃File "', fg="bright_white", bold=True),
        line_format=click.style(text='", line ', fg="bright_white", bold=True),
    )
    logging.addLevelName(level=TRACE, levelName="TRACE")
    logging.addLevelName(level=SUCCESS, levelName="SUCCESS")
    if settings.Settings.DEBUG:
        formatter = DebugFormatter(fmt=debug_format)
    else:  # pragma: no cover
        formatter = logging.Formatter(fmt=raw_format)

    handler = logging.StreamHandler()
    handler.setFormatter(fmt=formatter)
    handler.setLevel(level=settings.Settings.LOGGER_LEVEL)

    main_logger = logging.getLogger(name=settings.Settings.LOGGER_NAME)
    main_logger.setLevel(level=settings.Settings.LOGGER_LEVEL)
    main_logger.addHandler(hdlr=handler)

    def _trace(msg, **kwargs):
        main_logger.log(level=TRACE, msg=msg, **kwargs)

    def _success(msg, **kwargs):
        main_logger.log(level=SUCCESS, msg=msg, **kwargs)

    main_logger.trace = _trace
    main_logger.success = _success

    return main_logger


logger = setup_logging()
