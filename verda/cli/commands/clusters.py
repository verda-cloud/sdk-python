"""Commands for managing compute clusters."""

from typing import Annotated

import typer

from verda.cli import main as cli_main
from verda.cli.utils.client import get_client
from verda.cli.utils.errors import handle_api_errors
from verda.cli.utils.output import (
    console,
    output_json,
    output_single,
    output_table,
    spinner,
    success,
)
from verda.constants import ClusterStatus, Locations

app = typer.Typer(no_args_is_help=True)


def status_color(status: str) -> str:
    """Format status with color."""
    colors = {
        'running': '[green]running[/green]',
        'provisioning': '[yellow]provisioning[/yellow]',
        'ordered': '[yellow]ordered[/yellow]',
        'discontinued': '[red]discontinued[/red]',
        'error': '[red]error[/red]',
    }
    return colors.get(status, status)


CLUSTER_COLUMNS = [
    ('ID', 'id', None),
    ('Hostname', 'hostname', None),
    ('Type', 'cluster_type', None),
    ('Status', 'status', status_color),
    ('Location', 'location', None),
    ('IP', 'ip', lambda x: x or '-'),
    ('Workers', 'worker_nodes', lambda x: str(len(x)) if x else '0'),
]


@app.command('list')
@handle_api_errors
def list_clusters(
    status: Annotated[
        str | None,
        typer.Option('--status', '-s', help='Filter by status'),
    ] = None,
) -> None:
    """List all clusters."""
    client = get_client()
    with spinner('Fetching clusters...'):
        clusters = client.clusters.get(status=status)

    if cli_main.state['json_output']:
        output_json(clusters)
    else:
        output_table(clusters, CLUSTER_COLUMNS, title='Clusters')


@app.command('get')
@handle_api_errors
def get_cluster(
    cluster_id: Annotated[str, typer.Argument(help='Cluster ID')],
) -> None:
    """Get cluster details by ID."""
    client = get_client()
    with spinner('Fetching cluster...'):
        cluster = client.clusters.get_by_id(cluster_id)

    if cli_main.state['json_output']:
        output_json(cluster)
    else:
        fields = [
            ('ID', 'id', None),
            ('Hostname', 'hostname', None),
            ('Description', 'description', None),
            ('Type', 'cluster_type', None),
            ('Status', 'status', status_color),
            ('Location', 'location', None),
            ('IP', 'ip', None),
            ('Image', 'image', None),
            ('Workers', 'worker_nodes', lambda x: str(len(x)) if x else '0'),
            ('Shared Volumes', 'shared_volumes', lambda x: str(len(x)) if x else '0'),
            ('Created', 'created_at', None),
        ]
        output_single(cluster, fields, title=f'Cluster: {cluster.hostname}')


@app.command('create')
@handle_api_errors
def create_cluster(
    cluster_type: Annotated[
        str,
        typer.Option('--type', '-t', help='Cluster type'),
    ],
    image: Annotated[
        str,
        typer.Option('--image', '-i', help='Image name'),
    ],
    hostname: Annotated[
        str,
        typer.Option('--hostname', '-n', help='Cluster hostname'),
    ],
    description: Annotated[
        str,
        typer.Option('--description', '-d', help='Cluster description'),
    ] = '',
    ssh_key_ids: Annotated[
        list[str] | None,
        typer.Option('--ssh-key', '-k', help='SSH key IDs'),
    ] = None,
    location: Annotated[
        str,
        typer.Option('--location', '-l', help='Datacenter location'),
    ] = Locations.FIN_03,
    startup_script_id: Annotated[
        str | None,
        typer.Option('--startup-script', help='Startup script ID'),
    ] = None,
    shared_volume_name: Annotated[
        str | None,
        typer.Option('--shared-volume-name', help='Shared volume name'),
    ] = None,
    shared_volume_size: Annotated[
        int | None,
        typer.Option('--shared-volume-size', help='Shared volume size in GB'),
    ] = None,
    no_wait: Annotated[
        bool,
        typer.Option('--no-wait', help="Don't wait for cluster to provision"),
    ] = False,
) -> None:
    """Create a new cluster."""
    client = get_client()

    wait_status = None if no_wait else ClusterStatus.PROVISIONING

    with spinner('Creating cluster...'):
        cluster = client.clusters.create(
            cluster_type=cluster_type,
            image=image,
            hostname=hostname,
            description=description,
            ssh_key_ids=ssh_key_ids or [],
            location=location,
            startup_script_id=startup_script_id,
            shared_volume_name=shared_volume_name,
            shared_volume_size=shared_volume_size,
            wait_for_status=wait_status,
        )

    if cli_main.state['json_output']:
        output_json(cluster)
    else:
        success(f"Cluster '{cluster.hostname}' created with ID: {cluster.id}")


@app.command('delete')
@handle_api_errors
def delete_cluster(
    cluster_id: Annotated[str, typer.Argument(help='Cluster ID')],
    force: Annotated[
        bool,
        typer.Option('--force', '-f', help='Skip confirmation'),
    ] = False,
) -> None:
    """Delete a cluster."""
    if not force:
        confirm = typer.confirm(f'Are you sure you want to delete cluster {cluster_id}?')
        if not confirm:
            raise typer.Abort()

    client = get_client()
    with spinner('Deleting cluster...'):
        client.clusters.delete(cluster_id)
    success(f'Cluster {cluster_id} deletion initiated')


@app.command('availability')
@handle_api_errors
def check_availability(
    cluster_type: Annotated[
        str | None,
        typer.Argument(help='Cluster type to check (omit to list all)'),
    ] = None,
    location: Annotated[
        str | None,
        typer.Option('--location', '-l', help='Location code'),
    ] = None,
) -> None:
    """Check cluster type availability."""
    client = get_client()

    if cluster_type:
        with spinner('Checking availability...'):
            available = client.clusters.is_available(cluster_type, location_code=location)
        if cli_main.state['json_output']:
            output_json({'cluster_type': cluster_type, 'available': available})
        else:
            status = '[green]Available[/green]' if available else '[red]Not Available[/red]'
            typer.echo(f'{cluster_type}: {status}')
    else:
        with spinner('Fetching availabilities...'):
            availabilities = client.clusters.get_availabilities(location_code=location)
        if cli_main.state['json_output']:
            output_json(availabilities)
        else:
            console.print('Available Cluster Types:')
            for item in availabilities:
                console.print(f'  {item}')


@app.command('images')
@handle_api_errors
def list_cluster_images(
    cluster_type: Annotated[
        str | None,
        typer.Option('--type', '-t', help='Cluster type'),
    ] = None,
) -> None:
    """List available cluster images."""
    client = get_client()
    with spinner('Fetching images...'):
        images = client.clusters.get_cluster_images(cluster_type=cluster_type)

    if cli_main.state['json_output']:
        output_json(images)
    else:
        console.print('Available Cluster Images:')
        for img in images:
            console.print(f'  {img}')
