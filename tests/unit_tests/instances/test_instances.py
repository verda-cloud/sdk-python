import copy
import json

import pytest
import responses

from verda.constants import Actions, ErrorCodes, InstanceStatus, Locations
from verda.exceptions import APIException
from verda.instances import Instance, InstancesService, OSVolume

INVALID_REQUEST = ErrorCodes.INVALID_REQUEST
INVALID_REQUEST_MESSAGE = 'Your existence is invalid'

INSTANCE_ID = 'deadc0de-a5d2-4972-ae4e-d429115d055b'
SSH_KEY_ID = '12345dc1-a5d2-4972-ae4e-d429115d055b'
OS_VOLUME_ID = '46fc0247-8f65-4d8a-ad73-852a8b3dc1d3'

INSTANCE_TYPE = '1V100.6V'
INSTANCE_IMAGE = 'ubuntu-24.04-cuda-12.8-open-docker'
INSTANCE_HOSTNAME = "I'll be your host for today"
INSTANCE_DESCRIPTION = 'hope you enjoy your GPU'
INSTANCE_STATUS = 'running'
INSTANCE_PRICE_PER_HOUR = 0.60
INSTANCE_LOCATION = Locations.FIN_01
INSTANCE_IP = '1.2.3.4'
INSTANCE_CREATED_AT = 'whatchalookingatboy?'
INSTANCE_OS_VOLUME = {'name': 'os volume', 'size': 50}

PAYLOAD = [
    {
        'created_at': INSTANCE_CREATED_AT,
        'status': INSTANCE_STATUS,
        'ip': INSTANCE_IP,
        'cpu': {'description': 'super-duper-cpu', 'number_of_cores': 6},
        'gpu': {'description': 'super-duper-gpu', 'number_of_gpus': 1},
        'memory': {'description': 'super-duper-memory', 'size_in_gigabytes': 32},
        'gpu_memory': {'description': 'super-duper-memory', 'size_in_gigabytes': 20},
        'storage': {'description': 'super-duper-storage', 'size_in_gigabytes': 320},
        'hostname': INSTANCE_HOSTNAME,
        'description': INSTANCE_DESCRIPTION,
        'location': INSTANCE_LOCATION,
        'price_per_hour': INSTANCE_PRICE_PER_HOUR,
        'instance_type': INSTANCE_TYPE,
        'image': INSTANCE_IMAGE,
        'id': INSTANCE_ID,
        'ssh_key_ids': [SSH_KEY_ID],
        'os_volume_id': OS_VOLUME_ID,
    }
]

PAYLOAD_SPOT = PAYLOAD
PAYLOAD_SPOT[0]['is_spot'] = True


class TestInstancesService:
    @pytest.fixture
    def instances_service(self, http_client):
        return InstancesService(http_client)

    @pytest.fixture
    def endpoint(self, http_client):
        return http_client._base_url + '/instances'

    def test_get_instances(self, instances_service, endpoint):
        # arrange - add response mock
        responses.add(responses.GET, endpoint, json=PAYLOAD, status=200)

        # act
        instances = instances_service.get()
        instance = instances[0]

        # assert
        assert isinstance(instances, list)
        assert len(instances) == 1
        assert isinstance(instance, Instance)
        assert isinstance(instance.ssh_key_ids, list)
        assert instance.id == INSTANCE_ID
        assert instance.ssh_key_ids == [SSH_KEY_ID]
        assert instance.status == INSTANCE_STATUS
        assert instance.image == INSTANCE_IMAGE
        assert instance.instance_type == INSTANCE_TYPE
        assert instance.price_per_hour == INSTANCE_PRICE_PER_HOUR
        assert instance.location == INSTANCE_LOCATION
        assert instance.description == INSTANCE_DESCRIPTION
        assert instance.hostname == INSTANCE_HOSTNAME
        assert instance.ip == INSTANCE_IP
        assert instance.created_at == INSTANCE_CREATED_AT
        assert isinstance(instance.cpu, dict)
        assert isinstance(instance.gpu, dict)
        assert isinstance(instance.memory, dict)
        assert isinstance(instance.storage, dict)
        assert responses.assert_call_count(endpoint, 1) is True

    def test_get_instances_by_status_successful(self, instances_service, endpoint):
        # arrange - add response mock
        url = endpoint + '?status=running'
        responses.add(responses.GET, url, json=PAYLOAD, status=200)

        # act
        instances = instances_service.get(status='running')
        instance = instances[0]

        # assert
        assert isinstance(instances, list)
        assert len(instances) == 1
        assert isinstance(instance, Instance)
        assert isinstance(instance.ssh_key_ids, list)
        assert instance.id == INSTANCE_ID
        assert instance.ssh_key_ids == [SSH_KEY_ID]
        assert instance.status == INSTANCE_STATUS
        assert instance.image == INSTANCE_IMAGE
        assert instance.instance_type == INSTANCE_TYPE
        assert instance.price_per_hour == INSTANCE_PRICE_PER_HOUR
        assert instance.location == INSTANCE_LOCATION
        assert instance.description == INSTANCE_DESCRIPTION
        assert instance.hostname == INSTANCE_HOSTNAME
        assert instance.ip == INSTANCE_IP
        assert instance.created_at == INSTANCE_CREATED_AT
        assert isinstance(instance.cpu, dict)
        assert isinstance(instance.gpu, dict)
        assert isinstance(instance.memory, dict)
        assert isinstance(instance.storage, dict)
        assert responses.assert_call_count(url, 1) is True

    def test_get_instances_by_status_failed(self, instances_service, endpoint):
        # arrange - add response mock
        url = endpoint + '?status=blabbering'
        responses.add(
            responses.GET,
            url,
            json={'code': INVALID_REQUEST, 'message': INVALID_REQUEST_MESSAGE},
            status=400,
        )

        # act
        with pytest.raises(APIException) as excinfo:
            instances_service.get(status='blabbering')

        # assert
        assert excinfo.value.code == INVALID_REQUEST
        assert excinfo.value.message == INVALID_REQUEST_MESSAGE
        assert responses.assert_call_count(url, 1) is True

    def test_get_instance_by_id_successful(self, instances_service, endpoint):
        # arrange - add response mock
        url = endpoint + '/' + INSTANCE_ID
        responses.add(responses.GET, url, json=PAYLOAD[0], status=200)

        # act
        instance = instances_service.get_by_id(INSTANCE_ID)

        # assert
        assert isinstance(instance, Instance)
        assert instance.id == INSTANCE_ID
        assert instance.ssh_key_ids == [SSH_KEY_ID]
        assert instance.status == INSTANCE_STATUS
        assert instance.image == INSTANCE_IMAGE
        assert instance.instance_type == INSTANCE_TYPE
        assert instance.price_per_hour == INSTANCE_PRICE_PER_HOUR
        assert instance.location == INSTANCE_LOCATION
        assert instance.description == INSTANCE_DESCRIPTION
        assert instance.hostname == INSTANCE_HOSTNAME
        assert instance.ip == INSTANCE_IP
        assert instance.created_at == INSTANCE_CREATED_AT
        assert isinstance(instance.cpu, dict)
        assert isinstance(instance.gpu, dict)
        assert isinstance(instance.memory, dict)
        assert isinstance(instance.storage, dict)
        assert responses.assert_call_count(url, 1) is True

    def test_get_instance_by_id_failed(self, instances_service, endpoint):
        # arrange - add response mock
        url = endpoint + '/x'
        responses.add(
            responses.GET,
            url,
            json={'code': INVALID_REQUEST, 'message': INVALID_REQUEST_MESSAGE},
            status=400,
        )

        # act
        with pytest.raises(APIException) as excinfo:
            instances_service.get_by_id('x')

        # assert
        assert excinfo.value.code == INVALID_REQUEST
        assert excinfo.value.message == INVALID_REQUEST_MESSAGE
        assert responses.assert_call_count(url, 1) is True

    def test_create_instance_successful(self, instances_service, endpoint):
        # arrange - add response mock
        # create instance
        responses.add(responses.POST, endpoint, body=INSTANCE_ID, status=200)
        # get instance by id
        url = endpoint + '/' + INSTANCE_ID
        responses.add(responses.GET, url, json=PAYLOAD[0], status=200)

        # act
        instance = instances_service.create(
            instance_type=INSTANCE_TYPE,
            image=INSTANCE_IMAGE,
            ssh_key_ids=[SSH_KEY_ID],
            hostname=INSTANCE_HOSTNAME,
            description=INSTANCE_DESCRIPTION,
            os_volume=INSTANCE_OS_VOLUME,
        )

        # assert
        assert isinstance(instance, Instance)
        assert instance.id == INSTANCE_ID
        assert instance.ssh_key_ids == [SSH_KEY_ID]
        assert instance.status == INSTANCE_STATUS
        assert instance.image == INSTANCE_IMAGE
        assert instance.instance_type == INSTANCE_TYPE
        assert instance.price_per_hour == INSTANCE_PRICE_PER_HOUR
        assert instance.location == INSTANCE_LOCATION
        assert instance.description == INSTANCE_DESCRIPTION
        assert instance.hostname == INSTANCE_HOSTNAME
        assert instance.ip == INSTANCE_IP
        assert instance.created_at == INSTANCE_CREATED_AT
        assert instance.os_volume_id == OS_VOLUME_ID
        assert isinstance(instance.cpu, dict)
        assert isinstance(instance.gpu, dict)
        assert isinstance(instance.memory, dict)
        assert isinstance(instance.gpu_memory, dict)
        assert isinstance(instance.storage, dict)
        assert responses.assert_call_count(endpoint, 1) is True
        assert responses.assert_call_count(url, 1) is True
        assert isinstance(instance.__str__(), str)

    def test_create_spot_instance_successful(self, instances_service, endpoint):
        # arrange - add response mock
        # add response mock for the create instance endpoint
        responses.add(responses.POST, endpoint, body=INSTANCE_ID, status=200)
        # add response mock for the get instance by id endpoint
        url = endpoint + '/' + INSTANCE_ID
        responses.add(responses.GET, url, json=PAYLOAD_SPOT[0], status=200)

        # act
        instance = instances_service.create(
            instance_type=INSTANCE_TYPE,
            image=INSTANCE_IMAGE,
            ssh_key_ids=[SSH_KEY_ID],
            hostname=INSTANCE_HOSTNAME,
            description=INSTANCE_DESCRIPTION,
            os_volume=INSTANCE_OS_VOLUME,
        )

        # assert
        assert isinstance(instance, Instance)
        assert instance.id == INSTANCE_ID
        assert instance.ssh_key_ids == [SSH_KEY_ID]
        assert instance.status == INSTANCE_STATUS
        assert instance.image == INSTANCE_IMAGE
        assert instance.instance_type == INSTANCE_TYPE
        assert instance.price_per_hour == INSTANCE_PRICE_PER_HOUR
        assert instance.location == INSTANCE_LOCATION
        assert instance.description == INSTANCE_DESCRIPTION
        assert instance.hostname == INSTANCE_HOSTNAME
        assert instance.ip == INSTANCE_IP
        assert instance.created_at == INSTANCE_CREATED_AT
        assert instance.os_volume_id == OS_VOLUME_ID
        assert instance.is_spot
        assert isinstance(instance.cpu, dict)
        assert isinstance(instance.gpu, dict)
        assert isinstance(instance.memory, dict)
        assert isinstance(instance.gpu_memory, dict)
        assert isinstance(instance.storage, dict)
        assert responses.assert_call_count(endpoint, 1) is True
        assert responses.assert_call_count(url, 1) is True

    def test_create_spot_instance_with_spot_volume_policy(self, instances_service, endpoint):
        # arrange
        responses.add(responses.POST, endpoint, body=INSTANCE_ID, status=200)
        url = endpoint + '/' + INSTANCE_ID
        responses.add(responses.GET, url, json=PAYLOAD[0], status=200)

        os_volume = OSVolume(
            name='spot-instance-os-volume', size=50, on_spot_discontinue='delete_permanently'
        )

        # act
        instances_service.create(
            instance_type=INSTANCE_TYPE,
            image=INSTANCE_IMAGE,
            ssh_key_ids=[SSH_KEY_ID],
            hostname=INSTANCE_HOSTNAME,
            description=INSTANCE_DESCRIPTION,
            os_volume=os_volume,
        )

        # assert
        request_body = responses.calls[0].request.body.decode('utf-8')
        body = json.loads(request_body)
        assert body['os_volume']['name'] == os_volume.name
        assert body['os_volume']['size'] == os_volume.size
        assert body['os_volume']['on_spot_discontinue'] == 'delete_permanently'

    def test_create_instance_attached_os_volume_successful(self, instances_service, endpoint):
        # arrange - add response mock
        # create instance
        responses.add(responses.POST, endpoint, body=INSTANCE_ID, status=200)
        # get instance by id
        url = endpoint + '/' + INSTANCE_ID
        responses.add(responses.GET, url, json=PAYLOAD[0], status=200)

        # act
        instance = instances_service.create(
            instance_type=INSTANCE_TYPE,
            image=OS_VOLUME_ID,
            hostname=INSTANCE_HOSTNAME,
            description=INSTANCE_DESCRIPTION,
        )

        # assert
        assert isinstance(instance, Instance)
        assert instance.id == INSTANCE_ID
        assert instance.ssh_key_ids == [SSH_KEY_ID]
        assert instance.status == INSTANCE_STATUS
        assert instance.image == INSTANCE_IMAGE
        assert instance.instance_type == INSTANCE_TYPE
        assert instance.price_per_hour == INSTANCE_PRICE_PER_HOUR
        assert instance.location == INSTANCE_LOCATION
        assert instance.description == INSTANCE_DESCRIPTION
        assert instance.hostname == INSTANCE_HOSTNAME
        assert instance.ip == INSTANCE_IP
        assert instance.created_at == INSTANCE_CREATED_AT
        assert instance.os_volume_id == OS_VOLUME_ID
        assert isinstance(instance.cpu, dict)
        assert isinstance(instance.gpu, dict)
        assert isinstance(instance.memory, dict)
        assert isinstance(instance.gpu_memory, dict)
        assert isinstance(instance.storage, dict)
        assert responses.assert_call_count(endpoint, 1) is True
        assert responses.assert_call_count(url, 1) is True

    @pytest.mark.parametrize(
        ('wait_for_status', 'expected_status', 'expected_get_instance_call_count'),
        [
            (None, InstanceStatus.ORDERED, 1),
            (InstanceStatus.ORDERED, InstanceStatus.ORDERED, 1),
            (InstanceStatus.PROVISIONING, InstanceStatus.PROVISIONING, 2),
            (lambda status: status != InstanceStatus.ORDERED, InstanceStatus.PROVISIONING, 2),
            (InstanceStatus.RUNNING, InstanceStatus.RUNNING, 3),
        ],
    )
    def test_create_wait_for_status(
        self,
        instances_service,
        endpoint,
        wait_for_status,
        expected_status,
        expected_get_instance_call_count,
    ):
        # arrange - add response mock
        # create instance
        responses.add(responses.POST, endpoint, body=INSTANCE_ID, status=200)
        # First get instance by id - ordered
        get_instance_url = endpoint + '/' + INSTANCE_ID
        payload = copy.deepcopy(PAYLOAD[0])
        payload['status'] = InstanceStatus.ORDERED
        responses.add(responses.GET, get_instance_url, json=payload, status=200)
        # Second get instance by id - provisioning
        payload = copy.deepcopy(PAYLOAD[0])
        payload['status'] = InstanceStatus.PROVISIONING
        responses.add(responses.GET, get_instance_url, json=payload, status=200)
        # Third get instance by id - running
        payload = copy.deepcopy(PAYLOAD[0])
        payload['status'] = InstanceStatus.RUNNING
        responses.add(responses.GET, get_instance_url, json=payload, status=200)

        # act
        instance = instances_service.create(
            instance_type=INSTANCE_TYPE,
            image=OS_VOLUME_ID,
            hostname=INSTANCE_HOSTNAME,
            description=INSTANCE_DESCRIPTION,
            wait_for_status=wait_for_status,
            max_interval=0,
            max_wait_time=1,
        )

        # assert
        assert isinstance(instance, Instance)
        assert instance.id == INSTANCE_ID
        assert instance.status == expected_status
        assert responses.assert_call_count(endpoint, 1) is True
        assert (
            responses.assert_call_count(get_instance_url, expected_get_instance_call_count) is True
        )

    def test_create_instance_failed(self, instances_service, endpoint):
        # arrange - add response mock
        responses.add(
            responses.POST,
            endpoint,
            json={'code': INVALID_REQUEST, 'message': INVALID_REQUEST_MESSAGE},
            status=400,
        )

        # act
        with pytest.raises(APIException) as excinfo:
            instances_service.create(
                instance_type=INSTANCE_TYPE,
                image=INSTANCE_IMAGE,
                ssh_key_ids=[SSH_KEY_ID],
                hostname=INSTANCE_HOSTNAME,
                description=INSTANCE_DESCRIPTION,
            )

        # assert
        assert excinfo.value.code == INVALID_REQUEST
        assert excinfo.value.message == INVALID_REQUEST_MESSAGE
        assert responses.assert_call_count(endpoint, 1) is True

    def test_action_successful(self, instances_service, endpoint):
        # arrange - add response mock
        url = endpoint
        responses.add(responses.PUT, url, status=202)

        # act
        result = instances_service.action(id_list=[INSTANCE_ID], action=Actions.SHUTDOWN)

        # assert
        assert result is None
        assert responses.assert_call_count(url, 1) is True

    def test_action_with_delete_permanently_sends_payload(self, instances_service, endpoint):
        # arrange
        url = endpoint
        responses.add(responses.PUT, url, status=202)
        volume_ids = [OS_VOLUME_ID]

        # act
        instances_service.action(
            id_list=[INSTANCE_ID],
            action=Actions.DELETE,
            volume_ids=volume_ids,
            delete_permanently=True,
        )

        # assert
        request_body = responses.calls[0].request.body.decode('utf-8')
        body = json.loads(request_body)
        assert body['id'] == [INSTANCE_ID]
        assert body['action'] == Actions.DELETE
        assert body['volume_ids'] == volume_ids
        assert body['delete_permanently'] is True

    def test_action_failed(self, instances_service, endpoint):
        # arrange - add response mock
        url = endpoint
        responses.add(
            responses.PUT,
            url,
            json={'code': INVALID_REQUEST, 'message': INVALID_REQUEST_MESSAGE},
            status=400,
        )

        # act
        with pytest.raises(APIException) as excinfo:
            instances_service.action(id_list=[INSTANCE_ID], action='fluxturcate')

        # assert
        assert excinfo.value.code == INVALID_REQUEST
        assert excinfo.value.message == INVALID_REQUEST_MESSAGE
        assert responses.assert_call_count(url, 1) is True

    def test_is_available_successful(self, instances_service):
        # arrange - add response mock
        url = (
            instances_service._http_client._base_url
            + '/instance-availability/'
            + INSTANCE_TYPE
            + '?isSpot=false'
        )
        responses.add(responses.GET, url, json=True, status=200)

        # act
        is_available = instances_service.is_available(INSTANCE_TYPE)

        # assert
        assert is_available is True
        assert responses.assert_call_count(url, 1) is True

    def test_is_spot_available_successful(self, instances_service):
        # arrange - add response mock
        url = (
            instances_service._http_client._base_url
            + '/instance-availability/'
            + INSTANCE_TYPE
            + '?isSpot=true'
        )
        responses.add(responses.GET, url, json=True, status=200)

        # act
        is_available = instances_service.is_available(INSTANCE_TYPE, is_spot=True)

        # assert
        assert is_available is True
        assert responses.assert_call_count(url, 1) is True

    def test_is_available_failed(self, instances_service):
        # arrange - add response mock
        url = (
            instances_service._http_client._base_url + '/instance-availability/x' + '?isSpot=false'
        )
        responses.add(
            responses.GET,
            url,
            json={'code': INVALID_REQUEST, 'message': INVALID_REQUEST_MESSAGE},
            status=400,
        )

        # act
        with pytest.raises(APIException) as excinfo:
            instances_service.is_available('x')

        # assert
        assert excinfo.value.code == INVALID_REQUEST
        assert excinfo.value.message == INVALID_REQUEST_MESSAGE
        assert responses.assert_call_count(url, 1) is True
