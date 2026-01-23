"""Commands for managing startup scripts."""

from pathlib import Path
from typing import Annotated

import typer

from verda.cli import main as cli_main
from verda.cli.utils.client import get_client
from verda.cli.utils.errors import handle_api_errors
from verda.cli.utils.output import output_json, output_single, output_table, success

app = typer.Typer(no_args_is_help=True)

SCRIPT_COLUMNS = [
    ('ID', 'id', None),
    ('Name', 'name', None),
    ('Script', 'script', lambda x: x[:40] + '...' if len(x) > 40 else x),
]


@app.command('list')
@handle_api_errors
def list_scripts() -> None:
    """List all startup scripts."""
    client = get_client()
    scripts = client.startup_scripts.get()

    if cli_main.state['json_output']:
        output_json(scripts)
    else:
        output_table(scripts, SCRIPT_COLUMNS, title='Startup Scripts')


@app.command('get')
@handle_api_errors
def get_script(
    script_id: Annotated[str, typer.Argument(help='Script ID')],
) -> None:
    """Get startup script details by ID."""
    client = get_client()
    script = client.startup_scripts.get_by_id(script_id)

    if cli_main.state['json_output']:
        output_json(script)
    else:
        fields = [
            ('ID', 'id', None),
            ('Name', 'name', None),
            ('Script', 'script', None),
        ]
        output_single(script, fields, title=f'Startup Script: {script.name}')


@app.command('create')
@handle_api_errors
def create_script(
    name: Annotated[
        str,
        typer.Option('--name', '-n', help='Script name'),
    ],
    script: Annotated[
        str | None,
        typer.Option('--script', '-s', help='Script content'),
    ] = None,
    script_file: Annotated[
        Path | None,
        typer.Option('--file', '-f', help='Path to script file'),
    ] = None,
) -> None:
    """Create a new startup script."""
    if not script and not script_file:
        typer.echo('Error: Either --script or --file must be provided', err=True)
        raise typer.Exit(code=1)

    if script_file:
        script = script_file.read_text()

    client = get_client()
    result = client.startup_scripts.create(name, script)

    if cli_main.state['json_output']:
        output_json(result)
    else:
        success(f"Startup script '{result.name}' created with ID: {result.id}")


@app.command('delete')
@handle_api_errors
def delete_script(
    script_ids: Annotated[list[str], typer.Argument(help='Script ID(s) to delete')],
    force: Annotated[
        bool,
        typer.Option('--force', '-f', help='Skip confirmation'),
    ] = False,
) -> None:
    """Delete startup script(s)."""
    if not force:
        confirm = typer.confirm(f'Delete {len(script_ids)} script(s)?')
        if not confirm:
            raise typer.Abort()

    client = get_client()
    if len(script_ids) == 1:
        client.startup_scripts.delete_by_id(script_ids[0])
    else:
        client.startup_scripts.delete(script_ids)
    success('Script(s) deleted')
