import itertools
import time
from dataclasses import dataclass

from dataclasses_json import dataclass_json

from verda.constants import Actions, ClusterStatus, ErrorCodes, Locations
from verda.exceptions import APIException
from verda.http_client import HTTPClient

CLUSTERS_ENDPOINT = '/clusters'

# Default shared volume size is 30TB
DEFAULT_SHARED_VOLUME_SIZE = 30000


@dataclass_json
@dataclass
class ClusterWorkerNode:
    """Represents a worker node in a cluster.

    Attributes:
        id: Unique identifier for the node.
        status: Current status of the node.
        hostname: Network hostname of the node.
        private_ip: Private IP address of the node.
    """

    id: str
    status: str
    hostname: str
    private_ip: str


@dataclass_json
@dataclass
class SharedVolume:
    """Represents a shared volume in a cluster.

    Attributes:
        id: Unique identifier for the volume.
        name: Name of the volume.
        size_in_gigabytes: Size of the volume in gigabytes.
        mount_point: Mount point of the volume.
    """

    id: str
    name: str
    size_in_gigabytes: int
    mount_point: str | None = None


@dataclass_json
@dataclass
class Cluster:
    """Represents a compute cluster with multiple nodes.

    Attributes:
        id: Unique identifier for the cluster.
        hostname: Human-readable hostname of the cluster.
        description: Description of the cluster.
        status: Current operational status of the cluster.
        created_at: Timestamp of cluster creation.
        location: Datacenter location code (default: Locations.FIN_03).
        cluster_type: Type of the cluster.
        worker_nodes: List of nodes in the cluster.
        ssh_key_ids: List of SSH key IDs associated with the cluster nodes.
        image: Image ID or type used for cluster nodes.
        startup_script_id: ID of the startup script to run on nodes.
        public_ip: IP address of the jumphost.
    """

    id: str
    hostname: str
    description: str
    status: str
    created_at: str
    location: str
    cluster_type: str
    worker_nodes: list[ClusterWorkerNode]
    shared_volumes: list[SharedVolume]
    ssh_key_ids: list[str]

    image: str | None = None
    startup_script_id: str | None = None
    ip: str | None = None


class ClustersService:
    """Service for managing compute clusters through the API.

    This service provides methods to create, retrieve, and manage compute clusters.
    """

    def __init__(self, http_client: HTTPClient) -> None:
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
        cluster_type: str,
        image: str,
        hostname: str,
        *,
        description: str = '',
        ssh_key_ids: list = [],
        location: str = Locations.FIN_03,
        startup_script_id: str | None = None,
        shared_volume_name: str | None = None,
        shared_volume_size: int | None = None,
        wait_for_status: str | None = ClusterStatus.PROVISIONING,
        max_wait_time: float = 900,
        initial_interval: float = 1.0,
        max_interval: float = 10,
        backoff_coefficient: float = 2.0,
    ) -> Cluster:
        """Creates and deploys a new compute cluster.

        Args:
            hostname: Name for the cluster.
            cluster_type: Cluster type.
            image: Image type or ID for cluster nodes.
            description: Human-readable description of the cluster.
            ssh_key_ids: List of SSH key IDs to associate with cluster nodes.
            location: Datacenter location code (default: Locations.FIN_03).
            startup_script_id: Optional ID of startup script to run on nodes.
            shared_volume_name: Optional name for the shared volume.
            shared_volume_size: Optional size for the shared volume, in GB, default to 30TB.
            wait_for_status: Status to wait for the cluster to reach, default to PROVISIONING. If None, no wait is performed.
            max_wait_time: Maximum total wait for the cluster to start creating, in seconds (default: 900)
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
            'hostname': hostname,
            'cluster_type': cluster_type,
            'image': image,
            'description': description,
            'ssh_key_ids': ssh_key_ids,
            'contract': 'PAY_AS_YOU_GO',
            'location_code': location,
            'startup_script_id': startup_script_id,
            'shared_volume': {
                'name': shared_volume_name if shared_volume_name else hostname + '-shared-volume',
                'size': shared_volume_size if shared_volume_size else DEFAULT_SHARED_VOLUME_SIZE,
            },
        }
        response = self._http_client.post(CLUSTERS_ENDPOINT, json=payload).json()
        id = response['id']

        if not wait_for_status:
            return self.get_by_id(id)

        # Wait for cluster to enter creating state with timeout
        # TODO(shamrin) extract backoff logic, _instances module has the same code
        deadline = time.monotonic() + max_wait_time
        for i in itertools.count():
            cluster = self.get_by_id(id)
            if cluster.status == wait_for_status:
                return cluster

            if cluster.status == ClusterStatus.ERROR:
                raise APIException(ErrorCodes.SERVER_ERROR, f'Cluster {id} entered error state')

            if cluster.status == ClusterStatus.DISCONTINUED:
                raise APIException(ErrorCodes.SERVER_ERROR, f'Cluster {id} was discontinued')

            now = time.monotonic()
            if now >= deadline:
                raise TimeoutError(
                    f'Cluster {id} did not enter creating state within {max_wait_time:.1f} seconds'
                )

            interval = min(initial_interval * backoff_coefficient**i, max_interval, deadline - now)
            time.sleep(interval)

    def action(self, id_list: list[str] | str, action: str) -> None:
        """Performs an action on one or more clusters.

        Args:
            id_list: Single cluster ID or list of cluster IDs to act upon.
            action: Action to perform on the clusters. Only `delete` is supported.

        Raises:
            HTTPError: If the action fails or other API error occurs.
        """
        if action != Actions.DELETE:
            raise ValueError(f'Invalid action: {action}. Only DELETE is supported.')

        # TODO(shamrin) change public API to support `delete`
        action = 'discontinue'

        if isinstance(id_list, str):
            payload = {'actions': [{'id': id_list, 'action': action}]}
        else:
            payload = {'actions': [{'id': id, 'action': action} for id in id_list]}

        self._http_client.put(CLUSTERS_ENDPOINT, json=payload)

    def delete(self, cluster_id: str) -> None:
        """Deletes a cluster.

        Args:
            cluster_id: ID of the cluster to delete.
        """
        self.action(cluster_id, 'delete')

    def is_available(
        self,
        cluster_type: str,
        location_code: str | None = None,
    ) -> bool:
        """Checks if a specific cluster type is available for deployment.

        Args:
            cluster_type: Type of cluster to check availability for.
            location_code: Optional datacenter location code.

        Returns:
            True if the cluster type is available, False otherwise.
        """
        query_params = {'location_code': location_code}
        url = f'/cluster-availability/{cluster_type}'
        response = self._http_client.get(url, query_params).text
        return response == 'true'

    def get_availabilities(self, location_code: str | None = None) -> list[str]:
        """Retrieves a list of available cluster types across locations.

        Args:
            location_code: Optional datacenter location code to filter by.

        Returns:
            List of available cluster types and their details.
        """
        query_params = {'location_code': location_code}
        response = self._http_client.get('/cluster-availability', params=query_params).json()
        availabilities = response[0]['availabilities']
        return availabilities

    def get_cluster_images(
        self,
        cluster_type: str | None = None,
    ) -> list[str]:
        """Retrieves a list of available images for a given cluster type (optional).

        Args:
            cluster_type: Type of cluster to get images for.

        Returns:
            List of available images for the given cluster type.
        """
        query_params = {'instance_type': cluster_type}
        images = self._http_client.get('/images/cluster', params=query_params).json()
        return [image['image_type'] for image in images]
