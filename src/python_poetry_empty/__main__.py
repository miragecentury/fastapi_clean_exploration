"""
Entry point for the module.
"""

import logging

import structlog

from .application import Application
from .setup.log import LogModeEnum, setup_log

_logger: logging.Logger = structlog.get_logger(__package__)


def main() -> None:
    """
    Main entry point for the module.
    """
    setup_log(mode=LogModeEnum.CONSOLE)
    app = Application()
    app.run()


if __name__ == "__main__":
    main()
