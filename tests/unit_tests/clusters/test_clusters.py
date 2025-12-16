import pytest
import responses  # https://github.com/getsentry/responses

from verda.clusters import Cluster, ClusterNode, ClustersService
from verda.constants import ErrorCodes, Locations
from verda.exceptions import APIException

INVALID_REQUEST = ErrorCodes.INVALID_REQUEST
INVALID_REQUEST_MESSAGE = 'Invalid cluster request'

CLUSTER_ID = 'deadc0de-a5d2-4972-ae4e-d429115d055b'
SSH_KEY_ID = '12345dc1-a5d2-4972-ae4e-d429115d055b'

CLUSTER_NAME = 'test-cluster'
CLUSTER_DESCRIPTION = 'Test compute cluster'
CLUSTER_STATUS = 'running'
CLUSTER_INSTANCE_TYPE = '8V100.48V'
CLUSTER_NODE_COUNT = 3
CLUSTER_LOCATION = Locations.FIN_01
CLUSTER_IMAGE = 'ubuntu-24.04-cuda-12.8-open-docker'
CLUSTER_CREATED_AT = '2024-01-01T00:00:00Z'
CLUSTER_MASTER_IP = '10.0.0.1'
CLUSTER_ENDPOINT = 'cluster-endpoint.verda.com'

NODE_1_ID = 'node1-c0de-a5d2-4972-ae4e-d429115d055b'
NODE_2_ID = 'node2-c0de-a5d2-4972-ae4e-d429115d055b'
NODE_3_ID = 'node3-c0de-a5d2-4972-ae4e-d429115d055b'

NODES_PAYLOAD = [
    {
        'id': NODE_1_ID,
        'instance_type': CLUSTER_INSTANCE_TYPE,
        'status': 'running',
        'hostname': 'test-cluster-node-1',
        'ip': '10.0.0.2',
        'created_at': CLUSTER_CREATED_AT,
    },
    {
        'id': NODE_2_ID,
        'instance_type': CLUSTER_INSTANCE_TYPE,
        'status': 'running',
        'hostname': 'test-cluster-node-2',
        'ip': '10.0.0.3',
        'created_at': CLUSTER_CREATED_AT,
    },
    {
        'id': NODE_3_ID,
        'instance_type': CLUSTER_INSTANCE_TYPE,
        'status': 'running',
        'hostname': 'test-cluster-node-3',
        'ip': '10.0.0.4',
        'created_at': CLUSTER_CREATED_AT,
    },
]

CLUSTER_PAYLOAD = [
    {
        'id': CLUSTER_ID,
        'name': CLUSTER_NAME,
        'description': CLUSTER_DESCRIPTION,
        'status': CLUSTER_STATUS,
        'created_at': CLUSTER_CREATED_AT,
        'location': CLUSTER_LOCATION,
        'instance_type': CLUSTER_INSTANCE_TYPE,
        'node_count': CLUSTER_NODE_COUNT,
        'nodes': NODES_PAYLOAD,
        'ssh_key_ids': [SSH_KEY_ID],
        'image': CLUSTER_IMAGE,
        'master_ip': CLUSTER_MASTER_IP,
        'endpoint': CLUSTER_ENDPOINT,
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
        assert cluster.name == CLUSTER_NAME
        assert cluster.description == CLUSTER_DESCRIPTION
        assert cluster.status == CLUSTER_STATUS
        assert cluster.created_at == CLUSTER_CREATED_AT
        assert cluster.location == CLUSTER_LOCATION
        assert cluster.instance_type == CLUSTER_INSTANCE_TYPE
        assert cluster.node_count == CLUSTER_NODE_COUNT
        assert isinstance(cluster.nodes, list)
        assert len(cluster.nodes) == CLUSTER_NODE_COUNT
        assert isinstance(cluster.nodes[0], ClusterNode)
        assert cluster.ssh_key_ids == [SSH_KEY_ID]
        assert cluster.image == CLUSTER_IMAGE
        assert cluster.master_ip == CLUSTER_MASTER_IP
        assert cluster.endpoint == CLUSTER_ENDPOINT
        assert responses.assert_call_count(endpoint, 1) is True

    def test_get_clusters_by_status_successful(self, clusters_service, endpoint):
        # arrange - add response mock
        url = endpoint + '?status=running'
        responses.add(responses.GET, url, json=CLUSTER_PAYLOAD, status=200)

        # act
        clusters = clusters_service.get(status='running')
        cluster = clusters[0]

        # assert
        assert isinstance(clusters, list)
        assert len(clusters) == 1
        assert isinstance(cluster, Cluster)
        assert cluster.id == CLUSTER_ID
        assert cluster.status == CLUSTER_STATUS
        assert responses.assert_call_count(url, 1) is True

    def test_get_clusters_by_status_failed(self, clusters_service, endpoint):
        # arrange - add response mock
        url = endpoint + '?status=invalid_status'
        responses.add(
            responses.GET,
            url,
            json={'code': INVALID_REQUEST, 'message': INVALID_REQUEST_MESSAGE},
            status=400,
        )

        # act
        with pytest.raises(APIException) as excinfo:
            clusters_service.get(status='invalid_status')

        # assert
        assert excinfo.value.code == INVALID_REQUEST
        assert excinfo.value.message == INVALID_REQUEST_MESSAGE
        assert responses.assert_call_count(url, 1) is True

    def test_get_cluster_by_id_successful(self, clusters_service, endpoint):
        # arrange - add response mock
        url = endpoint + '/' + CLUSTER_ID
        responses.add(responses.GET, url, json=CLUSTER_PAYLOAD[0], status=200)

        # act
        cluster = clusters_service.get_by_id(CLUSTER_ID)

        # assert
        assert isinstance(cluster, Cluster)
        assert cluster.id == CLUSTER_ID
        assert cluster.name == CLUSTER_NAME
        assert cluster.description == CLUSTER_DESCRIPTION
        assert cluster.status == CLUSTER_STATUS
        assert cluster.instance_type == CLUSTER_INSTANCE_TYPE
        assert cluster.node_count == CLUSTER_NODE_COUNT
        assert responses.assert_call_count(url, 1) is True

    def test_get_cluster_by_id_failed(self, clusters_service, endpoint):
        # arrange - add response mock
        url = endpoint + '/invalid_id'
        responses.add(
            responses.GET,
            url,
            json={'code': INVALID_REQUEST, 'message': INVALID_REQUEST_MESSAGE},
            status=400,
        )

        # act
        with pytest.raises(APIException) as excinfo:
            clusters_service.get_by_id('invalid_id')

        # assert
        assert excinfo.value.code == INVALID_REQUEST
        assert excinfo.value.message == INVALID_REQUEST_MESSAGE
        assert responses.assert_call_count(url, 1) is True

    def test_create_cluster_successful(self, clusters_service, endpoint):
        # arrange - add response mock
        # create cluster
        responses.add(responses.POST, endpoint, body=CLUSTER_ID, status=200)
        # get cluster by id
        url = endpoint + '/' + CLUSTER_ID
        responses.add(responses.GET, url, json=CLUSTER_PAYLOAD[0], status=200)

        # act
        cluster = clusters_service.create(
            name=CLUSTER_NAME,
            instance_type=CLUSTER_INSTANCE_TYPE,
            node_count=CLUSTER_NODE_COUNT,
            image=CLUSTER_IMAGE,
            description=CLUSTER_DESCRIPTION,
            ssh_key_ids=[SSH_KEY_ID],
            location=CLUSTER_LOCATION,
        )

        # assert
        assert isinstance(cluster, Cluster)
        assert cluster.id == CLUSTER_ID
        assert cluster.name == CLUSTER_NAME
        assert cluster.description == CLUSTER_DESCRIPTION
        assert cluster.status == CLUSTER_STATUS
        assert cluster.instance_type == CLUSTER_INSTANCE_TYPE
        assert cluster.node_count == CLUSTER_NODE_COUNT
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
                name=CLUSTER_NAME,
                instance_type=CLUSTER_INSTANCE_TYPE,
                node_count=CLUSTER_NODE_COUNT,
                image=CLUSTER_IMAGE,
                description=CLUSTER_DESCRIPTION,
            )

        # assert
        assert excinfo.value.code == INVALID_REQUEST
        assert excinfo.value.message == INVALID_REQUEST_MESSAGE
        assert responses.assert_call_count(endpoint, 1) is True

    def test_delete_cluster_successful(self, clusters_service, endpoint):
        # arrange - add response mock
        url = endpoint + '/' + CLUSTER_ID
        responses.add(responses.DELETE, url, status=202)

        # act
        result = clusters_service.delete(CLUSTER_ID)

        # assert
        assert result is None
        assert responses.assert_call_count(url, 1) is True

    def test_delete_cluster_failed(self, clusters_service, endpoint):
        # arrange - add response mock
        url = endpoint + '/invalid_id'
        responses.add(
            responses.DELETE,
            url,
            json={'code': INVALID_REQUEST, 'message': INVALID_REQUEST_MESSAGE},
            status=400,
        )

        # act
        with pytest.raises(APIException) as excinfo:
            clusters_service.delete('invalid_id')

        # assert
        assert excinfo.value.code == INVALID_REQUEST
        assert excinfo.value.message == INVALID_REQUEST_MESSAGE
        assert responses.assert_call_count(url, 1) is True

    def test_scale_cluster_successful(self, clusters_service, endpoint):
        # arrange - add response mock
        new_node_count = 5
        scaled_payload = CLUSTER_PAYLOAD[0].copy()
        scaled_payload['node_count'] = new_node_count

        # scale endpoint
        scale_url = endpoint + '/' + CLUSTER_ID + '/scale'
        responses.add(responses.PUT, scale_url, status=200)

        # get cluster by id
        get_url = endpoint + '/' + CLUSTER_ID
        responses.add(responses.GET, get_url, json=scaled_payload, status=200)

        # act
        cluster = clusters_service.scale(CLUSTER_ID, new_node_count)

        # assert
        assert isinstance(cluster, Cluster)
        assert cluster.id == CLUSTER_ID
        assert cluster.node_count == new_node_count
        assert responses.assert_call_count(scale_url, 1) is True
        assert responses.assert_call_count(get_url, 1) is True

    def test_scale_cluster_failed(self, clusters_service, endpoint):
        # arrange - add response mock
        url = endpoint + '/' + CLUSTER_ID + '/scale'
        responses.add(
            responses.PUT,
            url,
            json={'code': INVALID_REQUEST, 'message': INVALID_REQUEST_MESSAGE},
            status=400,
        )

        # act
        with pytest.raises(APIException) as excinfo:
            clusters_service.scale(CLUSTER_ID, 5)

        # assert
        assert excinfo.value.code == INVALID_REQUEST
        assert excinfo.value.message == INVALID_REQUEST_MESSAGE
        assert responses.assert_call_count(url, 1) is True

    def test_get_cluster_nodes_successful(self, clusters_service, endpoint):
        # arrange - add response mock
        url = endpoint + '/' + CLUSTER_ID + '/nodes'
        responses.add(responses.GET, url, json=NODES_PAYLOAD, status=200)

        # act
        nodes = clusters_service.get_nodes(CLUSTER_ID)

        # assert
        assert isinstance(nodes, list)
        assert len(nodes) == CLUSTER_NODE_COUNT
        assert isinstance(nodes[0], ClusterNode)
        assert nodes[0].id == NODE_1_ID
        assert nodes[0].instance_type == CLUSTER_INSTANCE_TYPE
        assert nodes[0].status == 'running'
        assert nodes[1].id == NODE_2_ID
        assert nodes[2].id == NODE_3_ID
        assert responses.assert_call_count(url, 1) is True

    def test_get_cluster_nodes_failed(self, clusters_service, endpoint):
        # arrange - add response mock
        url = endpoint + '/invalid_id/nodes'
        responses.add(
            responses.GET,
            url,
            json={'code': INVALID_REQUEST, 'message': INVALID_REQUEST_MESSAGE},
            status=400,
        )

        # act
        with pytest.raises(APIException) as excinfo:
            clusters_service.get_nodes('invalid_id')

        # assert
        assert excinfo.value.code == INVALID_REQUEST
        assert excinfo.value.message == INVALID_REQUEST_MESSAGE
        assert responses.assert_call_count(url, 1) is True
