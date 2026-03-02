import pytest
import responses  # https://github.com/getsentry/responses
from responses import matchers

from verda.containers import (
    AWSECRCredentials,
    ComputeResource,
    Container,
    ContainerDeploymentStatus,
    ContainerRegistrySettings,
    ContainersService,
    CustomRegistryCredentials,
    Deployment,
    DockerHubCredentials,
    EntrypointOverridesSettings,
    EnvVar,
    EnvVarType,
    GCRCredentials,
    GithubCredentials,
    HealthcheckSettings,
    QueueLoadScalingTrigger,
    RegistryCredential,
    ReplicaInfo,
    ScalingOptions,
    ScalingPolicy,
    ScalingTriggers,
    Secret,
    UtilizationScalingTrigger,
    VolumeMount,
    VolumeMountType,
)
from verda.containers._containers import (
    CONTAINER_DEPLOYMENTS_ENDPOINT,
    CONTAINER_REGISTRY_CREDENTIALS_ENDPOINT,
    SECRETS_ENDPOINT,
    SERVERLESS_COMPUTE_RESOURCES_ENDPOINT,
)
from verda.exceptions import APIException

DEPLOYMENT_NAME = 'test-deployment'
CONTAINER_NAME = 'test-container'
COMPUTE_RESOURCE_NAME_GENERAL_COMPUTE = 'General Compute'
COMPUTE_RESOURCE_NAME_H100 = 'H100'
SECRET_NAME = 'test-secret'
SECRET_VALUE = 'test-secret-value'
REGISTRY_CREDENTIAL_NAME = 'test-credential'
ENV_VAR_NAME = 'TEST_VAR'
ENV_VAR_VALUE = 'test-value'

INVALID_REQUEST = 'INVALID_REQUEST'
INVALID_REQUEST_MESSAGE = 'Invalid request'

# Sample deployment data for testing
DEPLOYMENT_DATA = {
    'name': DEPLOYMENT_NAME,
    'container_registry_settings': {'is_private': False},
    'containers': [
        {
            'name': CONTAINER_NAME,
            'image': 'nginx:latest',
            'exposed_port': 80,
            'healthcheck': {'enabled': True, 'port': 80, 'path': '/health'},
            'entrypoint_overrides': {'enabled': False},
            'env': [
                {
                    'name': 'ENV_VAR1',
                    'value_or_reference_to_secret': 'value1',
                    'type': 'plain',
                }
            ],
            'volume_mounts': [{'type': 'scratch', 'mount_path': '/data'}],
        }
    ],
    'compute': {
        'name': COMPUTE_RESOURCE_NAME_GENERAL_COMPUTE,
        'size': 1,
        'is_available': True,
    },
    'is_spot': False,
    'endpoint_base_url': 'https://test-deployment.datacrunch.io',
    'scaling': {
        'min_replica_count': 1,
        'max_replica_count': 3,
        'scale_down_policy': {'delay_seconds': 300},
        'scale_up_policy': {'delay_seconds': 60},
        'queue_message_ttl_seconds': 3600,
        'concurrent_requests_per_replica': 10,
        'scaling_triggers': {
            'queue_load': {'threshold': 0.75},
            'cpu_utilization': {'enabled': True, 'threshold': 0.8},
            'gpu_utilization': {'enabled': False},
        },
    },
    'created_at': '2023-01-01T00:00:00+00:00',
}

# Sample compute resources data
COMPUTE_RESOURCES_DATA = [
    {'name': COMPUTE_RESOURCE_NAME_GENERAL_COMPUTE, 'size': 1, 'is_available': True},
    {'name': COMPUTE_RESOURCE_NAME_H100, 'size': 4, 'is_available': True},
]

# Sample secrets data
SECRETS_DATA = [
    {
        'name': SECRET_NAME,
        'created_at': '2023-01-01T00:00:00+00:00',
        'secret_type': 'generic',
    }
]

# Sample registry credentials data
REGISTRY_CREDENTIALS_DATA = [
    {'name': REGISTRY_CREDENTIAL_NAME, 'created_at': '2023-01-01T00:00:00+00:00'}
]

# Sample deployment status data
DEPLOYMENT_STATUS_DATA = {'status': 'healthy'}

# Sample replicas data
REPLICAS_DATA = {
    'list': [
        {
            'id': 'replica-1',
            'status': 'running',
            'started_at': '2023-01-01T00:00:00+00:00',
        }
    ]
}


# Sample environment variables data
ENV_VARS_DATA = [
    {
        'container_name': CONTAINER_NAME,
        'env': [
            {
                'name': ENV_VAR_NAME,
                'value_or_reference_to_secret': ENV_VAR_VALUE,
                'type': 'plain',
            }
        ],
    }
]


class TestContainersService:
    @pytest.fixture
    def containers_service(self, http_client):
        return ContainersService(http_client)

    @pytest.fixture
    def deployments_endpoint(self, http_client):
        return http_client._base_url + CONTAINER_DEPLOYMENTS_ENDPOINT

    @pytest.fixture
    def compute_resources_endpoint(self, http_client):
        return http_client._base_url + SERVERLESS_COMPUTE_RESOURCES_ENDPOINT

    @pytest.fixture
    def secrets_endpoint(self, http_client):
        return http_client._base_url + SECRETS_ENDPOINT

    @pytest.fixture
    def registry_credentials_endpoint(self, http_client):
        return http_client._base_url + CONTAINER_REGISTRY_CREDENTIALS_ENDPOINT

    @responses.activate
    def test_get_deployments(self, containers_service, deployments_endpoint):
        # arrange - add response mock
        responses.add(responses.GET, deployments_endpoint, json=[DEPLOYMENT_DATA], status=200)

        # act
        deployments = containers_service.get_deployments()
        deployment = deployments[0]

        # assert
        assert isinstance(deployments, list)
        assert len(deployments) == 1
        assert isinstance(deployment, Deployment)
        assert deployment.name == DEPLOYMENT_NAME
        assert len(deployment.containers) == 1
        assert isinstance(deployment.containers[0], Container)
        assert isinstance(deployment.compute, ComputeResource)
        assert deployment.compute.name == COMPUTE_RESOURCE_NAME_GENERAL_COMPUTE
        assert responses.assert_call_count(deployments_endpoint, 1) is True

    @responses.activate
    def test_get_deployment_by_name(self, containers_service, deployments_endpoint):
        # arrange - add response mock
        url = f'{deployments_endpoint}/{DEPLOYMENT_NAME}'
        responses.add(responses.GET, url, json=DEPLOYMENT_DATA, status=200)

        # act
        deployment = containers_service.get_deployment_by_name(DEPLOYMENT_NAME)

        # assert
        assert isinstance(deployment, Deployment)
        assert deployment.name == DEPLOYMENT_NAME
        assert len(deployment.containers) == 1
        assert deployment.containers[0].name == CONTAINER_NAME
        assert deployment.compute.name == COMPUTE_RESOURCE_NAME_GENERAL_COMPUTE
        assert responses.assert_call_count(url, 1) is True

    @responses.activate
    def test_get_deployment_by_name_error(self, containers_service, deployments_endpoint):
        # arrange - add response mock
        url = f'{deployments_endpoint}/nonexistent'
        responses.add(
            responses.GET,
            url,
            json={'code': INVALID_REQUEST, 'message': INVALID_REQUEST_MESSAGE},
            status=400,
        )

        # act
        with pytest.raises(APIException) as excinfo:
            containers_service.get_deployment_by_name('nonexistent')

        # assert
        assert excinfo.value.code == INVALID_REQUEST
        assert excinfo.value.message == INVALID_REQUEST_MESSAGE
        assert responses.assert_call_count(url, 1) is True

    @responses.activate
    def test_create_deployment(self, containers_service, deployments_endpoint):
        # arrange - add response mock
        responses.add(responses.POST, deployments_endpoint, json=DEPLOYMENT_DATA, status=200)

        container = Container(
            image='nginx:latest',
            exposed_port=80,
            healthcheck=HealthcheckSettings(enabled=True, port=80, path='/health'),
            entrypoint_overrides=EntrypointOverridesSettings(enabled=False),
            env=[
                EnvVar(
                    name='ENV_VAR1',
                    value_or_reference_to_secret='value1',
                    type=EnvVarType.PLAIN,
                )
            ],
            volume_mounts=[VolumeMount(type=VolumeMountType.SCRATCH, mount_path='/data')],
        )

        compute = ComputeResource(name=COMPUTE_RESOURCE_NAME_GENERAL_COMPUTE, size=1)

        container_registry_settings = ContainerRegistrySettings(is_private=False)

        # create deployment object
        deployment = Deployment(
            name=DEPLOYMENT_NAME,
            container_registry_settings=container_registry_settings,
            containers=[container],
            compute=compute,
            is_spot=False,
        )

        # act
        created_deployment = containers_service.create_deployment(deployment)

        # assert
        assert isinstance(created_deployment, Deployment)
        assert created_deployment.name == DEPLOYMENT_NAME
        assert len(created_deployment.containers) == 1
        assert created_deployment.containers[0].name == CONTAINER_NAME
        assert created_deployment.compute.name == COMPUTE_RESOURCE_NAME_GENERAL_COMPUTE
        assert responses.assert_call_count(deployments_endpoint, 1) is True

    @responses.activate
    def test_update_deployment(self, containers_service, deployments_endpoint):
        # arrange - add response mock
        url = f'{deployments_endpoint}/{DEPLOYMENT_NAME}'
        responses.add(responses.PATCH, url, json=DEPLOYMENT_DATA, status=200)

        # create deployment object
        container = Container(name=CONTAINER_NAME, image='nginx:latest', exposed_port=80)

        container_registry_settings = ContainerRegistrySettings(is_private=False)

        compute = ComputeResource(name=COMPUTE_RESOURCE_NAME_GENERAL_COMPUTE, size=1)

        deployment = Deployment(
            name=DEPLOYMENT_NAME,
            container_registry_settings=container_registry_settings,
            containers=[container],
            compute=compute,
        )

        # act
        updated_deployment = containers_service.update_deployment(DEPLOYMENT_NAME, deployment)

        # assert
        assert isinstance(updated_deployment, Deployment)
        assert updated_deployment.name == DEPLOYMENT_NAME
        assert len(updated_deployment.containers) == 1
        assert updated_deployment.containers[0].name == CONTAINER_NAME
        assert updated_deployment.compute.name == COMPUTE_RESOURCE_NAME_GENERAL_COMPUTE
        assert responses.assert_call_count(url, 1) is True

    @responses.activate
    def test_delete_deployment(self, containers_service, deployments_endpoint):
        # arrange - add response mock
        url = f'{deployments_endpoint}/{DEPLOYMENT_NAME}'
        responses.add(responses.DELETE, url, status=204)

        # act
        containers_service.delete_deployment(DEPLOYMENT_NAME)

        # assert
        assert responses.assert_call_count(url, 1) is True

    @responses.activate
    def test_get_deployment_status(self, containers_service, deployments_endpoint):
        # arrange - add response mock
        url = f'{deployments_endpoint}/{DEPLOYMENT_NAME}/status'
        responses.add(responses.GET, url, json=DEPLOYMENT_STATUS_DATA, status=200)

        # act
        status = containers_service.get_deployment_status(DEPLOYMENT_NAME)

        # assert
        assert status == ContainerDeploymentStatus.HEALTHY
        assert responses.assert_call_count(url, 1) is True

    @responses.activate
    def test_restart_deployment(self, containers_service, deployments_endpoint):
        # arrange - add response mock
        url = f'{deployments_endpoint}/{DEPLOYMENT_NAME}/restart'
        responses.add(responses.POST, url, status=204)

        # act
        containers_service.restart_deployment(DEPLOYMENT_NAME)

        # assert
        assert responses.assert_call_count(url, 1) is True

    @responses.activate
    def test_get_deployment_scaling_options(self, containers_service, deployments_endpoint):
        # arrange - add response mock
        url = f'{deployments_endpoint}/{DEPLOYMENT_NAME}/scaling'
        responses.add(responses.GET, url, json=DEPLOYMENT_DATA['scaling'], status=200)

        # act
        scaling_options = containers_service.get_deployment_scaling_options(DEPLOYMENT_NAME)

        # assert
        assert isinstance(scaling_options, ScalingOptions)
        assert scaling_options.min_replica_count == 1
        assert scaling_options.max_replica_count == 3
        assert responses.assert_call_count(url, 1) is True

    @responses.activate
    def test_update_deployment_scaling_options(self, containers_service, deployments_endpoint):
        # arrange - add response mock
        url = f'{deployments_endpoint}/{DEPLOYMENT_NAME}/scaling'
        responses.add(responses.PATCH, url, json=DEPLOYMENT_DATA['scaling'], status=200)

        # create scaling options object
        scaling_options = ScalingOptions(
            min_replica_count=1,
            max_replica_count=5,
            scale_down_policy=ScalingPolicy(delay_seconds=300),
            scale_up_policy=ScalingPolicy(delay_seconds=60),
            queue_message_ttl_seconds=3600,
            concurrent_requests_per_replica=10,
            scaling_triggers=ScalingTriggers(
                queue_load=QueueLoadScalingTrigger(threshold=0.75),
                cpu_utilization=UtilizationScalingTrigger(enabled=True, threshold=0.8),
                gpu_utilization=UtilizationScalingTrigger(enabled=False),
            ),
        )

        # act
        updated_scaling = containers_service.update_deployment_scaling_options(
            DEPLOYMENT_NAME, scaling_options
        )

        # assert
        assert isinstance(updated_scaling, ScalingOptions)
        assert updated_scaling.min_replica_count == 1
        assert updated_scaling.max_replica_count == 3
        assert responses.assert_call_count(url, 1) is True

    @responses.activate
    def test_get_deployment_replicas(self, containers_service, deployments_endpoint):
        # arrange - add response mock
        url = f'{deployments_endpoint}/{DEPLOYMENT_NAME}/replicas'
        responses.add(responses.GET, url, json=REPLICAS_DATA, status=200)

        # act
        replicas = containers_service.get_deployment_replicas(DEPLOYMENT_NAME)

        # assert
        assert len(replicas) == 1
        assert replicas[0] == ReplicaInfo('replica-1', 'running', '2023-01-01T00:00:00+00:00')
        assert responses.assert_call_count(url, 1) is True

    @responses.activate
    def test_purge_deployment_queue(self, containers_service, deployments_endpoint):
        # arrange - add response mock
        url = f'{deployments_endpoint}/{DEPLOYMENT_NAME}/purge-queue'
        responses.add(responses.POST, url, status=204)

        # act
        containers_service.purge_deployment_queue(DEPLOYMENT_NAME)

        # assert
        assert responses.assert_call_count(url, 1) is True

    @responses.activate
    def test_pause_deployment(self, containers_service, deployments_endpoint):
        # arrange - add response mock
        url = f'{deployments_endpoint}/{DEPLOYMENT_NAME}/pause'
        responses.add(responses.POST, url, status=204)

        # act
        containers_service.pause_deployment(DEPLOYMENT_NAME)

        # assert
        assert responses.assert_call_count(url, 1) is True

    @responses.activate
    def test_resume_deployment(self, containers_service, deployments_endpoint):
        # arrange - add response mock
        url = f'{deployments_endpoint}/{DEPLOYMENT_NAME}/resume'
        responses.add(responses.POST, url, status=204)

        # act
        containers_service.resume_deployment(DEPLOYMENT_NAME)

        # assert
        assert responses.assert_call_count(url, 1) is True

    @responses.activate
    def test_get_deployment_environment_variables(self, containers_service, deployments_endpoint):
        # arrange - add response mock
        url = f'{deployments_endpoint}/{DEPLOYMENT_NAME}/environment-variables'
        responses.add(responses.GET, url, json=ENV_VARS_DATA, status=200)

        # act
        env_vars = containers_service.get_deployment_environment_variables(DEPLOYMENT_NAME)

        # assert
        assert env_vars[CONTAINER_NAME] == [
            EnvVar(
                name=ENV_VAR_NAME,
                value_or_reference_to_secret=ENV_VAR_VALUE,
                type=EnvVarType.PLAIN,
            )
        ]
        assert responses.assert_call_count(url, 1) is True

    @responses.activate
    def test_add_deployment_environment_variables(self, containers_service, deployments_endpoint):
        # arrange - add response mock
        url = f'{deployments_endpoint}/{DEPLOYMENT_NAME}/environment-variables'
        responses.add(responses.POST, url, json=ENV_VARS_DATA, status=200)

        # act
        env_vars = [
            EnvVar(
                name=ENV_VAR_NAME,
                value_or_reference_to_secret=ENV_VAR_VALUE,
                type=EnvVarType.PLAIN,
            )
        ]
        result = containers_service.add_deployment_environment_variables(
            DEPLOYMENT_NAME, CONTAINER_NAME, env_vars
        )

        # assert
        assert result[CONTAINER_NAME] == [
            EnvVar(
                name=ENV_VAR_NAME,
                value_or_reference_to_secret=ENV_VAR_VALUE,
                type=EnvVarType.PLAIN,
            )
        ]
        assert responses.assert_call_count(url, 1) is True

    @responses.activate
    def test_update_deployment_environment_variables(
        self, containers_service, deployments_endpoint
    ):
        # arrange - add response mock
        url = f'{deployments_endpoint}/{DEPLOYMENT_NAME}/environment-variables'
        responses.add(responses.PATCH, url, json=ENV_VARS_DATA[0], status=200)

        # act
        env_vars = [
            EnvVar(
                name=ENV_VAR_NAME,
                value_or_reference_to_secret=ENV_VAR_VALUE,
                type=EnvVarType.PLAIN,
            )
        ]
        result = containers_service.update_deployment_environment_variables(
            DEPLOYMENT_NAME, CONTAINER_NAME, env_vars
        )

        # assert
        assert result[CONTAINER_NAME] == [
            EnvVar(
                name=ENV_VAR_NAME,
                value_or_reference_to_secret=ENV_VAR_VALUE,
                type=EnvVarType.PLAIN,
            )
        ]
        assert responses.assert_call_count(url, 1) is True

    @responses.activate
    def test_delete_deployment_environment_variables(
        self, containers_service, deployments_endpoint
    ):
        # arrange - add response mock
        url = f'{deployments_endpoint}/{DEPLOYMENT_NAME}/environment-variables'
        responses.add(responses.DELETE, url, json=ENV_VARS_DATA, status=200)

        # act
        result = containers_service.delete_deployment_environment_variables(
            DEPLOYMENT_NAME, CONTAINER_NAME, ['random-env-var-name']
        )

        # assert
        assert result == {
            CONTAINER_NAME: [
                EnvVar(
                    name=ENV_VAR_NAME,
                    value_or_reference_to_secret=ENV_VAR_VALUE,
                    type=EnvVarType.PLAIN,
                )
            ]
        }
        assert responses.assert_call_count(url, 1) is True

    @responses.activate
    def test_get_compute_resources(self, containers_service, compute_resources_endpoint):
        # arrange - add response mock
        responses.add(
            responses.GET,
            compute_resources_endpoint,
            # Wrap in list to simulate resource groups
            json=COMPUTE_RESOURCES_DATA,
            status=200,
        )

        # act
        resources = containers_service.get_compute_resources()

        # assert
        assert isinstance(resources, list)
        assert len(resources) == 2
        assert isinstance(resources[0], ComputeResource)
        assert resources[0].name == COMPUTE_RESOURCE_NAME_GENERAL_COMPUTE
        assert resources[0].size == 1
        assert resources[0].is_available
        assert responses.assert_call_count(compute_resources_endpoint, 1) is True

    @responses.activate
    def test_get_compute_resources_filter_by_size(
        self, containers_service, compute_resources_endpoint
    ):
        # arrange - add response mock
        responses.add(
            responses.GET,
            compute_resources_endpoint,
            json=COMPUTE_RESOURCES_DATA,
            status=200,
        )

        # act
        resources = containers_service.get_compute_resources(size=4)

        # assert
        assert isinstance(resources, list)
        assert len(resources) == 1
        assert isinstance(resources[0], ComputeResource)
        assert resources[0].name == COMPUTE_RESOURCE_NAME_H100
        assert resources[0].size == 4
        assert resources[0].is_available
        assert responses.assert_call_count(compute_resources_endpoint, 1) is True

    @responses.activate
    def test_get_compute_resources_filter_by_availability(
        self, containers_service, compute_resources_endpoint
    ):
        # arrange - add response mock
        responses.add(
            responses.GET,
            compute_resources_endpoint,
            json=COMPUTE_RESOURCES_DATA,
            status=200,
        )

        # act
        resources = containers_service.get_compute_resources(is_available=True)

        # assert
        assert isinstance(resources, list)
        assert len(resources) == 2
        assert all(r.is_available for r in resources)
        assert responses.assert_call_count(compute_resources_endpoint, 1) is True

    @responses.activate
    def test_get_compute_resources_filter_by_size_and_availability(
        self, containers_service, compute_resources_endpoint
    ):
        # arrange - add response mock
        responses.add(
            responses.GET,
            compute_resources_endpoint,
            json=COMPUTE_RESOURCES_DATA,
            status=200,
        )

        # act
        resources = containers_service.get_compute_resources(size=1, is_available=True)

        # assert
        assert isinstance(resources, list)
        assert len(resources) == 1
        assert resources[0].name == COMPUTE_RESOURCE_NAME_GENERAL_COMPUTE
        assert resources[0].size == 1
        assert resources[0].is_available
        assert responses.assert_call_count(compute_resources_endpoint, 1) is True

    @responses.activate
    def test_get_secrets(self, containers_service, secrets_endpoint):
        # arrange - add response mock
        responses.add(responses.GET, secrets_endpoint, json=SECRETS_DATA, status=200)

        # act
        secrets = containers_service.get_secrets()

        # assert
        assert isinstance(secrets, list)
        assert len(secrets) == 1
        assert isinstance(secrets[0], Secret)
        assert secrets[0].name == SECRET_NAME
        assert responses.assert_call_count(secrets_endpoint, 1) is True

    @responses.activate
    def test_create_secret(self, containers_service, secrets_endpoint):
        # arrange - add response mock
        responses.add(
            responses.POST,
            secrets_endpoint,
            status=201,
            match=[
                matchers.json_params_matcher(
                    # The test will now fail if the request body doesn't match the expected JSON structure
                    {'name': SECRET_NAME, 'value': SECRET_VALUE}
                )
            ],
        )

        # act
        containers_service.create_secret(SECRET_NAME, SECRET_VALUE)

        # assert
        assert responses.assert_call_count(secrets_endpoint, 1) is True

    @responses.activate
    def test_delete_secret(self, containers_service, secrets_endpoint):
        # arrange - add response mock
        url = f'{secrets_endpoint}/{SECRET_NAME}?force=false'
        responses.add(responses.DELETE, url, status=200)

        # act
        containers_service.delete_secret(SECRET_NAME)

        # assert
        assert responses.assert_call_count(url, 1) is True
        request = responses.calls[0].request
        assert 'force=false' in request.url

    @responses.activate
    def test_delete_secret_with_force(self, containers_service, secrets_endpoint):
        # arrange
        url = f'{secrets_endpoint}/{SECRET_NAME}?force=true'
        responses.add(responses.DELETE, url, status=200)

        # act
        containers_service.delete_secret(SECRET_NAME, force=True)

        # assert
        assert responses.assert_call_count(url, 1) is True
        request = responses.calls[0].request
        assert 'force=true' in request.url

    @responses.activate
    def test_get_registry_credentials(self, containers_service, registry_credentials_endpoint):
        # arrange - add response mock
        responses.add(
            responses.GET,
            registry_credentials_endpoint,
            json=REGISTRY_CREDENTIALS_DATA,
            status=200,
        )

        # act
        credentials = containers_service.get_registry_credentials()

        # assert
        assert isinstance(credentials, list)
        assert len(credentials) == 1
        assert isinstance(credentials[0], RegistryCredential)
        assert credentials[0].name == REGISTRY_CREDENTIAL_NAME
        assert responses.assert_call_count(registry_credentials_endpoint, 1) is True

    @responses.activate
    def test_add_registry_credentials(self, containers_service, registry_credentials_endpoint):
        USERNAME = 'username'
        ACCESS_TOKEN = 'token'
        # arrange - add response mock
        responses.add(responses.POST, registry_credentials_endpoint, status=201)

        # act
        creds = DockerHubCredentials(
            name=REGISTRY_CREDENTIAL_NAME, username=USERNAME, access_token=ACCESS_TOKEN
        )
        containers_service.add_registry_credentials(creds)

        # assert
        assert responses.assert_call_count(registry_credentials_endpoint, 1) is True
        assert (
            responses.calls[0].request.body.decode('utf-8')
            == '{"name": "test-credential", "type": "dockerhub", "username": "username", "access_token": "token"}'
        )

    @responses.activate
    def test_add_registry_credentials_github(
        self, containers_service, registry_credentials_endpoint
    ):
        # arrange
        responses.add(responses.POST, registry_credentials_endpoint, status=201)

        # act
        creds = GithubCredentials(
            name=REGISTRY_CREDENTIAL_NAME,
            username='test-username',
            access_token='test-token',
        )
        containers_service.add_registry_credentials(creds)

        # assert
        assert responses.assert_call_count(registry_credentials_endpoint, 1) is True
        assert (
            responses.calls[0].request.body.decode('utf-8')
            == '{"name": "test-credential", "type": "ghcr", "username": "test-username", "access_token": "test-token"}'
        )

    @responses.activate
    def test_add_registry_credentials_gcr(self, containers_service, registry_credentials_endpoint):
        # arrange
        responses.add(responses.POST, registry_credentials_endpoint, status=201)

        # act
        service_account_key = '{"key": "value"}'
        creds = GCRCredentials(
            name=REGISTRY_CREDENTIAL_NAME, service_account_key=service_account_key
        )
        containers_service.add_registry_credentials(creds)

        # assert
        assert responses.assert_call_count(registry_credentials_endpoint, 1) is True
        assert (
            responses.calls[0].request.body.decode('utf-8')
            == '{"name": "test-credential", "type": "gcr", "service_account_key": "{\\"key\\": \\"value\\"}"}'
        )

    @responses.activate
    def test_add_registry_credentials_aws_ecr(
        self, containers_service, registry_credentials_endpoint
    ):
        # arrange
        responses.add(responses.POST, registry_credentials_endpoint, status=201)

        # act
        creds = AWSECRCredentials(
            name=REGISTRY_CREDENTIAL_NAME,
            access_key_id='test-key',
            secret_access_key='test-secret',
            region='us-west-2',
            ecr_repo='test.ecr.aws.com',
        )
        containers_service.add_registry_credentials(creds)

        # assert
        assert responses.assert_call_count(registry_credentials_endpoint, 1) is True
        assert (
            responses.calls[0].request.body.decode('utf-8')
            == '{"name": "test-credential", "type": "aws-ecr", "access_key_id": "test-key", "secret_access_key": "test-secret", "region": "us-west-2", "ecr_repo": "test.ecr.aws.com"}'
        )

    @responses.activate
    def test_add_registry_credentials_custom(
        self, containers_service, registry_credentials_endpoint
    ):
        # arrange
        responses.add(responses.POST, registry_credentials_endpoint, status=201)

        # act
        docker_config = '{"auths": {"registry.example.com": {"auth": "base64-encoded"}}}'
        creds = CustomRegistryCredentials(
            name=REGISTRY_CREDENTIAL_NAME, docker_config_json=docker_config
        )
        containers_service.add_registry_credentials(creds)

        # assert
        assert responses.assert_call_count(registry_credentials_endpoint, 1) is True
        assert (
            responses.calls[0].request.body.decode('utf-8')
            == '{"name": "test-credential", "type": "custom", "docker_config_json": "{\\"auths\\": {\\"registry.example.com\\": {\\"auth\\": \\"base64-encoded\\"}}}"}'
        )

    @responses.activate
    def test_delete_registry_credentials(self, containers_service, registry_credentials_endpoint):
        # arrange - add response mock
        url = f'{registry_credentials_endpoint}/{REGISTRY_CREDENTIAL_NAME}'
        responses.add(responses.DELETE, url, status=200)

        # act
        containers_service.delete_registry_credentials(REGISTRY_CREDENTIAL_NAME)

        # assert
        assert responses.assert_call_count(url, 1) is True
