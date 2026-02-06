"""Commands for managing SSH keys."""

from pathlib import Path
from typing import Annotated

import typer

from verda.cli import main as cli_main
from verda.cli.utils.client import get_client
from verda.cli.utils.errors import handle_api_errors
from verda.cli.utils.output import output_json, output_single, output_table, spinner, success

app = typer.Typer(no_args_is_help=True)

SSH_KEY_COLUMNS = [
    ('ID', 'id', None),
    ('Name', 'name', None),
    ('Public Key', 'public_key', lambda x: x[:50] + '...' if len(x) > 50 else x),
]


@app.command('list')
@handle_api_errors
def list_ssh_keys() -> None:
    """List all SSH keys."""
    client = get_client()
    with spinner('Fetching SSH keys...'):
        keys = client.ssh_keys.get()

    if cli_main.state['json_output']:
        output_json(keys)
    else:
        output_table(keys, SSH_KEY_COLUMNS, title='SSH Keys')


@app.command('get')
@handle_api_errors
def get_ssh_key(
    key_id: Annotated[str, typer.Argument(help='SSH key ID')],
) -> None:
    """Get SSH key details by ID."""
    client = get_client()
    with spinner('Fetching SSH key...'):
        key = client.ssh_keys.get_by_id(key_id)

    if cli_main.state['json_output']:
        output_json(key)
    else:
        fields = [
            ('ID', 'id', None),
            ('Name', 'name', None),
            ('Public Key', 'public_key', None),
        ]
        output_single(key, fields, title=f'SSH Key: {key.name}')


@app.command('create')
@handle_api_errors
def create_ssh_key(
    name: Annotated[
        str,
        typer.Option('--name', '-n', help='Key name'),
    ],
    key: Annotated[
        str | None,
        typer.Option('--key', '-k', help='Public key string'),
    ] = None,
    key_file: Annotated[
        Path | None,
        typer.Option('--file', '-f', help='Path to public key file'),
    ] = None,
) -> None:
    """Create a new SSH key."""
    if not key and not key_file:
        typer.echo('Error: Either --key or --file must be provided', err=True)
        raise typer.Exit(code=1)

    if key_file:
        key = key_file.read_text().strip()

    client = get_client()
    with spinner('Creating SSH key...'):
        ssh_key = client.ssh_keys.create(name, key)

    if cli_main.state['json_output']:
        output_json(ssh_key)
    else:
        success(f"SSH key '{ssh_key.name}' created with ID: {ssh_key.id}")


@app.command('delete')
@handle_api_errors
def delete_ssh_key(
    key_ids: Annotated[list[str], typer.Argument(help='SSH key ID(s) to delete')],
    force: Annotated[
        bool,
        typer.Option('--force', '-f', help='Skip confirmation'),
    ] = False,
) -> None:
    """Delete SSH key(s)."""
    if not force:
        confirm = typer.confirm(f'Are you sure you want to delete {len(key_ids)} SSH key(s)?')
        if not confirm:
            raise typer.Abort()

    client = get_client()
    with spinner('Deleting SSH key(s)...'):
        if len(key_ids) == 1:
            client.ssh_keys.delete_by_id(key_ids[0])
        else:
            client.ssh_keys.delete(key_ids)
    success('SSH key(s) deleted')
