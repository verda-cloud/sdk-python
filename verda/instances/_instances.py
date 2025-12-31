import itertools
import time
from dataclasses import dataclass
from typing import Literal

from dataclasses_json import dataclass_json

from verda.constants import InstanceStatus, Locations

INSTANCES_ENDPOINT = '/instances'

Contract = Literal['LONG_TERM', 'PAY_AS_YOU_GO', 'SPOT']
Pricing = Literal['DYNAMIC_PRICE', 'FIXED_PRICE']


@dataclass_json
@dataclass
class Instance:
    """Represents a cloud instance with its configuration and state.

    Attributes:
        id: Unique identifier for the instance.
        instance_type: Type of the instance (e.g., '8V100.48V').
        price_per_hour: Cost per hour of running the instance.
        hostname: Network hostname of the instance.
        description: Human-readable description of the instance.
        status: Current operational status of the instance.
        created_at: Timestamp of instance creation.
        ssh_key_ids: List of SSH key IDs associated with the instance.
        cpu: CPU configuration details.
        gpu: GPU configuration details.
        memory: Memory configuration details.
        storage: Storage configuration details.
        gpu_memory: GPU memory configuration details.
        ip: IP address assigned to the instance.
        os_volume_id: ID of the operating system volume.
        location: Datacenter location code (default: Locations.FIN_03).
        image: Image ID or type used for the instance.
        startup_script_id: ID of the startup script to run.
        is_spot: Whether the instance is a spot instance.
        contract: Contract type for the instance. (e.g. 'LONG_TERM', 'PAY_AS_YOU_GO', 'SPOT')
        pricing: Pricing model for the instance. (e.g. 'DYNAMIC_PRICE', 'FIXED_PRICE')
    """

    id: str
    instance_type: str
    price_per_hour: float
    hostname: str
    description: str
    status: str
    created_at: str
    ssh_key_ids: list[str]
    cpu: dict
    gpu: dict
    memory: dict
    storage: dict
    gpu_memory: dict
    # Can be None if instance is still not provisioned
    ip: str | None = None
    # Can be None if instance is still not provisioned
    os_volume_id: str | None = None
    location: str = Locations.FIN_03
    image: str | None = None
    startup_script_id: str | None = None
    is_spot: bool = False
    contract: Contract | None = None
    pricing: Pricing | None = None


class InstancesService:
    """Service for managing cloud instances through the API.

    This service provides methods to create, retrieve, and manage cloud instances.
    """

    def __init__(self, http_client) -> None:
        """Initializes the InstancesService with an HTTP client.

        Args:
            http_client: HTTP client for making API requests.
        """
        self._http_client = http_client

    def get(self, status: str | None = None) -> list[Instance]:
        """Retrieves all non-deleted instances or instances with specific status.

        Args:
            status: Optional status filter for instances. If None, returns all
                non-deleted instances.

        Returns:
            List of instance objects matching the criteria.
        """
        instances_dict = self._http_client.get(INSTANCES_ENDPOINT, params={'status': status}).json()
        return [
            Instance.from_dict(instance_dict, infer_missing=True)
            for instance_dict in instances_dict
        ]

    def get_by_id(self, id: str) -> Instance:
        """Retrieves a specific instance by its ID.

        Args:
            id: Unique identifier of the instance to retrieve.

        Returns:
            Instance object with the specified ID.

        Raises:
            HTTPError: If the instance is not found or other API error occurs.
        """
        instance_dict = self._http_client.get(INSTANCES_ENDPOINT + f'/{id}').json()
        return Instance.from_dict(instance_dict, infer_missing=True)

    def create(
        self,
        instance_type: str,
        image: str,
        hostname: str,
        description: str,
        ssh_key_ids: list = [],
        location: str = Locations.FIN_03,
        startup_script_id: str | None = None,
        volumes: list[dict] | None = None,
        existing_volumes: list[str] | None = None,
        os_volume: dict | None = None,
        is_spot: bool = False,
        contract: Contract | None = None,
        pricing: Pricing | None = None,
        coupon: str | None = None,
        *,
        max_wait_time: float = 180,
        initial_interval: float = 0.5,
        max_interval: float = 5,
        backoff_coefficient: float = 2.0,
    ) -> Instance:
        """Creates and deploys a new cloud instance.

        Args:
            instance_type: Type of instance to create (e.g., '8V100.48V').
            image: Image type or existing OS volume ID for the instance.
            hostname: Network hostname for the instance.
            description: Human-readable description of the instance.
            ssh_key_ids: List of SSH key IDs to associate with the instance.
            location: Datacenter location code (default: Locations.FIN_03).
            startup_script_id: Optional ID of startup script to run.
            volumes: Optional list of volume configurations to create.
            existing_volumes: Optional list of existing volume IDs to attach.
            os_volume: Optional OS volume configuration details.
            is_spot: Whether to create a spot instance.
            contract: Optional contract type for the instance.
            pricing: Optional pricing model for the instance.
            coupon: Optional coupon code for discounts.
            max_wait_time: Maximum total wait for the instance to start provisioning, in seconds (default: 180)
            initial_interval: Initial interval, in seconds (default: 0.5)
            max_interval: The longest single delay allowed between retries, in seconds (default: 5)
            backoff_coefficient: Coefficient to calculate the next retry interval (default 2.0)

        Returns:
            The newly created instance object.

        Raises:
            HTTPError: If instance creation fails or other API error occurs.
        """
        payload = {
            'instance_type': instance_type,
            'image': image,
            'ssh_key_ids': ssh_key_ids,
            'startup_script_id': startup_script_id,
            'hostname': hostname,
            'description': description,
            'location_code': location,
            'os_volume': os_volume,
            'volumes': volumes or [],
            'existing_volumes': existing_volumes or [],
            'is_spot': is_spot,
            'coupon': coupon,
        }
        if contract:
            payload['contract'] = contract
        if pricing:
            payload['pricing'] = pricing
        id = self._http_client.post(INSTANCES_ENDPOINT, json=payload).text

        # Wait for instance to enter provisioning state with timeout
        # TODO(shamrin) extract backoff logic, _clusters module has the same code
        deadline = time.monotonic() + max_wait_time
        for i in itertools.count():
            instance = self.get_by_id(id)
            if instance.status != InstanceStatus.ORDERED:
                return instance

            now = time.monotonic()
            if now >= deadline:
                raise TimeoutError(
                    f'Instance {id} did not enter provisioning state within {max_wait_time:.1f} seconds'
                )

            interval = min(initial_interval * backoff_coefficient**i, max_interval, deadline - now)
            time.sleep(interval)

    def action(
        self,
        id_list: list[str] | str,
        action: str,
        volume_ids: list[str] | None = None,
    ) -> None:
        """Performs an action on one or more instances.

        Args:
            id_list: Single instance ID or list of instance IDs to act upon.
            action: Action to perform on the instances.
            volume_ids: Optional list of volume IDs to delete.

        Raises:
            HTTPError: If the action fails or other API error occurs.
        """
        if type(id_list) is str:
            id_list = [id_list]

        payload = {'id': id_list, 'action': action, 'volume_ids': volume_ids}

        self._http_client.put(INSTANCES_ENDPOINT, json=payload)
        return

    def is_available(
        self,
        instance_type: str,
        is_spot: bool = False,
        location_code: str | None = None,
    ) -> bool:
        """Checks if a specific instance type is available for deployment.

        Args:
            instance_type: Type of instance to check availability for.
            is_spot: Whether to check spot instance availability.
            location_code: Optional datacenter location code.

        Returns:
            True if the instance type is available, False otherwise.
        """
        is_spot = str(is_spot).lower()
        query_params = {'isSpot': is_spot, 'location_code': location_code}
        url = f'/instance-availability/{instance_type}'
        return self._http_client.get(url, query_params).json()

    def get_availabilities(
        self, is_spot: bool | None = None, location_code: str | None = None
    ) -> list[dict]:
        """Retrieves a list of available instance types across locations.

        Args:
            is_spot: Optional flag to filter spot instance availability.
            location_code: Optional datacenter location code to filter by.

        Returns:
            List of available instance types and their details.
        """
        is_spot = str(is_spot).lower() if is_spot is not None else None
        query_params = {'isSpot': is_spot, 'location_code': location_code}
        return self._http_client.get('/instance-availability', params=query_params).json()
