import json

import pytest
import responses  # https://github.com/getsentry/responses

from verda.containers import ComputeResource, Container, ContainerRegistrySettings
from verda.exceptions import APIException
from verda.job_deployments import (
    JobDeployment,
    JobDeploymentsService,
    JobDeploymentStatus,
    JobDeploymentSummary,
    JobScalingOptions,
)

JOB_NAME = 'test-job'
CONTAINER_NAME = 'worker'
INVALID_REQUEST = 'INVALID_REQUEST'
INVALID_REQUEST_MESSAGE = 'Invalid request'

JOB_SUMMARY_PAYLOAD = [
    {
        'name': JOB_NAME,
        'created_at': '2024-01-01T00:00:00Z',
        'compute': {
            'name': 'H100',
            'size': 1,
        },
    }
]

JOB_PAYLOAD = {
    'name': JOB_NAME,
    'containers': [
        {
            'name': CONTAINER_NAME,
            'image': 'busybox:latest',
            'exposed_port': 8080,
            'env': [],
            'volume_mounts': [],
        }
    ],
    'endpoint_base_url': 'https://test-job.datacrunch.io',
    'created_at': '2024-01-01T00:00:00Z',
    'compute': {
        'name': 'H100',
        'size': 1,
    },
    'container_registry_settings': {
        'is_private': False,
        'credentials': None,
    },
}

SCALING_PAYLOAD = {
    'max_replica_count': 5,
    'queue_message_ttl_seconds': 600,
    'deadline_seconds': 1800,
}


class TestJobDeploymentsService:
    @pytest.fixture
    def service(self, http_client):
        return JobDeploymentsService(http_client)

    @pytest.fixture
    def endpoint(self, http_client):
        return http_client._base_url + '/job-deployments'

    @responses.activate
    def test_get_job_deployments(self, service, endpoint):
        responses.add(responses.GET, endpoint, json=JOB_SUMMARY_PAYLOAD, status=200)

        deployments = service.get()

        assert isinstance(deployments, list)
        assert len(deployments) == 1
        assert isinstance(deployments[0], JobDeploymentSummary)
        assert deployments[0].name == JOB_NAME
        assert deployments[0].compute.name == 'H100'
        assert responses.assert_call_count(endpoint, 1) is True

    @responses.activate
    def test_get_job_deployment_by_name(self, service, endpoint):
        url = f'{endpoint}/{JOB_NAME}'
        responses.add(responses.GET, url, json=JOB_PAYLOAD, status=200)

        deployment = service.get_by_name(JOB_NAME)

        assert isinstance(deployment, JobDeployment)
        assert deployment.name == JOB_NAME
        assert deployment.endpoint_base_url == 'https://test-job.datacrunch.io'
        assert deployment.compute.size == 1
        assert deployment.containers[0].name == CONTAINER_NAME
        assert responses.assert_call_count(url, 1) is True

    @responses.activate
    def test_get_job_deployment_by_name_error(self, service, endpoint):
        url = f'{endpoint}/missing-job'
        responses.add(
            responses.GET,
            url,
            json={'code': INVALID_REQUEST, 'message': INVALID_REQUEST_MESSAGE},
            status=400,
        )

        with pytest.raises(APIException) as excinfo:
            service.get_by_name('missing-job')

        assert excinfo.value.code == INVALID_REQUEST
        assert excinfo.value.message == INVALID_REQUEST_MESSAGE
        assert responses.assert_call_count(url, 1) is True

    @responses.activate
    def test_create_job_deployment(self, service, endpoint):
        responses.add(responses.POST, endpoint, json=JOB_PAYLOAD, status=201)

        deployment = JobDeployment(
            name=JOB_NAME,
            containers=[Container(image='busybox:latest', exposed_port=8080, name=CONTAINER_NAME)],
            compute=ComputeResource(name='H100', size=1),
            container_registry_settings=ContainerRegistrySettings(is_private=False),
            scaling=JobScalingOptions(**SCALING_PAYLOAD),
        )

        created = service.create(deployment)

        assert isinstance(created, JobDeployment)
        assert created.name == JOB_NAME
        request_body = json.loads(responses.calls[0].request.body.decode('utf-8'))
        assert request_body['scaling'] == SCALING_PAYLOAD
        assert responses.assert_call_count(endpoint, 1) is True

    @responses.activate
    def test_update_job_deployment(self, service, endpoint):
        url = f'{endpoint}/{JOB_NAME}'
        responses.add(responses.PATCH, url, json=JOB_PAYLOAD, status=200)

        deployment = JobDeployment(
            name=JOB_NAME,
            containers=[Container(image='busybox:latest', exposed_port=8080, name=CONTAINER_NAME)],
            compute=ComputeResource(name='H100', size=1),
            scaling=JobScalingOptions(**SCALING_PAYLOAD),
        )

        updated = service.update(JOB_NAME, deployment)

        assert isinstance(updated, JobDeployment)
        assert updated.name == JOB_NAME
        assert responses.assert_call_count(url, 1) is True

    @responses.activate
    def test_delete_job_deployment(self, service, endpoint):
        url = f'{endpoint}/{JOB_NAME}?timeout=120000'
        responses.add(responses.DELETE, url, status=200)

        service.delete(JOB_NAME, timeout=120000)

        assert responses.assert_call_count(url, 1) is True

    @responses.activate
    def test_get_job_status(self, service, endpoint):
        url = f'{endpoint}/{JOB_NAME}/status'
        responses.add(responses.GET, url, json={'status': 'running'}, status=200)

        status = service.get_status(JOB_NAME)

        assert status == JobDeploymentStatus.RUNNING
        assert responses.assert_call_count(url, 1) is True

    @responses.activate
    def test_get_job_scaling_options(self, service, endpoint):
        url = f'{endpoint}/{JOB_NAME}/scaling'
        responses.add(responses.GET, url, json=SCALING_PAYLOAD, status=200)

        scaling = service.get_scaling_options(JOB_NAME)

        assert isinstance(scaling, JobScalingOptions)
        assert scaling.max_replica_count == 5
        assert scaling.deadline_seconds == 1800
        assert responses.assert_call_count(url, 1) is True

    @responses.activate
    def test_pause_job_deployment(self, service, endpoint):
        url = f'{endpoint}/{JOB_NAME}/pause'
        responses.add(responses.POST, url, status=204)

        service.pause(JOB_NAME)

        assert responses.assert_call_count(url, 1) is True

    @responses.activate
    def test_resume_job_deployment(self, service, endpoint):
        url = f'{endpoint}/{JOB_NAME}/resume'
        responses.add(responses.POST, url, status=204)

        service.resume(JOB_NAME)

        assert responses.assert_call_count(url, 1) is True

    @responses.activate
    def test_purge_job_deployment_queue(self, service, endpoint):
        url = f'{endpoint}/{JOB_NAME}/purge-queue'
        responses.add(responses.POST, url, status=204)

        service.purge_queue(JOB_NAME)

        assert responses.assert_call_count(url, 1) is True
