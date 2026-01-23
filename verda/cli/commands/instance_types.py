"""Commands for listing available instance types."""

import typer

from verda.cli import main as cli_main
from verda.cli.utils.client import get_client
from verda.cli.utils.errors import handle_api_errors
from verda.cli.utils.output import output_json, output_table

app = typer.Typer(no_args_is_help=True)


def format_gpu(gpu: dict) -> str:
    """Format GPU details."""
    if not gpu:
        return '-'
    return gpu.get('description', '-')


def format_memory(memory: dict) -> str:
    """Format memory details."""
    if not memory:
        return '-'
    return memory.get('description', '-')


@app.command('list')
@handle_api_errors
def list_instance_types() -> None:
    """List available instance types with pricing."""
    client = get_client()
    types = client.instance_types.get()

    if cli_main.state['json_output']:
        output_json(types)
    else:
        columns = [
            ('Type', 'instance_type', None),
            ('Description', 'description', None),
            ('Price/hr', 'price_per_hour', lambda x: f'${x:.4f}'),
            ('Spot Price/hr', 'spot_price_per_hour', lambda x: f'${x:.4f}'),
            ('GPU', 'gpu', format_gpu),
            ('Memory', 'memory', format_memory),
        ]
        output_table(types, columns, title='Instance Types')
