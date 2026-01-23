"""Commands for managing compute instances."""

from typing import Annotated

import typer

from verda.cli import main as cli_main
from verda.cli.utils.client import get_client
from verda.cli.utils.errors import handle_api_errors
from verda.cli.utils.output import output_json, output_single, output_table, success
from verda.constants import Actions, Locations

app = typer.Typer(no_args_is_help=True)


def status_color(status: str) -> str:
    """Format status with color."""
    colors = {
        'running': '[green]running[/green]',
        'offline': '[red]offline[/red]',
        'provisioning': '[yellow]provisioning[/yellow]',
        'ordered': '[yellow]ordered[/yellow]',
        'hibernating': '[blue]hibernating[/blue]',
        'starting_hibernation': '[blue]starting_hibernation[/blue]',
        'restoring': '[yellow]restoring[/yellow]',
        'error': '[red]error[/red]',
    }
    return colors.get(status, status)


INSTANCE_COLUMNS = [
    ('ID', 'id', None),
    ('Type', 'instance_type', None),
    ('Hostname', 'hostname', None),
    ('Status', 'status', status_color),
    ('IP', 'ip', None),
    ('Location', 'location', None),
    ('Price/hr', 'price_per_hour', lambda x: f'${x:.4f}'),
]


@app.command('list')
@handle_api_errors
def list_instances(
    status: Annotated[
        str | None,
        typer.Option('--status', '-s', help='Filter by status'),
    ] = None,
) -> None:
    """List all instances."""
    client = get_client()
    instances = client.instances.get(status=status)

    if cli_main.state['json_output']:
        output_json(instances)
    else:
        output_table(instances, INSTANCE_COLUMNS, title='Instances')


@app.command('get')
@handle_api_errors
def get_instance(
    instance_id: Annotated[str, typer.Argument(help='Instance ID')],
) -> None:
    """Get instance details by ID."""
    client = get_client()
    instance = client.instances.get_by_id(instance_id)

    if cli_main.state['json_output']:
        output_json(instance)
    else:
        fields = [
            ('ID', 'id', None),
            ('Type', 'instance_type', None),
            ('Hostname', 'hostname', None),
            ('Description', 'description', None),
            ('Status', 'status', status_color),
            ('IP', 'ip', None),
            ('Location', 'location', None),
            ('Image', 'image', None),
            ('Price/hr', 'price_per_hour', lambda x: f'${x:.4f}'),
            ('Created', 'created_at', None),
            ('Spot', 'is_spot', None),
            ('Contract', 'contract', None),
            ('OS Volume ID', 'os_volume_id', None),
        ]
        output_single(instance, fields, title=f'Instance: {instance.hostname}')


@app.command('create')
@handle_api_errors
def create_instance(
    instance_type: Annotated[
        str,
        typer.Option('--type', '-t', help='Instance type (e.g., 1V100.6V)'),
    ],
    image: Annotated[
        str,
        typer.Option('--image', '-i', help='Image name (e.g., ubuntu-24.04-cuda-12.8)'),
    ],
    hostname: Annotated[
        str,
        typer.Option('--hostname', '-n', help='Instance hostname'),
    ],
    description: Annotated[
        str,
        typer.Option('--description', '-d', help='Instance description'),
    ] = '',
    ssh_key_ids: Annotated[
        list[str] | None,
        typer.Option('--ssh-key', '-k', help='SSH key IDs (can specify multiple)'),
    ] = None,
    location: Annotated[
        str,
        typer.Option('--location', '-l', help='Datacenter location'),
    ] = Locations.FIN_03,
    startup_script_id: Annotated[
        str | None,
        typer.Option('--startup-script', help='Startup script ID'),
    ] = None,
    existing_volumes: Annotated[
        list[str] | None,
        typer.Option('--volume', '-v', help='Existing volume IDs to attach'),
    ] = None,
    spot: Annotated[
        bool,
        typer.Option('--spot', help='Create as spot instance'),
    ] = False,
    contract: Annotated[
        str | None,
        typer.Option('--contract', help='Contract type: LONG_TERM, PAY_AS_YOU_GO, SPOT'),
    ] = None,
    no_wait: Annotated[
        bool,
        typer.Option('--no-wait', help="Don't wait for instance to provision"),
    ] = False,
) -> None:
    """Create a new instance."""
    client = get_client()

    max_wait_time = 0 if no_wait else 180

    instance = client.instances.create(
        instance_type=instance_type,
        image=image,
        hostname=hostname,
        description=description,
        ssh_key_ids=ssh_key_ids or [],
        location=location,
        startup_script_id=startup_script_id,
        existing_volumes=existing_volumes,
        is_spot=spot,
        contract=contract,
        max_wait_time=max_wait_time,
    )

    if cli_main.state['json_output']:
        output_json(instance)
    else:
        success(f"Instance '{instance.hostname}' created with ID: {instance.id}")
        output_single(
            instance,
            [
                ('ID', 'id', None),
                ('Status', 'status', status_color),
                ('IP', 'ip', None),
            ],
        )


@app.command('start')
@handle_api_errors
def start_instance(
    instance_id: Annotated[str, typer.Argument(help='Instance ID')],
) -> None:
    """Start an instance."""
    client = get_client()
    client.instances.action(instance_id, Actions.START)
    success(f'Instance {instance_id} start initiated')


@app.command('stop')
@handle_api_errors
def stop_instance(
    instance_id: Annotated[str, typer.Argument(help='Instance ID')],
) -> None:
    """Stop (shutdown) an instance."""
    client = get_client()
    client.instances.action(instance_id, Actions.SHUTDOWN)
    success(f'Instance {instance_id} shutdown initiated')


@app.command('delete')
@handle_api_errors
def delete_instance(
    instance_id: Annotated[str, typer.Argument(help='Instance ID')],
    force: Annotated[
        bool,
        typer.Option('--force', '-f', help='Skip confirmation'),
    ] = False,
) -> None:
    """Delete an instance."""
    if not force:
        confirm = typer.confirm(f'Are you sure you want to delete instance {instance_id}?')
        if not confirm:
            raise typer.Abort()

    client = get_client()
    client.instances.action(instance_id, Actions.DELETE)
    success(f'Instance {instance_id} deletion initiated')


@app.command('hibernate')
@handle_api_errors
def hibernate_instance(
    instance_id: Annotated[str, typer.Argument(help='Instance ID')],
) -> None:
    """Hibernate an instance."""
    client = get_client()
    client.instances.action(instance_id, Actions.HIBERNATE)
    success(f'Instance {instance_id} hibernation initiated')


@app.command('restore')
@handle_api_errors
def restore_instance(
    instance_id: Annotated[str, typer.Argument(help='Instance ID')],
) -> None:
    """Restore a hibernated instance."""
    client = get_client()
    client.instances.action(instance_id, Actions.RESTORE)
    success(f'Instance {instance_id} restore initiated')


@app.command('availability')
@handle_api_errors
def check_availability(
    instance_type: Annotated[
        str | None,
        typer.Argument(help='Instance type to check (omit to list all)'),
    ] = None,
    location: Annotated[
        str | None,
        typer.Option('--location', '-l', help='Location code'),
    ] = None,
    spot: Annotated[
        bool,
        typer.Option('--spot', help='Check spot availability'),
    ] = False,
) -> None:
    """Check instance type availability."""
    client = get_client()

    if instance_type:
        available = client.instances.is_available(
            instance_type, is_spot=spot, location_code=location
        )
        if cli_main.state['json_output']:
            output_json({'instance_type': instance_type, 'available': available})
        else:
            status = '[green]Available[/green]' if available else '[red]Not Available[/red]'
            typer.echo(f'{instance_type}: {status}')
    else:
        availabilities = client.instances.get_availabilities(is_spot=spot, location_code=location)
        if cli_main.state['json_output']:
            output_json(availabilities)
        else:
            # Flatten the data: API returns [{location_code, availabilities: [types]}]
            flattened = []
            for loc_data in availabilities:
                loc_code = loc_data.get('location_code', '-')
                for inst_type in loc_data.get('availabilities', []):
                    flattened.append({'location': loc_code, 'instance_type': inst_type})

            columns = [
                ('Location', 'location', None),
                ('Instance Type', 'instance_type', None),
            ]
            output_table(flattened, columns, title='Available Instance Types')
