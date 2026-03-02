"""Container deployment and management service for Verda.

This module provides functionality for managing container deployments, including
creation, updates, deletion, and monitoring of containerized applications.
"""

import base64
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from dataclasses_json import Undefined, dataclass_json  # type: ignore

from verda.http_client import HTTPClient
from verda.inference_client import InferenceClient, InferenceResponse

# API endpoints
CONTAINER_DEPLOYMENTS_ENDPOINT = '/container-deployments'
SERVERLESS_COMPUTE_RESOURCES_ENDPOINT = '/serverless-compute-resources'
CONTAINER_REGISTRY_CREDENTIALS_ENDPOINT = '/container-registry-credentials'
SECRETS_ENDPOINT = '/secrets'
FILESET_SECRETS_ENDPOINT = '/file-secrets'


class EnvVarType(str, Enum):
    """Types of environment variables that can be set in containers."""

    PLAIN = 'plain'
    SECRET = 'secret'


class SecretType(str, Enum):
    """Types of secrets that can be set in containers."""

    GENERIC = 'generic'  # Regular secret, can be used in env vars
    FILESET = 'file-secret'  # A file secret that can be mounted into the container


class VolumeMountType(str, Enum):
    """Types of volume mounts that can be configured for containers."""

    SCRATCH = 'scratch'
    SECRET = 'secret'
    MEMORY = 'memory'
    SHARED = 'shared'


class ContainerRegistryType(str, Enum):
    """Supported container registry types."""

    GCR = 'gcr'
    DOCKERHUB = 'dockerhub'
    GITHUB = 'ghcr'
    AWS_ECR = 'aws-ecr'
    CUSTOM = 'custom'


class ContainerDeploymentStatus(str, Enum):
    """Possible states of a container deployment."""

    INITIALIZING = 'initializing'
    HEALTHY = 'healthy'
    DEGRADED = 'degraded'
    UNHEALTHY = 'unhealthy'
    PAUSED = 'paused'
    QUOTA_REACHED = 'quota_reached'
    IMAGE_PULLING = 'image_pulling'
    VERSION_UPDATING = 'version_updating'


@dataclass_json
@dataclass
class HealthcheckSettings:
    """Configuration for container health checking.

    Attributes:
        enabled: Whether health checking is enabled.
        port: Port number to perform health check on.
        path: HTTP path to perform health check on.
    """

    enabled: bool = True
    port: int | None = None
    path: str | None = None


@dataclass_json
@dataclass
class EntrypointOverridesSettings:
    """Configuration for overriding container entrypoint and command.

    Attributes:
        enabled: Whether entrypoint overrides are enabled.
        entrypoint: List of strings forming the entrypoint command.
        cmd: List of strings forming the command arguments.
    """

    enabled: bool = True
    entrypoint: list[str] | None = None
    cmd: list[str] | None = None


@dataclass_json
@dataclass
class EnvVar:
    """Environment variable configuration for containers.

    Attributes:
        name: Name of the environment variable.
        value_or_reference_to_secret: Direct value or reference to a secret.
        type: Type of the environment variable.
    """

    name: str
    value_or_reference_to_secret: str
    type: EnvVarType


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class VolumeMount:
    """Base class for volume mount configurations.

    Attributes:
        type: Type of volume mount.
        mount_path: Path where the volume should be mounted in the container.
        size_in_mb: Size of the volume in megabytes. Deprecated: use MemoryMount for memory volumes instead.
    """

    type: VolumeMountType
    mount_path: str
    # Deprecated: use MemoryMount for memory volumes instead.
    size_in_mb: int | None = field(default=None, kw_only=True)


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class GeneralStorageMount(VolumeMount):
    """General storage volume mount configuration."""

    def __init__(self, mount_path: str):
        """Initialize a general scratch volume mount.

        Args:
            mount_path: Path where the volume should be mounted in the container.
        """
        super().__init__(type=VolumeMountType.SCRATCH, mount_path=mount_path)


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class SecretMount(VolumeMount):
    """Secret volume mount configuration.

    A secret volume mount allows mounting secret files into the container.

    Attributes:
        secret_name: The name of the fileset secret to mount. This secret must be created in advance, for example using `create_fileset_secret_from_file_paths`
        file_names: List of file names that are part of the fileset secret.
    """

    secret_name: str
    file_names: list[str] | None = None

    def __init__(self, mount_path: str, secret_name: str, file_names: list[str] | None = None):
        self.secret_name = secret_name
        self.file_names = file_names
        super().__init__(type=VolumeMountType.SECRET, mount_path=mount_path)


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class MemoryMount(VolumeMount):
    """Memory volume mount configuration.

    A memory volume mount provides high-speed, ephemeral in-memory storage inside your container.
    The mount path is currently hardcoded to /dev/shm and cannot be changed.

    Attributes:
        size_in_mb: Size of the memory volume in megabytes.
    """

    size_in_mb: int

    def __init__(self, size_in_mb: int):
        super().__init__(type=VolumeMountType.MEMORY, mount_path='/dev/shm')
        self.size_in_mb = size_in_mb


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class SharedFileSystemMount(VolumeMount):
    """Shared filesystem volume mount configuration.

    A shared filesystem volume mount allows mounting a shared filesystem into the container.
    """

    volume_id: str  # The ID of the shared filesystem volume to mount, needs to be created first

    def __init__(self, mount_path: str, volume_id: str):
        super().__init__(type=VolumeMountType.SHARED, mount_path=mount_path)
        self.volume_id = volume_id


@dataclass_json
@dataclass
class Container:
    """Container configuration for deployment creation and updates.

    Attributes:
        image: Container image to use.
        exposed_port: Port to expose from the container.
        name: Name of the container (system-managed, read-only).
        healthcheck: Optional health check configuration.
        entrypoint_overrides: Optional entrypoint override settings.
        env: Optional list of environment variables.
        volume_mounts: Optional list of volume mounts.
    """

    image: str | dict
    exposed_port: int
    name: str | None = None
    healthcheck: HealthcheckSettings | None = None
    entrypoint_overrides: EntrypointOverridesSettings | None = None
    env: list[EnvVar] | None = None
    volume_mounts: list[VolumeMount] | None = None


@dataclass_json
@dataclass
class ContainerRegistryCredentials:
    """Credentials for accessing a container registry.

    Attributes:
        name: Name of the credentials.
    """

    name: str


@dataclass_json
@dataclass
class ContainerRegistrySettings:
    """Settings for container registry access.

    Attributes:
        is_private: Whether the registry is private.
        credentials: Optional credentials for accessing private registry.
    """

    is_private: bool
    credentials: ContainerRegistryCredentials | None = None


@dataclass_json
@dataclass
class ComputeResource:
    """Compute resource configuration.

    Attributes:
        name: Name of the compute resource.
        size: Size of the compute resource.
        is_available: Whether the compute resource is currently available.
    """

    name: str
    size: int
    # Made optional since it's only used in API responses
    is_available: bool | None = None


@dataclass_json
@dataclass
class ScalingPolicy:
    """Policy for controlling scaling behavior.

    Attributes:
        delay_seconds: Number of seconds to wait before applying scaling action.
    """

    delay_seconds: int


@dataclass_json
@dataclass
class QueueLoadScalingTrigger:
    """Trigger for scaling based on queue load.

    Attributes:
        threshold: Queue load threshold that triggers scaling.
    """

    threshold: float


@dataclass_json
@dataclass
class UtilizationScalingTrigger:
    """Trigger for scaling based on resource utilization.

    Attributes:
        enabled: Whether this trigger is enabled.
        threshold: Utilization threshold that triggers scaling.
    """

    enabled: bool
    threshold: float | None = None


@dataclass_json
@dataclass
class ScalingTriggers:
    """Collection of triggers that can cause scaling actions.

    Attributes:
        queue_load: Optional trigger based on queue load.
        cpu_utilization: Optional trigger based on CPU utilization.
        gpu_utilization: Optional trigger based on GPU utilization.
    """

    queue_load: QueueLoadScalingTrigger | None = None
    cpu_utilization: UtilizationScalingTrigger | None = None
    gpu_utilization: UtilizationScalingTrigger | None = None


@dataclass_json
@dataclass
class ScalingOptions:
    """Configuration for automatic scaling behavior.

    Attributes:
        min_replica_count: Minimum number of replicas to maintain.
        max_replica_count: Maximum number of replicas allowed.
        scale_down_policy: Policy for scaling down replicas.
        scale_up_policy: Policy for scaling up replicas.
        queue_message_ttl_seconds: Time-to-live for queue messages in seconds.
        concurrent_requests_per_replica: Number of concurrent requests each replica can handle.
        scaling_triggers: Configuration for various scaling triggers.
    """

    min_replica_count: int
    max_replica_count: int
    scale_down_policy: ScalingPolicy
    scale_up_policy: ScalingPolicy
    queue_message_ttl_seconds: int
    concurrent_requests_per_replica: int
    scaling_triggers: ScalingTriggers


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Deployment:
    """Configuration for creating or updating a container deployment.

    Attributes:
        name: Name of the deployment.
        container_registry_settings: Settings for accessing container registry.
        containers: List of container specifications in the deployment.
        compute: Compute resource configuration.
        is_spot: Whether is spot deployment.
        endpoint_base_url: Optional base URL for the deployment endpoint.
        scaling: Optional scaling configuration.
        created_at: Optional timestamp when the deployment was created.
    """

    name: str
    containers: list[Container]
    compute: ComputeResource
    container_registry_settings: ContainerRegistrySettings = field(
        default_factory=lambda: ContainerRegistrySettings(is_private=False)
    )
    is_spot: bool = False
    endpoint_base_url: str | None = None
    scaling: ScalingOptions | None = None
    created_at: str | None = None

    _inference_client: InferenceClient | None = None

    def __str__(self):
        """Returns a string representation of the deployment, excluding sensitive information.

        Returns:
            str: A formatted string representation of the deployment.
        """
        # Get all attributes except _inference_client
        attrs = {k: v for k, v in self.__dict__.items() if k != '_inference_client'}
        # Format each attribute
        attr_strs = [f'{k}={v!r}' for k, v in attrs.items()]
        return f'Deployment({", ".join(attr_strs)})'

    def __repr__(self):
        """Returns a repr representation of the deployment, excluding sensitive information.

        Returns:
            str: A formatted string representation of the deployment.
        """
        return self.__str__()

    @classmethod
    def from_dict_with_inference_key(
        cls, data: dict[str, Any], inference_key: str | None = None
    ) -> 'Deployment':
        """Creates a Deployment instance from a dictionary with an inference key.

        Args:
            data: Dictionary containing deployment data.
            inference_key: Inference key to set on the deployment.

        Returns:
            Deployment: A new Deployment instance with the inference client initialized.
        """
        deployment = Deployment.from_dict(data, infer_missing=True)
        if inference_key and deployment.endpoint_base_url:
            deployment._inference_client = InferenceClient(
                inference_key=inference_key,
                endpoint_base_url=deployment.endpoint_base_url,
            )
        return deployment

    def set_inference_client(self, inference_key: str) -> None:
        """Sets the inference client for this deployment.

        Args:
            inference_key: The inference key to use for authentication.

        Raises:
            ValueError: If endpoint_base_url is not set.
        """
        if self.endpoint_base_url is None:
            raise ValueError('Endpoint base URL must be set to use inference client')
        self._inference_client = InferenceClient(
            inference_key=inference_key, endpoint_base_url=self.endpoint_base_url
        )

    def _validate_inference_client(self) -> None:
        """Validates that the inference client is initialized.

        Raises:
            ValueError: If inference client is not initialized.
        """
        if self._inference_client is None:
            raise ValueError(
                'Inference client not initialized. Use from_dict_with_inference_key or set_inference_client to initialize inference capabilities.'
            )

    def run_sync(
        self,
        data: dict[str, Any],
        path: str = '',
        timeout_seconds: int = 60 * 5,
        headers: dict[str, str] | None = None,
        http_method: str = 'POST',
        stream: bool = False,
    ) -> InferenceResponse:
        """Runs a synchronous inference request.

        Args:
            data: The data to send in the request.
            path: The endpoint path to send the request to.
            timeout_seconds: Maximum time to wait for the response.
            headers: Optional headers to include in the request.
            http_method: The HTTP method to use for the request.
            stream: Whether to stream the response.

        Returns:
            InferenceResponse: The response from the inference request.

        Raises:
            ValueError: If the inference client is not initialized.
        """
        self._validate_inference_client()
        return self._inference_client.run_sync(
            data, path, timeout_seconds, headers, http_method, stream
        )

    def run(
        self,
        data: dict[str, Any],
        path: str = '',
        timeout_seconds: int = 60 * 5,
        headers: dict[str, str] | None = None,
        http_method: str = 'POST',
        stream: bool = False,
    ):
        """Runs an asynchronous inference request.

        Args:
            data: The data to send in the request.
            path: The endpoint path to send the request to.
            timeout_seconds: Maximum time to wait for the response.
            headers: Optional headers to include in the request.
            http_method: The HTTP method to use for the request.
            stream: Whether to stream the response.

        Returns:
            The response from the inference request.

        Raises:
            ValueError: If the inference client is not initialized.
        """
        self._validate_inference_client()
        return self._inference_client.run(data, path, timeout_seconds, headers, http_method, stream)

    def health(self):
        """Checks the health of the deployed application.

        Returns:
            The health check response.

        Raises:
            ValueError: If the inference client is not initialized.
        """
        self._validate_inference_client()
        # build healthcheck path
        healthcheck_path = '/health'
        if (
            self.containers
            and self.containers[0].healthcheck
            and self.containers[0].healthcheck.path
        ):
            healthcheck_path = self.containers[0].healthcheck.path

        return self._inference_client.health(healthcheck_path)

    # Function alias
    healthcheck = health


@dataclass_json
@dataclass
class ReplicaInfo:
    """Information about a deployment replica.

    Attributes:
        id: Unique identifier of the replica.
        status: Current status of the replica.
        started_at: Timestamp when the replica was started.
    """

    id: str
    status: str
    started_at: str


@dataclass_json
@dataclass
class Secret:
    """A secret model class.

    Attributes:
        name: Name of the secret.
        created_at: Timestamp when the secret was created.
        secret_type: Type of the secret.
    """

    name: str
    created_at: str
    secret_type: SecretType


@dataclass_json
@dataclass
class RegistryCredential:
    """A container registry credential model class.

    Attributes:
        name: Name of the registry credential.
        created_at: Timestamp when the credential was created.
    """

    name: str
    created_at: str


@dataclass_json
@dataclass
class BaseRegistryCredentials:
    """Base class for registry credentials.

    Attributes:
        name: Name of the registry credential.
        type: Type of the container registry.
    """

    name: str
    type: ContainerRegistryType


@dataclass_json
@dataclass
class DockerHubCredentials(BaseRegistryCredentials):
    """Credentials for DockerHub registry.

    Attributes:
        username: DockerHub username.
        access_token: DockerHub access token.
    """

    username: str
    access_token: str

    def __init__(self, name: str, username: str, access_token: str):
        """Initializes DockerHub credentials.

        Args:
            name: Name of the credentials.
            username: DockerHub username.
            access_token: DockerHub access token.
        """
        super().__init__(name=name, type=ContainerRegistryType.DOCKERHUB)
        self.username = username
        self.access_token = access_token


@dataclass_json
@dataclass
class GithubCredentials(BaseRegistryCredentials):
    """Credentials for GitHub Container Registry.

    Attributes:
        username: GitHub username.
        access_token: GitHub access token.
    """

    username: str
    access_token: str

    def __init__(self, name: str, username: str, access_token: str):
        """Initializes GitHub credentials.

        Args:
            name: Name of the credentials.
            username: GitHub username.
            access_token: GitHub access token.
        """
        super().__init__(name=name, type=ContainerRegistryType.GITHUB)
        self.username = username
        self.access_token = access_token


@dataclass_json
@dataclass
class GCRCredentials(BaseRegistryCredentials):
    """Credentials for Google Container Registry.

    Attributes:
        service_account_key: GCP service account key JSON.
    """

    service_account_key: str

    def __init__(self, name: str, service_account_key: str):
        """Initializes GCR credentials.

        Args:
            name: Name of the credentials.
            service_account_key: GCP service account key JSON.
        """
        super().__init__(name=name, type=ContainerRegistryType.GCR)
        self.service_account_key = service_account_key


@dataclass_json
@dataclass
class AWSECRCredentials(BaseRegistryCredentials):
    """Credentials for AWS Elastic Container Registry.

    Attributes:
        access_key_id: AWS access key ID.
        secret_access_key: AWS secret access key.
        region: AWS region.
        ecr_repo: ECR repository name.
    """

    access_key_id: str
    secret_access_key: str
    region: str
    ecr_repo: str

    def __init__(
        self,
        name: str,
        access_key_id: str,
        secret_access_key: str,
        region: str,
        ecr_repo: str,
    ):
        """Initializes AWS ECR credentials.

        Args:
            name: Name of the credentials.
            access_key_id: AWS access key ID.
            secret_access_key: AWS secret access key.
            region: AWS region.
            ecr_repo: ECR repository name.
        """
        super().__init__(name=name, type=ContainerRegistryType.AWS_ECR)
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.region = region
        self.ecr_repo = ecr_repo


@dataclass_json
@dataclass
class CustomRegistryCredentials(BaseRegistryCredentials):
    """Credentials for custom container registries.

    Attributes:
        docker_config_json: Docker config JSON containing registry credentials.
    """

    docker_config_json: str

    def __init__(self, name: str, docker_config_json: str):
        """Initializes custom registry credentials.

        Args:
            name: Name of the credentials.
            docker_config_json: Docker config JSON containing registry credentials.
        """
        super().__init__(name=name, type=ContainerRegistryType.CUSTOM)
        self.docker_config_json = docker_config_json


class ContainersService:
    """Service for managing container deployments.

    This class provides methods for interacting with container deployment API,
    including CRUD operations for deployments and related resources.
    """

    def __init__(self, http_client: HTTPClient, inference_key: str | None = None) -> None:
        """Initializes the containers service.

        Args:
            http_client: HTTP client for making API requests.
            inference_key: Optional inference key for authenticating inference requests.
        """
        self.client = http_client
        self._inference_key = inference_key

    def get_deployments(self) -> list[Deployment]:
        """Retrieves all container deployments.

        Returns:
            list[Deployment]: List of all deployments.
        """
        response = self.client.get(CONTAINER_DEPLOYMENTS_ENDPOINT)
        return [
            Deployment.from_dict_with_inference_key(deployment, self._inference_key)
            for deployment in response.json()
        ]

    def get_deployment_by_name(self, deployment_name: str) -> Deployment:
        """Retrieves a specific deployment by name.

        Args:
            deployment_name: Name of the deployment to retrieve.

        Returns:
            Deployment: The requested deployment.
        """
        response = self.client.get(f'{CONTAINER_DEPLOYMENTS_ENDPOINT}/{deployment_name}')
        return Deployment.from_dict_with_inference_key(response.json(), self._inference_key)

    # Function alias
    get_deployment = get_deployment_by_name

    def create_deployment(self, deployment: Deployment) -> Deployment:
        """Creates a new container deployment.

        Args:
            deployment: Deployment configuration to create.

        Returns:
            Deployment: The created deployment.
        """
        response = self.client.post(CONTAINER_DEPLOYMENTS_ENDPOINT, deployment.to_dict())
        return Deployment.from_dict_with_inference_key(response.json(), self._inference_key)

    def update_deployment(self, deployment_name: str, deployment: Deployment) -> Deployment:
        """Updates an existing deployment.

        Args:
            deployment_name: Name of the deployment to update.
            deployment: Updated deployment configuration.

        Returns:
            Deployment: The updated deployment.
        """
        response = self.client.patch(
            f'{CONTAINER_DEPLOYMENTS_ENDPOINT}/{deployment_name}', deployment.to_dict()
        )
        return Deployment.from_dict_with_inference_key(response.json(), self._inference_key)

    def delete_deployment(self, deployment_name: str) -> None:
        """Deletes a deployment.

        Args:
            deployment_name: Name of the deployment to delete.
        """
        self.client.delete(f'{CONTAINER_DEPLOYMENTS_ENDPOINT}/{deployment_name}')

    def get_deployment_status(self, deployment_name: str) -> ContainerDeploymentStatus:
        """Retrieves the current status of a deployment.

        Args:
            deployment_name: Name of the deployment.

        Returns:
            ContainerDeploymentStatus: Current status of the deployment.
        """
        response = self.client.get(f'{CONTAINER_DEPLOYMENTS_ENDPOINT}/{deployment_name}/status')
        return ContainerDeploymentStatus(response.json()['status'])

    def restart_deployment(self, deployment_name: str) -> None:
        """Restarts a deployment.

        Args:
            deployment_name: Name of the deployment to restart.
        """
        self.client.post(f'{CONTAINER_DEPLOYMENTS_ENDPOINT}/{deployment_name}/restart')

    def get_deployment_scaling_options(self, deployment_name: str) -> ScalingOptions:
        """Retrieves the scaling options for a deployment.

        Args:
            deployment_name: Name of the deployment.

        Returns:
            ScalingOptions: Current scaling options for the deployment.
        """
        response = self.client.get(f'{CONTAINER_DEPLOYMENTS_ENDPOINT}/{deployment_name}/scaling')
        return ScalingOptions.from_dict(response.json())

    def update_deployment_scaling_options(
        self, deployment_name: str, scaling_options: ScalingOptions
    ) -> ScalingOptions:
        """Updates the scaling options for a deployment.

        Args:
            deployment_name: Name of the deployment.
            scaling_options: New scaling options to apply.

        Returns:
            ScalingOptions: Updated scaling options for the deployment.
        """
        response = self.client.patch(
            f'{CONTAINER_DEPLOYMENTS_ENDPOINT}/{deployment_name}/scaling',
            scaling_options.to_dict(),
        )
        return ScalingOptions.from_dict(response.json())

    def get_deployment_replicas(self, deployment_name: str) -> list[ReplicaInfo]:
        """Retrieves information about deployment replicas.

        Args:
            deployment_name: Name of the deployment.

        Returns:
            list[ReplicaInfo]: List of replica information.
        """
        response = self.client.get(f'{CONTAINER_DEPLOYMENTS_ENDPOINT}/{deployment_name}/replicas')
        return [ReplicaInfo.from_dict(replica) for replica in response.json()['list']]

    def purge_deployment_queue(self, deployment_name: str) -> None:
        """Purges the deployment queue.

        Args:
            deployment_name: Name of the deployment.
        """
        self.client.post(f'{CONTAINER_DEPLOYMENTS_ENDPOINT}/{deployment_name}/purge-queue')

    def pause_deployment(self, deployment_name: str) -> None:
        """Pauses a deployment.

        Args:
            deployment_name: Name of the deployment to pause.
        """
        self.client.post(f'{CONTAINER_DEPLOYMENTS_ENDPOINT}/{deployment_name}/pause')

    def resume_deployment(self, deployment_name: str) -> None:
        """Resumes a paused deployment.

        Args:
            deployment_name: Name of the deployment to resume.
        """
        self.client.post(f'{CONTAINER_DEPLOYMENTS_ENDPOINT}/{deployment_name}/resume')

    def get_deployment_environment_variables(self, deployment_name: str) -> dict[str, list[EnvVar]]:
        """Retrieves environment variables for a deployment.

        Args:
            deployment_name: Name of the deployment.

        Returns:
            dict[str, list[EnvVar]]: Dictionary mapping container names to their environment variables.
        """
        response = self.client.get(
            f'{CONTAINER_DEPLOYMENTS_ENDPOINT}/{deployment_name}/environment-variables'
        )
        result = {}
        for item in response.json():
            container_name = item['container_name']
            env_vars = item['env']
            result[container_name] = [EnvVar.from_dict(env_var) for env_var in env_vars]
        return result

    def add_deployment_environment_variables(
        self, deployment_name: str, container_name: str, env_vars: list[EnvVar]
    ) -> dict[str, list[EnvVar]]:
        """Adds environment variables to a container in a deployment.

        Args:
            deployment_name: Name of the deployment.
            container_name: Name of the container.
            env_vars: List of environment variables to add.

        Returns:
            dict[str, list[EnvVar]]: Updated environment variables for all containers.
        """
        response = self.client.post(
            f'{CONTAINER_DEPLOYMENTS_ENDPOINT}/{deployment_name}/environment-variables',
            {
                'container_name': container_name,
                'env': [env_var.to_dict() for env_var in env_vars],
            },
        )
        result = {}
        for item in response.json():
            container_name = item['container_name']
            env_vars = item['env']
            result[container_name] = [EnvVar.from_dict(env_var) for env_var in env_vars]
        return result

    def update_deployment_environment_variables(
        self, deployment_name: str, container_name: str, env_vars: list[EnvVar]
    ) -> dict[str, list[EnvVar]]:
        """Updates environment variables for a container in a deployment.

        Args:
            deployment_name: Name of the deployment.
            container_name: Name of the container.
            env_vars: List of updated environment variables.

        Returns:
            dict[str, list[EnvVar]]: Updated environment variables for all containers.
        """
        response = self.client.patch(
            f'{CONTAINER_DEPLOYMENTS_ENDPOINT}/{deployment_name}/environment-variables',
            {
                'container_name': container_name,
                'env': [env_var.to_dict() for env_var in env_vars],
            },
        )
        result = {}
        item = response.json()
        container_name = item['container_name']
        env_vars = item['env']
        result[container_name] = [EnvVar.from_dict(env_var) for env_var in env_vars]
        return result

    def delete_deployment_environment_variables(
        self, deployment_name: str, container_name: str, env_var_names: list[str]
    ) -> dict[str, list[EnvVar]]:
        """Deletes environment variables from a container in a deployment.

        Args:
            deployment_name: Name of the deployment.
            container_name: Name of the container.
            env_var_names: List of environment variable names to delete.

        Returns:
            dict[str, list[EnvVar]]: Updated environment variables for all containers.
        """
        response = self.client.delete(
            f'{CONTAINER_DEPLOYMENTS_ENDPOINT}/{deployment_name}/environment-variables',
            {'container_name': container_name, 'env': env_var_names},
        )
        result = {}
        for item in response.json():
            container_name = item['container_name']
            env_vars = item['env']
            result[container_name] = [EnvVar.from_dict(env_var) for env_var in env_vars]
        return result

    def get_compute_resources(
        self, size: int | None = None, is_available: bool | None = None
    ) -> list[ComputeResource]:
        """Retrieves compute resources, optionally filtered by size and availability.

        Args:
            size: Optional size to filter resources by (e.g. 8 for 8x GPUs)
            is_available: Optional boolean to filter by availability status

        Returns:
            list[ComputeResource]: List of compute resources matching the filters.
                                 If no filters provided, returns all resources.
        """
        response = self.client.get(SERVERLESS_COMPUTE_RESOURCES_ENDPOINT)
        resources = []
        for resource in response.json():
            resources.append(ComputeResource.from_dict(resource))
        if size:
            resources = [r for r in resources if r.size == size]
        if is_available:
            resources = [r for r in resources if r.is_available == is_available]
        return resources

    # Function alias
    get_gpus = get_compute_resources

    def get_secrets(self) -> list[Secret]:
        """Retrieves all secrets.

        Returns:
            list[Secret]: List of all secrets.
        """
        response = self.client.get(SECRETS_ENDPOINT)
        return [Secret.from_dict(secret) for secret in response.json()]

    def create_secret(self, name: str, value: str) -> None:
        """Creates a new secret.

        Args:
            name: Name of the secret.
            value: Value of the secret.
        """
        self.client.post(SECRETS_ENDPOINT, {'name': name, 'value': value})

    def delete_secret(self, secret_name: str, force: bool = False) -> None:
        """Deletes a secret.

        Args:
            secret_name: Name of the secret to delete.
            force: Whether to force delete even if secret is in use.
        """
        self.client.delete(
            f'{SECRETS_ENDPOINT}/{secret_name}', params={'force': str(force).lower()}
        )

    def get_registry_credentials(self) -> list[RegistryCredential]:
        """Retrieves all registry credentials.

        Returns:
            list[RegistryCredential]: List of all registry credentials.
        """
        response = self.client.get(CONTAINER_REGISTRY_CREDENTIALS_ENDPOINT)
        return [RegistryCredential.from_dict(credential) for credential in response.json()]

    def add_registry_credentials(self, credentials: BaseRegistryCredentials) -> None:
        """Adds new registry credentials.

        Args:
            credentials: Registry credentials to add.
        """
        data = credentials.to_dict()
        self.client.post(CONTAINER_REGISTRY_CREDENTIALS_ENDPOINT, data)

    def delete_registry_credentials(self, credentials_name: str) -> None:
        """Deletes registry credentials.

        Args:
            credentials_name: Name of the credentials to delete.
        """
        self.client.delete(f'{CONTAINER_REGISTRY_CREDENTIALS_ENDPOINT}/{credentials_name}')

    def get_fileset_secrets(self) -> list[Secret]:
        """Retrieves all fileset secrets.

        Returns:
           List of all fileset secrets.
        """
        response = self.client.get(FILESET_SECRETS_ENDPOINT)
        return [Secret.from_dict(secret) for secret in response.json()]

    def delete_fileset_secret(self, secret_name: str) -> None:
        """Deletes a fileset secret.

        Args:
            secret_name: Name of the secret to delete.
        """
        self.client.delete(f'{FILESET_SECRETS_ENDPOINT}/{secret_name}')

    def create_fileset_secret_from_file_paths(
        self, secret_name: str, file_paths: list[str]
    ) -> None:
        """Creates a new fileset secret.

        A fileset secret is a secret that contains several files,
        and can be used to mount a directory with the files in a container.

        Args:
            secret_name: Name of the secret.
            file_paths: List of file paths to include in the secret.
        """
        processed_files = []
        for file_path in file_paths:
            with open(file_path, 'rb') as f:
                base64_content = base64.b64encode(f.read()).decode('utf-8')
                processed_files.append(
                    {
                        'file_name': os.path.basename(file_path),
                        'base64_content': base64_content,
                    }
                )
        self.client.post(FILESET_SECRETS_ENDPOINT, {'name': secret_name, 'files': processed_files})
