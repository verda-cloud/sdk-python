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

from dataclasses import dataclass

from dataclasses_json import Undefined, dataclass_json

IMAGES_ENDPOINT = '/images'


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Image:
    """Represents an OS image available for instances.

    Attributes:
        id: Unique identifier for the image.
        name: Human-readable name of the image.
        image_type: Image type identifier, e.g. 'ubuntu-20.04-cuda-11.0'.
        details: List of additional image details.
    """

    id: str
    name: str
    image_type: str
    details: list[str]

    def __str__(self) -> str:
        return self.to_json(indent=2)


class ImagesService:
    """A service for interacting with the images endpoint."""

    def __init__(self, http_client) -> None:
        self._http_client = http_client

    def get(self, instance_type: str | None = None) -> list[Image]:
        """Get the available instance images.

        Args:
            instance_type: Filter OS images by instance type, e.g. '1A100.22V'.
                Default is all instance images.

        Returns:
            List of Image objects.
        """
        params = {'instance_type': instance_type} if instance_type else None
        images = self._http_client.get(IMAGES_ENDPOINT, params=params).json()
        return [Image.from_dict(image) for image in images]
