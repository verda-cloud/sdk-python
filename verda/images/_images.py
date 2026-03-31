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
