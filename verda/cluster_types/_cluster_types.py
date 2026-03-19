from dataclasses import dataclass
from typing import Literal

from dataclasses_json import dataclass_json

CLUSTER_TYPES_ENDPOINT = '/cluster-types'

Currency = Literal['usd', 'eur']


@dataclass_json
@dataclass
class ClusterType:
    """Cluster type returned by the public API."""

    id: str
    model: str
    name: str
    cluster_type: str
    cpu: dict
    gpu: dict
    gpu_memory: dict
    memory: dict
    price_per_hour: float
    currency: Currency
    manufacturer: str
    node_details: list[str]
    supported_os: list[str]


class ClusterTypesService:
    """Service for interacting with cluster types."""

    def __init__(self, http_client) -> None:
        self._http_client = http_client

    def get(self, currency: Currency = 'usd') -> list[ClusterType]:
        """Return all available cluster types."""
        cluster_types = self._http_client.get(
            CLUSTER_TYPES_ENDPOINT,
            params={'currency': currency},
        ).json()
        return [
            ClusterType(
                id=cluster_type['id'],
                model=cluster_type['model'],
                name=cluster_type['name'],
                cluster_type=cluster_type['cluster_type'],
                cpu=cluster_type['cpu'],
                gpu=cluster_type['gpu'],
                gpu_memory=cluster_type['gpu_memory'],
                memory=cluster_type['memory'],
                price_per_hour=float(cluster_type['price_per_hour']),
                currency=cluster_type['currency'],
                manufacturer=cluster_type['manufacturer'],
                node_details=cluster_type['node_details'],
                supported_os=cluster_type['supported_os'],
            )
            for cluster_type in cluster_types
        ]
