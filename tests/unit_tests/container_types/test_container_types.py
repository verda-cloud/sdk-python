import responses  # https://github.com/getsentry/responses

from verda.container_types import ContainerType, ContainerTypesService

CONTAINER_TYPE_ID = 'type-c0de-a5d2-4972-ae4e-d429115d055b'


@responses.activate
def test_container_types(http_client):
    endpoint = http_client._base_url + '/container-types?currency=eur'
    responses.add(
        responses.GET,
        endpoint,
        json=[
            {
                'id': CONTAINER_TYPE_ID,
                'model': 'H100',
                'name': 'H100 SXM5 80GB',
                'instance_type': '1H100.80S.22V',
                'cpu': {'description': '22 CPU', 'number_of_cores': 22},
                'gpu': {'description': '1x H100 SXM5 80GB', 'number_of_gpus': 1},
                'gpu_memory': {'description': '80GB GPU RAM', 'size_in_gigabytes': 80},
                'memory': {'description': '187GB RAM', 'size_in_gigabytes': 187},
                'serverless_price': '1.75',
                'serverless_spot_price': '0.87',
                'currency': 'eur',
                'manufacturer': 'NVIDIA',
            }
        ],
        status=200,
    )

    service = ContainerTypesService(http_client)

    container_types = service.get(currency='eur')
    container_type = container_types[0]

    assert isinstance(container_types, list)
    assert len(container_types) == 1
    assert isinstance(container_type, ContainerType)
    assert container_type.id == CONTAINER_TYPE_ID
    assert container_type.model == 'H100'
    assert container_type.name == 'H100 SXM5 80GB'
    assert container_type.instance_type == '1H100.80S.22V'
    assert container_type.serverless_price == 1.75
    assert container_type.serverless_spot_price == 0.87
    assert container_type.currency == 'eur'
    assert container_type.manufacturer == 'NVIDIA'
    assert responses.assert_call_count(endpoint, 1) is True
