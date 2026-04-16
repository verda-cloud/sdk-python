# Copyright 2026 Verda Cloud Oy
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import responses  # https://github.com/getsentry/responses

from verda.constants import VolumeTypes
from verda.volume_types import VolumeType, VolumeTypesService

USD = 'usd'
NVMe_PRICE = 0.2
HDD_PRICE = 0.05


def test_volume_types(http_client):
    responses.add(
        responses.GET,
        http_client._base_url + '/volume-types',
        json=[
            {
                'type': VolumeTypes.NVMe,
                'price': {'currency': USD, 'price_per_month_per_gb': NVMe_PRICE},
            },
            {
                'type': VolumeTypes.HDD,
                'price': {'currency': USD, 'price_per_month_per_gb': HDD_PRICE},
            },
        ],
        status=200,
    )

    volume_types_service = VolumeTypesService(http_client)

    # act
    volumes_types = volume_types_service.get()
    nvme_type = volumes_types[0]
    hdd_type = volumes_types[1]

    # assert
    assert isinstance(volumes_types, list)
    assert len(volumes_types) == 2
    assert isinstance(nvme_type, VolumeType)
    assert isinstance(hdd_type, VolumeType)
    assert nvme_type.type == VolumeTypes.NVMe
    assert nvme_type.price_per_month_per_gb == NVMe_PRICE
    assert hdd_type.type == VolumeTypes.HDD
    assert hdd_type.price_per_month_per_gb == HDD_PRICE
