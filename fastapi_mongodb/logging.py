import copy
import enum
import functools
import logging
import typing
from typing import Union

import click

__all__ = ["logger", "simple_logger", "setup_logging"]

TRACE = 5
SUCCESS = 25


class Colors(str, enum.Enum):
    RED = "red"
    GREEN = "green"
    ORANGE = "yellow"
    BLUE = "blue"
    MAGENTA = "magenta"
    CYAN = "cyan"
    GRAY = "black"
    LIGHT_GRAY = "white"
    BRIGHT_BLACK = "bright_black"
    BRIGHT_RED = "bright_red"
    BRIGHT_GREEN = "bright_green"
    BRIGHT_YELLOW = "bright_yellow"
    BRIGHT_BLUE = "bright_blue"
    BRIGHT_MAGENTA = "bright_magenta"
    BRIGHT_CYAN = "bright_cyan"
    WHITE = "bright_white"
    CLEAR = "reset"


class Red(tuple[int], enum.Enum):
    RED = (244, 67, 54)
    RED_1 = (255, 235, 238)
    RED_2 = (254, 205, 210)
    RED_3 = (239, 154, 154)
    RED_4 = (229, 115, 115)
    RED_5 = (239, 83, 80)
    RED_6 = (244, 67, 54)
    RED_7 = (229, 57, 52)
    RED_8 = (211, 47, 47)
    RED_9 = (198, 40, 40)
    RED_10 = (183, 28, 28)


class Pink(tuple[int], enum.Enum):
    PINK = (233, 31, 99)
    PINK_1 = (252, 228, 236)
    PINK_2 = (248, 187, 208)
    PINK_3 = (244, 143, 177)
    PINK_4 = (239, 98, 146)
    PINK_5 = (236, 64, 121)
    PINK_6 = (233, 31, 99)
    PINK_7 = (216, 28, 96)
    PINK_8 = (194, 25, 92)
    PINK_9 = (173, 21, 87)
    PINK_10 = (136, 15, 79)


class Purple(tuple[int], enum.Enum):
    PURPLE = (156, 39, 176)
    PURPLE_1 = (243, 228, 245)
    PURPLE_2 = (225, 190, 231)
    PURPLE_3 = (206, 147, 216)
    PURPLE_4 = (186, 104, 200)
    PURPLE_5 = (171, 73, 188)
    PURPLE_6 = (156, 39, 176)
    PURPLE_7 = (142, 36, 170)
    PURPLE_8 = (123, 31, 163)
    PURPLE_9 = (106, 27, 154)
    PURPLE_10 = (74, 20, 140)


class DeepPurple(tuple[int], enum.Enum):
    DEEP_PURPLE = (103, 58, 183)
    DEEP_PURPLE_1 = (237, 231, 246)
    DEEP_PURPLE_2 = (209, 196, 233)
    DEEP_PURPLE_3 = (178, 157, 219)
    DEEP_PURPLE_4 = (149, 117, 205)
    DEEP_PURPLE_5 = (126, 87, 194)
    DEEP_PURPLE_6 = (103, 58, 183)
    DEEP_PURPLE_7 = (94, 53, 177)
    DEEP_PURPLE_8 = (81, 45, 167)
    DEEP_PURPLE_9 = (69, 39, 160)
    DEEP_PURPLE_10 = (49, 27, 146)


class Indigo(tuple[int], enum.Enum):
    INDIGO = (63, 81, 181)
    INDIGO_1 = (232, 234, 246)
    INDIGO_2 = (197, 202, 233)
    INDIGO_3 = (159, 168, 218)
    INDIGO_4 = (121, 134, 203)
    INDIGO_5 = (92, 107, 192)
    INDIGO_6 = (63, 81, 181)
    INDIGO_7 = (57, 73, 171)
    INDIGO_8 = (48, 63, 159)
    INDIGO_9 = (39, 53, 147)
    INDIGO_10 = (26, 35, 126)


class Blue(tuple[int], enum.Enum):
    BLUE = (33, 150, 243)
    BLUE_1 = (227, 242, 253)
    BLUE_2 = (187, 222, 251)
    BLUE_3 = (143, 202, 249)
    BLUE_4 = (99, 181, 246)
    BLUE_5 = (66, 165, 245)
    BLUE_6 = (33, 150, 243)
    BLUE_7 = (30, 136, 229)
    BLUE_8 = (25, 118, 210)
    BLUE_9 = (21, 101, 192)
    BLUE_10 = (13, 71, 161)


class LightBlue(tuple[int], enum.Enum):
    LIGHT_BLUE = (7, 169, 244)
    LIGHT_BLUE_1 = (225, 245, 254)
    LIGHT_BLUE_2 = (179, 229, 252)
    LIGHT_BLUE_3 = (129, 212, 250)
    LIGHT_BLUE_4 = (79, 195, 247)
    LIGHT_BLUE_5 = (41, 182, 246)
    LIGHT_BLUE_6 = (7, 169, 244)
    LIGHT_BLUE_7 = (4, 155, 229)
    LIGHT_BLUE_8 = (1, 136, 209)
    LIGHT_BLUE_9 = (2, 119, 189)
    LIGHT_BLUE_10 = (1, 87, 155)


class Cyan(tuple[int], enum.Enum):
    CYAN = (25, 188, 212)
    CYAN_1 = (223, 247, 250)
    CYAN_2 = (178, 235, 242)
    CYAN_3 = (128, 222, 234)
    CYAN_4 = (77, 208, 225)
    CYAN_5 = (38, 198, 218)
    CYAN_6 = (25, 188, 212)
    CYAN_7 = (22, 172, 193)
    CYAN_8 = (18, 151, 166)
    CYAN_9 = (15, 131, 143)
    CYAN_10 = (9, 96, 100)


class Gray(tuple[int], enum.Enum):
    GRAY = (158, 158, 158)
    GRAY_1 = (250, 250, 250)
    GRAY_2 = (245, 245, 245)
    GRAY_3 = (238, 238, 238)
    GRAY_4 = (224, 224, 224)
    GRAY_5 = (189, 189, 189)
    GRAY_6 = (158, 158, 158)
    GRAY_7 = (117, 117, 117)
    GRAY_8 = (97, 97, 97)
    GRAY_9 = (66, 66, 66)
    GRAY_10 = (33, 33, 33)


class Brown(tuple[int], enum.Enum):
    BROWN = (121, 85, 72)
    BROWN_1 = (239, 235, 233)
    BROWN_2 = (215, 204, 200)
    BROWN_3 = (188, 170, 164)
    BROWN_4 = (161, 136, 127)
    BROWN_5 = (141, 110, 99)
    BROWN_6 = (121, 85, 72)
    BROWN_7 = (109, 76, 65)
    BROWN_8 = (94, 64, 55)
    BROWN_9 = (78, 52, 46)
    BROWN_10 = (62, 39, 35)


class Palette:
    COLORS = Colors
    GRAY = Gray
    RED = Red
    PINK = Pink
    PURPLE = Purple
    DEEP_PURPLE = DeepPurple
    INDIGO = Indigo
    BLUE = Blue
    LIGHT_BLUE = LightBlue
    CYAN = Cyan
    BROWN = Brown


class Styler:
    def __init__(self, override_kwargs: list[dict[typing.Union[int, str], typing.Any]] = None):
        self.colors_map: dict[int, functools.partial] = {}  # {<level>: <partial_func from style>, ...}
        _default_kwargs = [
            {"level": TRACE, "fg": Palette.GRAY.GRAY_6},
            {"level": logging.DEBUG, "fg": Palette.BROWN.BROWN_6},
            {"level": logging.INFO, "fg": Palette.COLORS.BRIGHT_BLUE},
            {"level": SUCCESS, "fg": Palette.COLORS.GREEN},
            {"level": logging.WARNING, "fg": Palette.COLORS.BRIGHT_YELLOW},
            {"level": logging.ERROR, "fg": Palette.COLORS.BRIGHT_RED},
            {"level": logging.CRITICAL, "fg": Palette.DEEP_PURPLE.DEEP_PURPLE_5, "bold": True, "underline": True},
        ]

        for kwargs in _default_kwargs:
            self.set_style(**kwargs)

        if override_kwargs:
            for kwargs in override_kwargs:
                self.set_style(**kwargs)

    def get_style(self, level: int) -> functools.partial:
        return self.colors_map.get(level, None)

    def set_style(
        self,
        level: int,
        fg=None,
        bg=None,
        bold: bool = None,
        dim: bool = None,
        underline: bool = None,
        overline: bool = None,
        italic: bool = None,
        blink: bool = None,
        reverse: bool = None,
        strikethrough: bool = None,
        reset: bool = True,
    ):
        self.colors_map[level] = functools.partial(
            click.style,
            fg=fg,
            bg=bg,
            bold=bold,
            dim=dim,
            underline=underline,
            overline=overline,
            italic=italic,
            blink=blink,
            reverse=reverse,
            strikethrough=strikethrough,
            reset=reset,
        )


class DebugFormatter(logging.Formatter):
    def __init__(
        self,
        fmt: str = "{levelname} {message} ({asctime})",
        datefmt: str = "%Y-%m-%dT%H:%M:%S%z",
        style: str = "{",
        validate: bool = True,
        accent_color: str = "bright_cyan",
        styler: typing.ClassVar[Styler] = Styler,
    ):
        self.accent_color = accent_color
        self.styler = styler()
        super().__init__(fmt=fmt, datefmt=datefmt, style=style, validate=validate)

    def formatMessage(self, record: logging.LogRecord) -> str:
        record_copy = copy.copy(record)
        for key in record_copy.__dict__:
            if key == "message":
                record_copy.__dict__["message"] = self.styler.get_style(level=record_copy.levelno)(
                    text=record_copy.message
                )
            elif key == "levelname":
                separator = " " * (8 - len(record_copy.levelname))
                record_copy.__dict__["levelname"] = (
                    self.styler.get_style(level=record_copy.levelno)(text=record_copy.levelname)
                    + click.style(text=":", fg=self.accent_color)
                    + separator
                )
            elif key == "levelno":
                continue  # set it after iterations (because using in other cases)
            else:
                record_copy.__dict__[key] = click.style(text=str(record.__dict__[key]), fg=self.accent_color)

        record_copy.__dict__["levelno"] = click.style(text=str(record.__dict__["levelno"]), fg=self.accent_color)

        return super().formatMessage(record=record_copy)


class PyCharmDebugLogger(logging.getLoggerClass()):
    def trace(self, msg, *args, **kwargs):
        if self.isEnabledFor(level=TRACE):
            self._log(level=TRACE, msg=msg, args=args, **kwargs)

    def success(self, msg, *args, **kwargs):
        if self.isEnabledFor(level=SUCCESS):
            self._log(level=SUCCESS, msg=msg, args=args, **kwargs)


@functools.lru_cache()
def setup_logging(
    name: str = "Debug Logger",
    raw_format: str = "{levelname} {message} {asctime}",
    file_link_formatter: bool = True,
    color_formatter: bool = True,
    date_format: str = "%Y-%m-%dT%H:%M:%S%z",
    accent_color: Union[tuple[int, int, int], str] = Palette.COLORS.CYAN,
    styler: typing.ClassVar[Styler] = Styler,
):
    """Setup logging formatter"""
    if file_link_formatter and color_formatter:
        # make PyCharm available link to file where's log occurs
        # example of link creation: "File {pathname}, line {lineno}"
        file_format = click.style(text='╰───📑File "', fg="bright_white", bold=True)
        line_format = click.style(text='", line ', fg="bright_white", bold=True)
        debug_format = raw_format + f"\n{file_format}{{pathname}}{line_format}{{lineno}}"
        formatter = DebugFormatter(fmt=debug_format, datefmt=date_format, accent_color=accent_color, styler=styler)
    elif not file_link_formatter and color_formatter:
        # use colored formatter
        formatter = DebugFormatter(fmt=raw_format, datefmt=date_format, accent_color=accent_color, styler=styler)
    else:
        # use default Formatter
        formatter = logging.Formatter(fmt=raw_format, datefmt=date_format, style="{")

    logging.addLevelName(level=TRACE, levelName="TRACE")
    logging.addLevelName(level=SUCCESS, levelName="SUCCESS")
    handler = logging.StreamHandler()
    handler.setFormatter(fmt=formatter)
    handler.setLevel(level=TRACE)

    main_logger = PyCharmDebugLogger(name=name)
    main_logger.setLevel(level=TRACE)
    main_logger.addHandler(hdlr=handler)

    return main_logger


logger = setup_logging()
simple_logger = setup_logging(file_link_formatter=False)
raw_logger = setup_logging(file_link_formatter=False, color_formatter=False)
