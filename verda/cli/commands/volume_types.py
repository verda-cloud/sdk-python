"""Commands for listing available volume types."""

import typer

from verda.cli import main as cli_main
from verda.cli.utils.client import get_client
from verda.cli.utils.errors import handle_api_errors
from verda.cli.utils.output import output_json, output_table, spinner

app = typer.Typer(no_args_is_help=True)


@app.command('list')
@handle_api_errors
def list_volume_types() -> None:
    """List available volume types with pricing."""
    client = get_client()
    with spinner('Fetching volume types...'):
        types = client.volume_types.get()

    if cli_main.state['json_output']:
        output_json(types)
    else:
        columns = [
            ('Type', 'type', None),
            ('Price/GB/Month', 'price_per_month_per_gb', lambda x: f'${x:.4f}'),
        ]
        output_table(types, columns, title='Volume Types')
