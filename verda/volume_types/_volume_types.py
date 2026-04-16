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

VOLUME_TYPES_ENDPOINT = '/volume-types'


class VolumeType:
    """Volume type."""

    def __init__(self, type: str, price_per_month_per_gb: float) -> None:
        """Initialize a volume type object.

        :param type: volume type name
        :type type: str
        :param price_per_month_per_gb: price per month per gb of storage
        :type price_per_month_per_gb: float
        """
        self._type = type
        self._price_per_month_per_gb = price_per_month_per_gb

    @property
    def type(self) -> str:
        """Get the volume type.

        :return: volume type
        :rtype: str
        """
        return self._type

    @property
    def price_per_month_per_gb(self) -> str:
        """Get the volume price_per_month_per_gb.

        :return: volume price_per_month_per_gb
        :rtype: str
        """
        return self._price_per_month_per_gb

    def __str__(self) -> str:
        """Prints the volume type.

        :return: volume type string representation
        :rtype: str
        """
        return f'type: {self._type}\nprice_per_month_per_gb: ${self._price_per_month_per_gb}'


class VolumeTypesService:
    """A service for interacting with the volume-types endpoint."""

    def __init__(self, http_client) -> None:
        self._http_client = http_client

    def get(self) -> list[VolumeType]:
        """Get all volume types.

        :return: list of volume type objects
        :rtype: list[VolumesType]
        """
        volume_types = self._http_client.get(VOLUME_TYPES_ENDPOINT).json()
        volume_type_objects = [
            VolumeType(
                type=volume_type['type'],
                price_per_month_per_gb=volume_type['price']['price_per_month_per_gb'],
            )
            for volume_type in volume_types
        ]

        return volume_type_objects
