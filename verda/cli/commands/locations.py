"""Commands for listing datacenter locations."""

import typer

from verda.cli import main as cli_main
from verda.cli.utils.client import get_client
from verda.cli.utils.errors import handle_api_errors
from verda.cli.utils.output import output_json, output_table, spinner

app = typer.Typer(no_args_is_help=True)


@app.command('list')
@handle_api_errors
def list_locations() -> None:
    """List available datacenter locations."""
    client = get_client()
    with spinner('Fetching locations...'):
        locations = client.locations.get()

    if cli_main.state['json_output']:
        output_json(locations)
    else:
        columns = [
            ('Code', 'code', None),
            ('Name', 'name', None),
            ('Country', 'country', None),
        ]
        output_table(locations, columns, title='Datacenter Locations')
