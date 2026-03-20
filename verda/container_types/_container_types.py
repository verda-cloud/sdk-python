from dataclasses import dataclass

from dataclasses_json import dataclass_json

from verda.constants import Currency

CONTAINER_TYPES_ENDPOINT = '/container-types'


@dataclass_json
@dataclass
class ContainerType:
    """Container type returned by the public API."""

    id: str
    model: str
    name: str
    instance_type: str
    cpu: dict
    gpu: dict
    gpu_memory: dict
    memory: dict
    serverless_price: float
    serverless_spot_price: float
    currency: Currency
    manufacturer: str


class ContainerTypesService:
    """Service for interacting with container types."""

    def __init__(self, http_client) -> None:
        self._http_client = http_client

    def get(self, currency: Currency = 'usd') -> list[ContainerType]:
        """Return all available container types."""
        container_types = self._http_client.get(
            CONTAINER_TYPES_ENDPOINT,
            params={'currency': currency},
        ).json()
        return [
            ContainerType(
                id=container_type['id'],
                model=container_type['model'],
                name=container_type['name'],
                instance_type=container_type['instance_type'],
                cpu=container_type['cpu'],
                gpu=container_type['gpu'],
                gpu_memory=container_type['gpu_memory'],
                memory=container_type['memory'],
                serverless_price=float(container_type['serverless_price']),
                serverless_spot_price=float(container_type['serverless_spot_price']),
                currency=container_type['currency'],
                manufacturer=container_type['manufacturer'],
            )
            for container_type in container_types
        ]
