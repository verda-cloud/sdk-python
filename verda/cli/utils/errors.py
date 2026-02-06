"""Error handling utilities for CLI commands."""

import functools
from typing import TypeVar

import typer

from verda.cli.utils.output import error
from verda.exceptions import APIException

F = TypeVar('F')


def handle_api_errors(func: F) -> F:
    """Decorator to handle API errors gracefully.

    Catches common exceptions and displays user-friendly error messages.

    Args:
        func: Function to wrap

    Returns:
        Wrapped function with error handling
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except APIException as e:
            error(f'API Error [{e.code}]: {e.message}')
            raise typer.Exit(code=1) from None
        except TimeoutError as e:
            error(f'Timeout: {e}')
            raise typer.Exit(code=1) from None
        except ConnectionError as e:
            error(f'Connection error: {e}')
            raise typer.Exit(code=1) from None

    return wrapper  # type: ignore[return-value]
