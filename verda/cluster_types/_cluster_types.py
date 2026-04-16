# Copyright 2026 Verda Cloud Oy
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from dataclasses import dataclass

from dataclasses_json import dataclass_json

from verda.constants import Currency

CLUSTER_TYPES_ENDPOINT = '/cluster-types'


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
