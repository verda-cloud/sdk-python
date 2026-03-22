"""Main Typer application and entry point for verda-cli."""

from typing import Annotated

import typer

from verda._version import __version__
from verda.cli.commands import (
    balance,
    clusters,
    images,
    instance_types,
    instances,
    locations,
    ssh_keys,
    startup_scripts,
    volume_types,
    volumes,
)

app = typer.Typer(
    name='verda-cli',
    help='Verda Cloud CLI - Manage cloud instances, volumes, and clusters',
    no_args_is_help=True,
)

# Global state for JSON output mode
state = {'json_output': False}


def version_callback(value: bool) -> None:
    """Show version and exit."""
    if value:
        typer.echo(f'verda-cli version {__version__}')
        raise typer.Exit()


@app.callback()
def main(
    json_output: Annotated[
        bool,
        typer.Option('--json', '-j', help='Output in JSON format'),
    ] = False,
    _version: Annotated[
        bool,
        typer.Option(
            '--version',
            '-v',
            help='Show version and exit',
            callback=version_callback,
            is_eager=True,
        ),
    ] = False,
) -> None:
    """Verda Cloud CLI for managing cloud resources.

    Set VERDA_CLIENT_ID and VERDA_CLIENT_SECRET environment variables to authenticate.
    """
    state['json_output'] = json_output


# Register sub-applications
app.add_typer(instances.app, name='instances', help='Manage compute instances')
app.add_typer(volumes.app, name='volumes', help='Manage storage volumes')
app.add_typer(clusters.app, name='clusters', help='Manage compute clusters')
app.add_typer(ssh_keys.app, name='ssh-keys', help='Manage SSH keys')
app.add_typer(startup_scripts.app, name='startup-scripts', help='Manage startup scripts')
app.add_typer(images.app, name='images', help='List available OS images')
app.add_typer(instance_types.app, name='instance-types', help='List available instance types')
app.add_typer(volume_types.app, name='volume-types', help='List available volume types')
app.add_typer(locations.app, name='locations', help='List datacenter locations')
app.add_typer(balance.app, name='balance', help='Check account balance')


if __name__ == '__main__':
    app()
