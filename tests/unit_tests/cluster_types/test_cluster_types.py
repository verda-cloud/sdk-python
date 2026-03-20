import responses  # https://github.com/getsentry/responses

from verda.cluster_types import ClusterType, ClusterTypesService

CLUSTER_TYPE_ID = 'cluster-c0de-a5d2-4972-ae4e-d429115d055b'


@responses.activate
def test_cluster_types(http_client):
    endpoint = http_client._base_url + '/cluster-types?currency=usd'
    responses.add(
        responses.GET,
        endpoint,
        json=[
            {
                'id': CLUSTER_TYPE_ID,
                'model': 'H200',
                'name': 'H200 Cluster',
                'cluster_type': '16H200',
                'cpu': {'description': '64 CPU', 'number_of_cores': 64},
                'gpu': {'description': '16x H200', 'number_of_gpus': 16},
                'gpu_memory': {'description': '2.2TB VRAM', 'size_in_gigabytes': 2200},
                'memory': {'description': '4TB RAM', 'size_in_gigabytes': 4096},
                'price_per_hour': '45.50',
                'currency': 'usd',
                'manufacturer': 'NVIDIA',
                'node_details': ['2x 8 GPU nodes'],
                'supported_os': ['ubuntu-24.04-cuda-12.8-cluster'],
            }
        ],
        status=200,
    )

    service = ClusterTypesService(http_client)

    cluster_types = service.get()
    cluster_type = cluster_types[0]

    assert isinstance(cluster_types, list)
    assert len(cluster_types) == 1
    assert isinstance(cluster_type, ClusterType)
    assert cluster_type.id == CLUSTER_TYPE_ID
    assert cluster_type.model == 'H200'
    assert cluster_type.name == 'H200 Cluster'
    assert cluster_type.cluster_type == '16H200'
    assert cluster_type.price_per_hour == 45.5
    assert cluster_type.currency == 'usd'
    assert cluster_type.manufacturer == 'NVIDIA'
    assert cluster_type.node_details == ['2x 8 GPU nodes']
    assert cluster_type.supported_os == ['ubuntu-24.04-cuda-12.8-cluster']
    assert responses.assert_call_count(endpoint, 1) is True
