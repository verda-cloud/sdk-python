from dataclasses import dataclass

from dataclasses_json import dataclass_json

from verda.constants import Currency

INSTANCE_TYPES_ENDPOINT = '/instance-types'


@dataclass_json
@dataclass
class InstanceType:
    """Instance type.

    Attributes:
        id: Instance type ID.
        instance_type: Instance type, e.g. '8V100.48M'.
        price_per_hour: Instance type price per hour.
        spot_price_per_hour: Instance type spot price per hour.
        description: Instance type description.
        cpu: Instance type CPU details.
        gpu: Instance type GPU details.
        memory: Instance type memory details.
        gpu_memory: Instance type GPU memory details.
        storage: Instance type storage details.
        best_for: Suggested use cases for the instance type.
        model: GPU model.
        name: Human-readable instance type name.
        p2p: Peer-to-peer interconnect bandwidth details.
        currency: Currency used for pricing.
        manufacturer: Hardware manufacturer.
        display_name: Display name shown to users.
        supported_os: Supported operating system images.
        deploy_warning: Optional deployment warning returned by the API.
        serverless_price: Optional serverless price for the same hardware profile.
        serverless_spot_price: Optional serverless spot price for the same hardware profile.
    """

    id: str
    instance_type: str
    price_per_hour: float
    spot_price_per_hour: float
    description: str
    cpu: dict
    gpu: dict
    memory: dict
    gpu_memory: dict
    storage: dict
    best_for: list[str]
    model: str
    name: str
    p2p: str
    currency: Currency
    manufacturer: str
    display_name: str
    supported_os: list[str]
    deploy_warning: str | None = None
    serverless_price: float | None = None
    serverless_spot_price: float | None = None


class InstanceTypesService:
    """A service for interacting with the instance-types endpoint."""

    def __init__(self, http_client) -> None:
        self._http_client = http_client

    def get(self, currency: Currency = 'usd') -> list[InstanceType]:
        """Get all instance types.

        :return: list of instance type objects
        :rtype: list[InstanceType]
        """
        instance_types = self._http_client.get(
            INSTANCE_TYPES_ENDPOINT,
            params={'currency': currency},
        ).json()
        instance_type_objects = [
            InstanceType(
                id=instance_type['id'],
                instance_type=instance_type['instance_type'],
                price_per_hour=float(instance_type['price_per_hour']),
                spot_price_per_hour=float(instance_type['spot_price']),
                description=instance_type['description'],
                cpu=instance_type['cpu'],
                gpu=instance_type['gpu'],
                memory=instance_type['memory'],
                gpu_memory=instance_type['gpu_memory'],
                storage=instance_type['storage'],
                best_for=instance_type['best_for'],
                model=instance_type['model'],
                name=instance_type['name'],
                p2p=instance_type['p2p'],
                currency=instance_type['currency'],
                manufacturer=instance_type['manufacturer'],
                display_name=instance_type['display_name'],
                supported_os=instance_type['supported_os'],
                deploy_warning=instance_type.get('deploy_warning'),
                serverless_price=(
                    float(instance_type['serverless_price'])
                    if instance_type.get('serverless_price') is not None
                    else None
                ),
                serverless_spot_price=(
                    float(instance_type['serverless_spot_price'])
                    if instance_type.get('serverless_spot_price') is not None
                    else None
                ),
            )
            for instance_type in instance_types
        ]

        return instance_type_objects
