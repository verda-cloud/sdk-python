import itertools
import time
from dataclasses import dataclass
from typing import Literal

from dataclasses_json import dataclass_json

from verda.constants import Locations

CLUSTERS_ENDPOINT = '/clusters'

ClusterStatus = Literal[
    'creating', 'running', 'scaling', 'updating', 'deleting', 'deleted', 'error'
]


@dataclass_json
@dataclass
class ClusterNode:
    """Represents a node in a cluster.

    Attributes:
        id: Unique identifier for the node (instance ID).
        instance_type: Type of the instance for this node.
        status: Current status of the node.
        hostname: Network hostname of the node.
        ip: IP address of the node.
        created_at: Timestamp of node creation.
    """

    id: str
    instance_type: str
    status: str
    hostname: str
    ip: str | None = None
    created_at: str | None = None


@dataclass_json
@dataclass
class Cluster:
    """Represents a compute cluster with multiple nodes.

    Attributes:
        id: Unique identifier for the cluster.
        name: Human-readable name of the cluster.
        description: Description of the cluster.
        status: Current operational status of the cluster.
        created_at: Timestamp of cluster creation.
        location: Datacenter location code (default: Locations.FIN_03).
        instance_type: Type of instances used for cluster nodes.
        node_count: Number of nodes in the cluster.
        nodes: List of nodes in the cluster.
        ssh_key_ids: List of SSH key IDs associated with the cluster nodes.
        image: Image ID or type used for cluster nodes.
        startup_script_id: ID of the startup script to run on nodes.
        master_ip: IP address of the cluster master/coordinator node.
        endpoint: Cluster access endpoint.
    """

    id: str
    name: str
    description: str
    status: str
    created_at: str
    location: str
    instance_type: str
    node_count: int
    nodes: list[ClusterNode]
    ssh_key_ids: list[str]
    image: str | None = None
    startup_script_id: str | None = None
    master_ip: str | None = None
    endpoint: str | None = None


class ClustersService:
    """Service for managing compute clusters through the API.

    This service provides methods to create, retrieve, scale, and manage compute clusters.
    """

    def __init__(self, http_client) -> None:
        """Initializes the ClustersService with an HTTP client.

        Args:
            http_client: HTTP client for making API requests.
        """
        self._http_client = http_client

    def get(self, status: str | None = None) -> list[Cluster]:
        """Retrieves all clusters or clusters with specific status.

        Args:
            status: Optional status filter for clusters. If None, returns all
                non-deleted clusters.

        Returns:
            List of cluster objects matching the criteria.
        """
        clusters_dict = self._http_client.get(CLUSTERS_ENDPOINT, params={'status': status}).json()
        return [
            Cluster.from_dict(cluster_dict, infer_missing=True) for cluster_dict in clusters_dict
        ]

    def get_by_id(self, id: str) -> Cluster:
        """Retrieves a specific cluster by its ID.

        Args:
            id: Unique identifier of the cluster to retrieve.

        Returns:
            Cluster object with the specified ID.

        Raises:
            HTTPError: If the cluster is not found or other API error occurs.
        """
        cluster_dict = self._http_client.get(CLUSTERS_ENDPOINT + f'/{id}').json()
        return Cluster.from_dict(cluster_dict, infer_missing=True)

    def create(
        self,
        name: str,
        instance_type: str,
        node_count: int,
        image: str,
        description: str,
        ssh_key_ids: list = [],
        location: str = Locations.FIN_03,
        startup_script_id: str | None = None,
        *,
        max_wait_time: float = 300,
        initial_interval: float = 1.0,
        max_interval: float = 10,
        backoff_coefficient: float = 2.0,
    ) -> Cluster:
        """Creates and deploys a new compute cluster.

        Args:
            name: Name for the cluster.
            instance_type: Type of instances to use for cluster nodes (e.g., '8V100.48V').
            node_count: Number of nodes to create in the cluster.
            image: Image type or ID for cluster nodes.
            description: Human-readable description of the cluster.
            ssh_key_ids: List of SSH key IDs to associate with cluster nodes.
            location: Datacenter location code (default: Locations.FIN_03).
            startup_script_id: Optional ID of startup script to run on nodes.
            max_wait_time: Maximum total wait for the cluster to start creating, in seconds (default: 300)
            initial_interval: Initial interval, in seconds (default: 1.0)
            max_interval: The longest single delay allowed between retries, in seconds (default: 10)
            backoff_coefficient: Coefficient to calculate the next retry interval (default 2.0)

        Returns:
            The newly created cluster object.

        Raises:
            HTTPError: If cluster creation fails or other API error occurs.
            TimeoutError: If cluster does not start creating within max_wait_time.
        """
        payload = {
            'name': name,
            'instance_type': instance_type,
            'node_count': node_count,
            'image': image,
            'description': description,
            'ssh_key_ids': ssh_key_ids,
            'location_code': location,
            'startup_script_id': startup_script_id,
        }
        id = self._http_client.post(CLUSTERS_ENDPOINT, json=payload).text

        # Wait for cluster to enter creating state with timeout
        deadline = time.monotonic() + max_wait_time
        for i in itertools.count():
            cluster = self.get_by_id(id)
            if cluster.status != 'ordered':
                return cluster

            now = time.monotonic()
            if now >= deadline:
                raise TimeoutError(
                    f'Cluster {id} did not enter creating state within {max_wait_time:.1f} seconds'
                )

            interval = min(initial_interval * backoff_coefficient**i, max_interval, deadline - now)
            time.sleep(interval)

    def delete(self, id: str) -> None:
        """Deletes a cluster and all its nodes.

        Args:
            id: Unique identifier of the cluster to delete.

        Raises:
            HTTPError: If the deletion fails or other API error occurs.
        """
        self._http_client.delete(CLUSTERS_ENDPOINT + f'/{id}')
        return

    def scale(
        self,
        id: str,
        node_count: int,
    ) -> Cluster:
        """Scales a cluster to the specified number of nodes.

        Args:
            id: Unique identifier of the cluster to scale.
            node_count: Target number of nodes for the cluster.

        Returns:
            Updated cluster object.

        Raises:
            HTTPError: If the scaling fails or other API error occurs.
        """
        payload = {'node_count': node_count}
        self._http_client.put(CLUSTERS_ENDPOINT + f'/{id}/scale', json=payload)
        return self.get_by_id(id)

    def get_nodes(self, id: str) -> list[ClusterNode]:
        """Retrieves all nodes in a cluster.

        Args:
            id: Unique identifier of the cluster.

        Returns:
            List of nodes in the cluster.

        Raises:
            HTTPError: If the cluster is not found or other API error occurs.
        """
        nodes_dict = self._http_client.get(CLUSTERS_ENDPOINT + f'/{id}/nodes').json()
        return [ClusterNode.from_dict(node_dict, infer_missing=True) for node_dict in nodes_dict]
