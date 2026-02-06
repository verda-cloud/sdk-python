"""Commands for checking account balance."""

import typer

from verda.cli import main as cli_main
from verda.cli.utils.client import get_client
from verda.cli.utils.errors import handle_api_errors
from verda.cli.utils.output import console, output_json, spinner

app = typer.Typer(no_args_is_help=True)


@app.command('get')
@handle_api_errors
def get_balance() -> None:
    """Get account balance."""
    client = get_client()
    with spinner('Fetching balance...'):
        balance = client.balance.get()

    if cli_main.state['json_output']:
        output_json({'amount': balance.amount, 'currency': balance.currency})
    else:
        console.print(f'Balance: [bold green]{balance.currency} {balance.amount:.2f}[/bold green]')
