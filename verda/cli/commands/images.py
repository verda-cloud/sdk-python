"""Commands for listing available images."""

import typer

from verda.cli import main as cli_main
from verda.cli.utils.client import get_client
from verda.cli.utils.errors import handle_api_errors
from verda.cli.utils.output import output_json, output_table

app = typer.Typer(no_args_is_help=True)


@app.command('list')
@handle_api_errors
def list_images() -> None:
    """List available OS images."""
    client = get_client()
    images = client.images.get()

    if cli_main.state['json_output']:
        output_json(images)
    else:
        columns = [
            ('Image Type', 'image_type', None),
            ('Name', 'name', None),
            (
                'Details',
                'details',
                lambda x: ', '.join(x[:2]) + ('...' if len(x) > 2 else '') if x else '',
            ),
        ]
        output_table(images, columns, title='Available Images')
