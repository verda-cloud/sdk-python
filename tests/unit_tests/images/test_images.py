import json

import responses  # https://github.com/getsentry/responses
from responses import matchers

from verda.images import Image, ImagesService

IMAGE_RESPONSE = {
    'id': '0888da25-bb0d-41cc-a191-dccae45d96fd',
    'name': 'Ubuntu 20.04 + CUDA 11.0',
    'details': ['Ubuntu 20.04', 'CUDA 11.0'],
    'image_type': 'ubuntu-20.04-cuda-11.0',
}


def test_images(http_client):
    # arrange
    responses.add(
        responses.GET,
        http_client._base_url + '/images',
        json=[IMAGE_RESPONSE],
        status=200,
    )

    image_service = ImagesService(http_client)

    # act
    images = image_service.get()

    # assert
    assert isinstance(images, list)
    assert len(images) == 1
    assert isinstance(images[0], Image)
    assert images[0].id == '0888da25-bb0d-41cc-a191-dccae45d96fd'
    assert images[0].name == 'Ubuntu 20.04 + CUDA 11.0'
    assert images[0].image_type == 'ubuntu-20.04-cuda-11.0'
    assert isinstance(images[0].details, list)
    assert images[0].details[0] == 'Ubuntu 20.04'
    assert images[0].details[1] == 'CUDA 11.0'
    assert json.loads(str(images[0])) == IMAGE_RESPONSE


def test_images_filter_by_instance_type(http_client):
    # arrange
    responses.add(
        responses.GET,
        http_client._base_url + '/images',
        match=[matchers.query_param_matcher({'instance_type': '1A100.22V'})],
        json=[IMAGE_RESPONSE],
        status=200,
    )

    image_service = ImagesService(http_client)

    # act
    images = image_service.get(instance_type='1A100.22V')

    # assert
    assert isinstance(images, list)
    assert len(images) == 1
    assert isinstance(images[0], Image)
    assert images[0].id == '0888da25-bb0d-41cc-a191-dccae45d96fd'
    assert images[0].image_type == 'ubuntu-20.04-cuda-11.0'
