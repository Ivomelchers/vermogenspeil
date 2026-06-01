"""yfinance stderr/print onderdrukken — geen console-spam in runserver."""

from __future__ import annotations

import contextlib
import io
import logging
import warnings
from collections.abc import Iterator

_YFINANCE_LOGGER_NAMES = ("yfinance", "yfinance.base", "yfinance.scrapers", "yfinance.scrapers.quote")


def configure_yfinance_logging() -> None:
    for name in _YFINANCE_LOGGER_NAMES:
        logging.getLogger(name).setLevel(logging.CRITICAL)


@contextlib.contextmanager
def suppress_yfinance_noise() -> Iterator[None]:
    """Onderdruk yfinance-waarschuwingen ('possibly delisted', lege history)."""
    configure_yfinance_logging()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        stderr_buffer = io.StringIO()
        with contextlib.redirect_stderr(stderr_buffer):
            yield
