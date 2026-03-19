import responses  # https://github.com/getsentry/responses

from verda.instance_types import InstanceType, InstanceTypesService

TYPE_ID = '01cf5dc1-a5d2-4972-ae4e-d429115d055b'
CPU_DESCRIPTION = '48 CPU 3.5GHz'
NUMBER_OF_CORES = 48
GPU_DESCRIPTION = '8x NVidia Tesla V100'
NUMBER_OF_GPUS = 8
MEMORY_DESCRIPTION = '192GB RAM'
MEMORY_SIZE = 192
GPU_MEMORY_DESCRIPTION = '128GB VRAM'
GPU_MEMORY_SIZE = 128
STORAGE_DESCRIPTION = '1800GB NVME'
STORAGE_SIZE = 1800
INSTANCE_TYPE_DESCRIPTION = 'Dedicated Bare metal Server'
BEST_FOR = ['Large model inference', 'Multi-GPU training']
MODEL = 'V100'
NAME = 'Tesla V100'
P2P = '300 GB/s'
PRICE_PER_HOUR = 5.0
SPOT_PRICE_PER_HOUR = 2.5
MAX_DYNAMIC_PRICE = 7.5
SERVERLESS_PRICE = 1.25
SERVERLESS_SPOT_PRICE = 0.75
INSTANCE_TYPE = '8V100.48M'
CURRENCY = 'eur'
MANUFACTURER = 'NVIDIA'
DISPLAY_NAME = 'NVIDIA Tesla V100'
SUPPORTED_OS = ['ubuntu-24.04-cuda-12.8-open-docker']

PRICE_HISTORY_PAYLOAD = [{'date': '2024-01-01', 'price_per_hour': '2.00'}]


@responses.activate
def test_instance_types(http_client):
    # arrange - add response mock
    responses.add(
        responses.GET,
        http_client._base_url + '/instance-types?currency=eur',
        json=[
            {
                'id': TYPE_ID,
                'best_for': BEST_FOR,
                'cpu': {
                    'description': CPU_DESCRIPTION,
                    'number_of_cores': NUMBER_OF_CORES,
                },
                'deploy_warning': 'Use updated drivers',
                'gpu': {
                    'description': GPU_DESCRIPTION,
                    'number_of_gpus': NUMBER_OF_GPUS,
                },
                'memory': {
                    'description': MEMORY_DESCRIPTION,
                    'size_in_gigabytes': MEMORY_SIZE,
                },
                'gpu_memory': {
                    'description': GPU_MEMORY_DESCRIPTION,
                    'size_in_gigabytes': GPU_MEMORY_SIZE,
                },
                'storage': {
                    'description': STORAGE_DESCRIPTION,
                    'size_in_gigabytes': STORAGE_SIZE,
                },
                'description': INSTANCE_TYPE_DESCRIPTION,
                'model': MODEL,
                'name': NAME,
                'p2p': P2P,
                'price_per_hour': '5.00',
                'spot_price': '2.50',
                'max_dynamic_price': '7.50',
                'serverless_price': '1.25',
                'serverless_spot_price': '0.75',
                'instance_type': INSTANCE_TYPE,
                'currency': CURRENCY,
                'manufacturer': MANUFACTURER,
                'display_name': DISPLAY_NAME,
                'supported_os': SUPPORTED_OS,
            }
        ],
        status=200,
    )

    instance_types_service = InstanceTypesService(http_client)

    # act
    instance_types = instance_types_service.get(currency='eur')
    instance_type = instance_types[0]

    # assert
    assert isinstance(instance_types, list)
    assert len(instance_types) == 1
    assert isinstance(instance_type, InstanceType)
    assert instance_type.id == TYPE_ID
    assert instance_type.description == INSTANCE_TYPE_DESCRIPTION
    assert instance_type.price_per_hour == PRICE_PER_HOUR
    assert instance_type.spot_price_per_hour == SPOT_PRICE_PER_HOUR
    assert instance_type.instance_type == INSTANCE_TYPE
    assert instance_type.best_for == BEST_FOR
    assert instance_type.model == MODEL
    assert instance_type.name == NAME
    assert instance_type.p2p == P2P
    assert instance_type.currency == CURRENCY
    assert instance_type.manufacturer == MANUFACTURER
    assert instance_type.display_name == DISPLAY_NAME
    assert instance_type.supported_os == SUPPORTED_OS
    assert instance_type.deploy_warning == 'Use updated drivers'
    assert instance_type.max_dynamic_price == MAX_DYNAMIC_PRICE
    assert instance_type.serverless_price == SERVERLESS_PRICE
    assert instance_type.serverless_spot_price == SERVERLESS_SPOT_PRICE
    assert isinstance(instance_type.cpu, dict)
    assert isinstance(instance_type.gpu, dict)
    assert isinstance(instance_type.memory, dict)
    assert isinstance(instance_type.storage, dict)
    assert instance_type.cpu['description'] == CPU_DESCRIPTION
    assert instance_type.gpu['description'] == GPU_DESCRIPTION
    assert instance_type.memory['description'] == MEMORY_DESCRIPTION
    assert instance_type.gpu_memory['description'] == GPU_MEMORY_DESCRIPTION
    assert instance_type.storage['description'] == STORAGE_DESCRIPTION
    assert instance_type.cpu['number_of_cores'] == NUMBER_OF_CORES
    assert instance_type.gpu['number_of_gpus'] == NUMBER_OF_GPUS
    assert instance_type.memory['size_in_gigabytes'] == MEMORY_SIZE
    assert instance_type.gpu_memory['size_in_gigabytes'] == GPU_MEMORY_SIZE
    assert instance_type.storage['size_in_gigabytes'] == STORAGE_SIZE


@responses.activate
def test_instance_type_price_history(http_client):
    # arrange - add response mock
    responses.add(
        responses.GET,
        http_client._base_url + '/instance-types/price-history',
        json=PRICE_HISTORY_PAYLOAD,
        status=200,
    )

    instance_types_service = InstanceTypesService(http_client)

    # act
    price_history = instance_types_service.get_price_history()

    # assert
    assert price_history == PRICE_HISTORY_PAYLOAD
