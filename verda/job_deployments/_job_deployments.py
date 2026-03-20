"""Serverless job deployment service for Verda."""

from dataclasses import dataclass, field
from enum import Enum

from dataclasses_json import Undefined, dataclass_json

from verda.containers import ComputeResource, Container, ContainerRegistrySettings
from verda.helpers import strip_none_values
from verda.http_client import HTTPClient

JOB_DEPLOYMENTS_ENDPOINT = '/job-deployments'


class JobDeploymentStatus(str, Enum):
    """Possible states of a job deployment."""

    PAUSED = 'paused'
    TERMINATING = 'terminating'
    RUNNING = 'running'


@dataclass_json
@dataclass
class JobScalingOptions:
    """Scaling configuration for a job deployment."""

    max_replica_count: int
    queue_message_ttl_seconds: int
    deadline_seconds: int


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class JobDeploymentSummary:
    """Short job deployment information returned by the list endpoint."""

    name: str
    created_at: str
    compute: ComputeResource


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class JobDeployment:
    """Configuration and metadata for a serverless job deployment."""

    name: str
    containers: list[Container]
    compute: ComputeResource
    scaling: JobScalingOptions | None = None
    container_registry_settings: ContainerRegistrySettings = field(
        default_factory=lambda: ContainerRegistrySettings(is_private=False)
    )
    endpoint_base_url: str | None = None
    created_at: str | None = None


class JobDeploymentsService:
    """Service for managing serverless job deployments."""

    def __init__(self, http_client: HTTPClient) -> None:
        self._http_client = http_client

    def get(self) -> list[JobDeploymentSummary]:
        """Return all job deployments."""
        response = self._http_client.get(JOB_DEPLOYMENTS_ENDPOINT)
        return [JobDeploymentSummary.from_dict(job) for job in response.json()]

    def get_by_name(self, job_name: str) -> JobDeployment:
        """Return a job deployment by name."""
        response = self._http_client.get(f'{JOB_DEPLOYMENTS_ENDPOINT}/{job_name}')
        return JobDeployment.from_dict(response.json(), infer_missing=True)

    def create(self, deployment: JobDeployment) -> JobDeployment:
        """Create a new job deployment."""
        response = self._http_client.post(
            JOB_DEPLOYMENTS_ENDPOINT,
            json=strip_none_values(deployment.to_dict()),
        )
        return JobDeployment.from_dict(response.json(), infer_missing=True)

    def update(self, job_name: str, deployment: JobDeployment) -> JobDeployment:
        """Update an existing job deployment."""
        response = self._http_client.patch(
            f'{JOB_DEPLOYMENTS_ENDPOINT}/{job_name}',
            json=strip_none_values(deployment.to_dict()),
        )
        return JobDeployment.from_dict(response.json(), infer_missing=True)

    def delete(self, job_name: str, timeout: float | None = None) -> None:
        """Delete a job deployment."""
        params = {'timeout': timeout} if timeout is not None else None
        self._http_client.delete(f'{JOB_DEPLOYMENTS_ENDPOINT}/{job_name}', params=params)

    def get_status(self, job_name: str) -> JobDeploymentStatus:
        """Return the current status for a job deployment."""
        response = self._http_client.get(f'{JOB_DEPLOYMENTS_ENDPOINT}/{job_name}/status')
        return JobDeploymentStatus(response.json()['status'])

    def get_scaling_options(self, job_name: str) -> JobScalingOptions:
        """Return scaling options for a job deployment."""
        response = self._http_client.get(f'{JOB_DEPLOYMENTS_ENDPOINT}/{job_name}/scaling')
        return JobScalingOptions.from_dict(response.json())

    def pause(self, job_name: str) -> None:
        """Pause a job deployment."""
        self._http_client.post(f'{JOB_DEPLOYMENTS_ENDPOINT}/{job_name}/pause')

    def resume(self, job_name: str) -> None:
        """Resume a job deployment."""
        self._http_client.post(f'{JOB_DEPLOYMENTS_ENDPOINT}/{job_name}/resume')

    def purge_queue(self, job_name: str) -> None:
        """Purge the job deployment queue."""
        self._http_client.post(f'{JOB_DEPLOYMENTS_ENDPOINT}/{job_name}/purge-queue')
