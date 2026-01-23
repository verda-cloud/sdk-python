"""Commands for managing storage volumes."""

from typing import Annotated

import typer

from verda.cli import main as cli_main
from verda.cli.utils.client import get_client
from verda.cli.utils.errors import handle_api_errors
from verda.cli.utils.output import output_json, output_single, output_table, spinner, success
from verda.constants import Locations, VolumeTypes

app = typer.Typer(no_args_is_help=True)


def status_color(status: str) -> str:
    """Format status with color."""
    colors = {
        'attached': '[green]attached[/green]',
        'detached': '[yellow]detached[/yellow]',
        'creating': '[blue]creating[/blue]',
        'ordered': '[yellow]ordered[/yellow]',
        'cloning': '[blue]cloning[/blue]',
        'deleting': '[red]deleting[/red]',
        'deleted': '[red]deleted[/red]',
    }
    return colors.get(status, status)


VOLUME_COLUMNS = [
    ('ID', 'id', None),
    ('Name', 'name', None),
    ('Size (GB)', 'size', None),
    ('Type', 'type', None),
    ('Status', 'status', status_color),
    ('Location', 'location', None),
    ('Instance ID', 'instance_id', lambda x: x or '-'),
]


@app.command('list')
@handle_api_errors
def list_volumes(
    status: Annotated[
        str | None,
        typer.Option('--status', '-s', help='Filter by status'),
    ] = None,
) -> None:
    """List all volumes."""
    client = get_client()
    with spinner('Fetching volumes...'):
        volumes = client.volumes.get(status=status)

    if cli_main.state['json_output']:
        output_json(volumes)
    else:
        output_table(volumes, VOLUME_COLUMNS, title='Volumes')


@app.command('get')
@handle_api_errors
def get_volume(
    volume_id: Annotated[str, typer.Argument(help='Volume ID')],
) -> None:
    """Get volume details by ID."""
    client = get_client()
    with spinner('Fetching volume...'):
        volume = client.volumes.get_by_id(volume_id)

    if cli_main.state['json_output']:
        output_json(volume)
    else:
        fields = [
            ('ID', 'id', None),
            ('Name', 'name', None),
            ('Size (GB)', 'size', None),
            ('Type', 'type', None),
            ('Status', 'status', status_color),
            ('Location', 'location', None),
            ('Instance ID', 'instance_id', lambda x: x or 'Not attached'),
            ('OS Volume', 'is_os_volume', None),
            ('Created', 'created_at', None),
        ]
        output_single(volume, fields, title=f'Volume: {volume.name}')


@app.command('create')
@handle_api_errors
def create_volume(
    name: Annotated[
        str,
        typer.Option('--name', '-n', help='Volume name'),
    ],
    size: Annotated[
        int,
        typer.Option('--size', '-s', help='Size in GB'),
    ],
    volume_type: Annotated[
        str,
        typer.Option('--type', '-t', help='Volume type: NVMe, HDD, NVMe_Shared'),
    ] = VolumeTypes.NVMe,
    location: Annotated[
        str,
        typer.Option('--location', '-l', help='Datacenter location'),
    ] = Locations.FIN_03,
    instance_id: Annotated[
        str | None,
        typer.Option('--instance', '-i', help='Attach to instance'),
    ] = None,
) -> None:
    """Create a new volume."""
    client = get_client()
    with spinner('Creating volume...'):
        volume = client.volumes.create(
            type=volume_type,
            name=name,
            size=size,
            instance_id=instance_id,
            location=location,
        )

    if cli_main.state['json_output']:
        output_json(volume)
    else:
        success(f"Volume '{volume.name}' created with ID: {volume.id}")


@app.command('attach')
@handle_api_errors
def attach_volume(
    volume_ids: Annotated[list[str], typer.Argument(help='Volume ID(s) to attach')],
    instance_id: Annotated[
        str,
        typer.Option('--instance', '-i', help='Instance ID to attach to'),
    ],
) -> None:
    """Attach volume(s) to an instance."""
    client = get_client()
    with spinner('Attaching volume(s)...'):
        client.volumes.attach(volume_ids, instance_id)
    success(f'Volume(s) attached to instance {instance_id}')


@app.command('detach')
@handle_api_errors
def detach_volume(
    volume_ids: Annotated[list[str], typer.Argument(help='Volume ID(s) to detach')],
) -> None:
    """Detach volume(s) from instance(s)."""
    client = get_client()
    with spinner('Detaching volume(s)...'):
        client.volumes.detach(volume_ids)
    success('Volume(s) detached')


@app.command('delete')
@handle_api_errors
def delete_volume(
    volume_ids: Annotated[list[str], typer.Argument(help='Volume ID(s) to delete')],
    permanent: Annotated[
        bool,
        typer.Option('--permanent', '-p', help='Permanently delete (skip trash)'),
    ] = False,
    force: Annotated[
        bool,
        typer.Option('--force', '-f', help='Skip confirmation'),
    ] = False,
) -> None:
    """Delete volume(s)."""
    if not force:
        confirm = typer.confirm(f'Are you sure you want to delete {len(volume_ids)} volume(s)?')
        if not confirm:
            raise typer.Abort()

    client = get_client()
    with spinner('Deleting volume(s)...'):
        client.volumes.delete(volume_ids, is_permanent=permanent)
    success('Volume(s) deleted')


@app.command('rename')
@handle_api_errors
def rename_volume(
    volume_ids: Annotated[list[str], typer.Argument(help='Volume ID(s) to rename')],
    name: Annotated[
        str,
        typer.Option('--name', '-n', help='New name'),
    ],
) -> None:
    """Rename volume(s)."""
    client = get_client()
    with spinner('Renaming volume(s)...'):
        client.volumes.rename(volume_ids, name)
    success(f"Volume(s) renamed to '{name}'")


@app.command('resize')
@handle_api_errors
def resize_volume(
    volume_ids: Annotated[list[str], typer.Argument(help='Volume ID(s) to resize')],
    size: Annotated[
        int,
        typer.Option('--size', '-s', help='New size in GB'),
    ],
) -> None:
    """Increase volume size (can only increase, not decrease)."""
    client = get_client()
    with spinner('Resizing volume(s)...'):
        client.volumes.increase_size(volume_ids, size)
    success(f'Volume(s) resized to {size}GB')


@app.command('clone')
@handle_api_errors
def clone_volume(
    volume_id: Annotated[str, typer.Argument(help='Volume ID to clone')],
    name: Annotated[
        str | None,
        typer.Option('--name', '-n', help='Name for cloned volume'),
    ] = None,
    volume_type: Annotated[
        str | None,
        typer.Option('--type', '-t', help='Type for cloned volume'),
    ] = None,
) -> None:
    """Clone a volume."""
    client = get_client()
    with spinner('Cloning volume...'):
        volume = client.volumes.clone(volume_id, name=name, type=volume_type)

    if cli_main.state['json_output']:
        output_json(volume)
    else:
        success(f'Volume cloned with ID: {volume.id}')


@app.command('trash')
@handle_api_errors
def list_trash() -> None:
    """List volumes in trash."""
    client = get_client()
    with spinner('Fetching trash...'):
        volumes = client.volumes.get_in_trash()

    if cli_main.state['json_output']:
        output_json(volumes)
    else:
        output_table(volumes, VOLUME_COLUMNS, title='Volumes in Trash')
