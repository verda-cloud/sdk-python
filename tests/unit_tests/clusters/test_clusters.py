import pytest
import responses  # https://github.com/getsentry/responses

from verda.clusters import Cluster, ClustersService, ClusterWorkerNode
from verda.constants import ErrorCodes, Locations
from verda.exceptions import APIException

INVALID_REQUEST = ErrorCodes.INVALID_REQUEST
INVALID_REQUEST_MESSAGE = 'Invalid request'

CLUSTER_ID = 'deadc0de-a5d2-4972-ae4e-d429115d055b'
SSH_KEY_ID = '12345dc1-a5d2-4972-ae4e-d429115d055b'

CLUSTER_HOSTNAME = 'test-cluster'
CLUSTER_DESCRIPTION = 'Test compute cluster'
CLUSTER_STATUS = 'running'
CLUSTER_CLUSTER_TYPE = '16H200'
CLUSTER_NODE_COUNT = 2
CLUSTER_LOCATION = Locations.FIN_03
CLUSTER_IMAGE = 'ubuntu-22.04-cuda-12.4-cluster'
CLUSTER_CREATED_AT = '2024-01-01T00:00:00Z'
CLUSTER_IP = '10.0.0.1'

NODE_1_ID = 'node1-c0de-a5d2-4972-ae4e-d429115d055b'
NODE_2_ID = 'node2-c0de-a5d2-4972-ae4e-d429115d055b'

NODES_PAYLOAD = [
    {
        'id': NODE_1_ID,
        'status': 'running',
        'hostname': 'test-cluster-node-1',
        'private_ip': '10.0.0.1',
    },
    {
        'id': NODE_2_ID,
        'status': 'running',
        'hostname': 'test-cluster-node-2',
        'private_ip': '10.0.0.2',
    },
]

CLUSTER_PAYLOAD = [
    {
        'id': CLUSTER_ID,
        'hostname': CLUSTER_HOSTNAME,
        'description': CLUSTER_DESCRIPTION,
        'status': CLUSTER_STATUS,
        'created_at': CLUSTER_CREATED_AT,
        'location': CLUSTER_LOCATION,
        'cluster_type': CLUSTER_CLUSTER_TYPE,
        'worker_nodes': NODES_PAYLOAD,
        'ssh_key_ids': [SSH_KEY_ID],
        'image': CLUSTER_IMAGE,
        'ip': CLUSTER_IP,
    }
]


class TestClustersService:
    @pytest.fixture
    def clusters_service(self, http_client):
        return ClustersService(http_client)

    @pytest.fixture
    def endpoint(self, http_client):
        return http_client._base_url + '/clusters'

    def test_get_clusters(self, clusters_service, endpoint):
        # arrange - add response mock
        responses.add(responses.GET, endpoint, json=CLUSTER_PAYLOAD, status=200)

        # act
        clusters = clusters_service.get()
        cluster = clusters[0]

        # assert
        assert isinstance(clusters, list)
        assert len(clusters) == 1
        assert isinstance(cluster, Cluster)
        assert cluster.id == CLUSTER_ID
        assert cluster.hostname == CLUSTER_HOSTNAME
        assert cluster.description == CLUSTER_DESCRIPTION
        assert cluster.status == CLUSTER_STATUS
        assert cluster.created_at == CLUSTER_CREATED_AT
        assert cluster.location == CLUSTER_LOCATION
        assert cluster.cluster_type == CLUSTER_CLUSTER_TYPE
        assert isinstance(cluster.worker_nodes, list)
        assert len(cluster.worker_nodes) == CLUSTER_NODE_COUNT
        assert isinstance(cluster.worker_nodes[0], ClusterWorkerNode)
        assert cluster.ssh_key_ids == [SSH_KEY_ID]
        assert cluster.image == CLUSTER_IMAGE
        assert cluster.ip == CLUSTER_IP
        assert responses.assert_call_count(endpoint, 1) is True

    def test_create_cluster_successful(self, clusters_service, endpoint):
        # arrange - add response mock
        # create cluster
        responses.add(responses.POST, endpoint, json={'id': CLUSTER_ID}, status=200)
        # get cluster by id
        url = endpoint + '/' + CLUSTER_ID
        responses.add(responses.GET, url, json=CLUSTER_PAYLOAD[0], status=200)

        # act
        cluster = clusters_service.create(
            hostname=CLUSTER_HOSTNAME,
            cluster_type=CLUSTER_CLUSTER_TYPE,
            image=CLUSTER_IMAGE,
            description=CLUSTER_DESCRIPTION,
            ssh_key_ids=[SSH_KEY_ID],
            location=CLUSTER_LOCATION,
            wait_for_status=CLUSTER_STATUS,
        )

        # assert
        assert isinstance(cluster, Cluster)
        assert cluster.id == CLUSTER_ID
        assert cluster.hostname == CLUSTER_HOSTNAME
        assert cluster.description == CLUSTER_DESCRIPTION
        assert cluster.status == CLUSTER_STATUS
        assert cluster.cluster_type == CLUSTER_CLUSTER_TYPE
        assert len(cluster.worker_nodes) == CLUSTER_NODE_COUNT
        assert cluster.ssh_key_ids == [SSH_KEY_ID]
        assert cluster.location == CLUSTER_LOCATION
        assert cluster.image == CLUSTER_IMAGE
        assert responses.assert_call_count(endpoint, 1) is True
        assert responses.assert_call_count(url, 1) is True

    def test_create_cluster_failed(self, clusters_service, endpoint):
        # arrange - add response mock
        responses.add(
            responses.POST,
            endpoint,
            json={'code': INVALID_REQUEST, 'message': INVALID_REQUEST_MESSAGE},
            status=400,
        )

        # act
        with pytest.raises(APIException) as excinfo:
            clusters_service.create(
                hostname=CLUSTER_HOSTNAME,
                cluster_type=CLUSTER_CLUSTER_TYPE,
                image=CLUSTER_IMAGE,
                description=CLUSTER_DESCRIPTION,
                ssh_key_ids=[SSH_KEY_ID],
                location=CLUSTER_LOCATION,
            )

        # assert
        assert excinfo.value.code == INVALID_REQUEST
        assert excinfo.value.message == INVALID_REQUEST_MESSAGE
        assert responses.assert_call_count(endpoint, 1) is True

    def test_delete_cluster_successful(self, clusters_service, endpoint):
        # arrange - add response mock
        responses.add(responses.PUT, endpoint, status=202)

        # act
        result = clusters_service.delete(CLUSTER_ID)

        # assert
        assert result is None
        assert responses.assert_call_count(endpoint, 1) is True

    def test_delete_cluster_failed(self, clusters_service, endpoint):
        # arrange - add response mock
        responses.add(
            responses.PUT,
            endpoint,
            json={'code': INVALID_REQUEST, 'message': INVALID_REQUEST_MESSAGE},
            status=400,
        )

        # act
        with pytest.raises(APIException) as excinfo:
            clusters_service.delete('invalid_id')

        # assert
        assert excinfo.value.code == INVALID_REQUEST
        assert excinfo.value.message == INVALID_REQUEST_MESSAGE
        assert responses.assert_call_count(endpoint, 1) is True
