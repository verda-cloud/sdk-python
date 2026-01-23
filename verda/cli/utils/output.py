"""Output formatting utilities for table and JSON output."""

import json
from collections.abc import Callable, Generator
from contextlib import contextmanager
from dataclasses import asdict, is_dataclass
from typing import Any

from rich.console import Console
from rich.table import Table

console = Console()


@contextmanager
def spinner(message: str = 'Loading...') -> Generator[None, None, None]:
    """Context manager that shows a loading spinner.

    Args:
        message: Message to display while loading

    Yields:
        None
    """
    with console.status(f'[cyan]{message}[/cyan]', spinner='dots'):
        yield


def to_dict(obj: Any) -> dict | list | Any:
    """Convert an object to a dictionary for JSON serialization.

    Args:
        obj: Object to convert

    Returns:
        Dictionary representation of the object
    """
    if obj is None:
        return None
    if isinstance(obj, list):
        return [to_dict(item) for item in obj]
    if isinstance(obj, dict):
        return obj
    if is_dataclass(obj) and hasattr(obj, 'to_dict'):
        return obj.to_dict()
    if is_dataclass(obj):
        return asdict(obj)
    if hasattr(obj, '__dict__'):
        return {k: v for k, v in obj.__dict__.items() if not k.startswith('_')}
    return obj


def output_json(data: Any) -> None:
    """Output data as formatted JSON.

    Args:
        data: Data to output (will be converted to dict if needed)
    """
    json_data = to_dict(data)
    console.print_json(json.dumps(json_data, indent=2, default=str))


def output_table(
    data: list[Any],
    columns: list[tuple[str, str, Callable[[Any], str] | None]],
    title: str | None = None,
) -> None:
    """Output data as a rich table.

    Args:
        data: List of objects to display
        columns: List of (header, attr_name, formatter) tuples
        title: Optional table title
    """
    table = Table(title=title, show_header=True, header_style='bold cyan')

    for header, _, _ in columns:
        table.add_column(header)

    for item in data:
        row = []
        for _, attr, formatter in columns:
            if hasattr(item, attr):
                value = getattr(item, attr)
            elif isinstance(item, dict):
                value = item.get(attr)
            else:
                value = None

            if formatter and value is not None:
                value = formatter(value)
            row.append(str(value) if value is not None else '-')
        table.add_row(*row)

    console.print(table)


def output_single(
    data: Any,
    fields: list[tuple[str, str, Callable[[Any], str] | None]],
    title: str | None = None,
) -> None:
    """Output a single object's details as a key-value table.

    Args:
        data: Object to display
        fields: List of (label, attr_name, formatter) tuples
        title: Optional table title
    """
    table = Table(title=title, show_header=False, box=None)
    table.add_column('Field', style='bold')
    table.add_column('Value')

    for label, attr, formatter in fields:
        if hasattr(data, attr):
            value = getattr(data, attr)
        elif isinstance(data, dict):
            value = data.get(attr)
        else:
            value = None

        if formatter and value is not None:
            value = formatter(value)
        table.add_row(label, str(value) if value is not None else '-')

    console.print(table)


def success(message: str) -> None:
    """Print a success message.

    Args:
        message: Message to display
    """
    console.print(f'[green]Success:[/green] {message}')


def error(message: str) -> None:
    """Print an error message.

    Args:
        message: Message to display
    """
    console.print(f'[red]Error:[/red] {message}', style='red')


def warning(message: str) -> None:
    """Print a warning message.

    Args:
        message: Message to display
    """
    console.print(f'[yellow]Warning:[/yellow] {message}')
