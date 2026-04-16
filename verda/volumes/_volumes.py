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

from dataclasses import dataclass, field

from dataclasses_json import Undefined, dataclass_json

from verda.constants import Locations, VolumeActions

VOLUMES_ENDPOINT = '/volumes'


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Volume:
    """Represents a storage volume with its configuration and state.

    Attributes:
        id: Unique identifier for the volume.
        status: Current status of the volume (e.g., 'attached', 'detached').
        name: Volume name.
        size: Volume size in GB.
        type: Volume type (e.g., 'NVMe', 'HDD', 'NVMe_Shared').
        is_os_volume: Whether this is an operating system volume.
        created_at: Timestamp of volume creation (UTC).
        target: Target device (e.g., 'vda').
        location: Datacenter location code.
        instance_id: ID of the instance the volume is attached to, None if detached.
        ssh_key_ids: List of SSH key IDs linked to the volume.
        deleted_at: Timestamp of volume deletion (UTC).
        pseudo_path: Volume pseudo path for NFS export.
        mount_command: Ready-to-use NFS mount command.
        create_directory_command: mkdir command for creating the mount point directory.
        filesystem_to_fstab_command: fstab entry command for persistent mounts.
        instances: List of attached instance details.
        contract: Volume contract type (e.g., 'LONG_TERM', 'PAY_AS_YOU_GO').
        base_hourly_cost: Volume base hourly cost.
        monthly_price: Volume monthly price.
        currency: Volume currency (e.g., 'usd', 'eur').
        long_term: Long term contract details.
    """

    id: str
    status: str
    name: str
    size: int
    type: str
    is_os_volume: bool
    created_at: str
    target: str | None = None
    location: str = Locations.FIN_03
    instance_id: str | None = None
    ssh_key_ids: list[str] = field(default_factory=list)
    deleted_at: str | None = None
    pseudo_path: str | None = None
    mount_command: str | None = None
    create_directory_command: str | None = None
    filesystem_to_fstab_command: str | None = None
    instances: list[dict] | None = None
    contract: str | None = None
    base_hourly_cost: float | None = None
    monthly_price: float | None = None
    currency: str | None = None
    long_term: dict | None = None

    @classmethod
    def create_from_dict(cls, volume_dict: dict) -> 'Volume':
        """Create a Volume object from a dictionary.

        .. deprecated:: Use :meth:`from_dict` instead.
        """
        return cls.from_dict(volume_dict)


class VolumesService:
    """A service for interacting with the volumes endpoint."""

    def __init__(self, http_client) -> None:
        self._http_client = http_client

    def get(self, status: str | None = None) -> list[Volume]:
        """Get all of the client's non-deleted volumes, or volumes with specific status.

        :param status: optional, status of the volumes, defaults to None
        :type status: str, optional
        :return: list of volume details objects
        :rtype: list[Volume]
        """
        volumes_dict = self._http_client.get(VOLUMES_ENDPOINT, params={'status': status}).json()
        return [Volume.from_dict(v) for v in volumes_dict]

    def get_by_id(self, id: str) -> Volume:
        """Get a specific volume by its.

        :param id: volume id
        :type id: str
        :return: Volume details object
        :rtype: Volume
        """
        volume_dict = self._http_client.get(VOLUMES_ENDPOINT + f'/{id}').json()

        return Volume.from_dict(volume_dict)

    def get_in_trash(self) -> list[Volume]:
        """Get all volumes that are in trash.

        :return: list of volume details objects
        :rtype: list[Volume]
        """
        volumes_dicts = self._http_client.get(VOLUMES_ENDPOINT + '/trash').json()

        return [Volume.from_dict(v) for v in volumes_dicts]

    def create(
        self,
        type: str,
        name: str,
        size: int,
        instance_id: str | None = None,
        location: str = Locations.FIN_03,
    ) -> Volume:
        """Create new volume.

        :param type: volume type
        :type type: str
        :param name: volume name
        :type name: str
        :param size: volume size, in GB
        :type size: int
        :param instance_id: Instance id to be attached to, defaults to None
        :type instance_id: str, optional
        :param location: datacenter location, defaults to "FIN-03"
        :type location: str, optional
        :return: the new volume object
        :rtype: Volume
        """
        payload = {
            'type': type,
            'name': name,
            'size': size,
            'instance_id': instance_id,
            'location_code': location,
        }
        id = self._http_client.post(VOLUMES_ENDPOINT, json=payload).text
        volume = self.get_by_id(id)
        return volume

    def attach(self, id_list: list[str] | str, instance_id: str) -> None:
        """Attach multiple volumes or single volume to an instance.

        Note: the instance needs to be shut-down (offline)

        :param id_list: list of volume ids, or a volume id
        :type id_list: Union[list[str], str]
        :param instance_id: instance id the volume(s) will be attached to
        :type instance_id: str
        """
        payload = {
            'id': id_list,
            'action': VolumeActions.ATTACH,
            'instance_id': instance_id,
        }

        self._http_client.put(VOLUMES_ENDPOINT, json=payload)
        return

    def detach(self, id_list: list[str] | str) -> None:
        """Detach multiple volumes or single volume from an instance(s).

        Note: the instances need to be shut-down (offline)

        :param id_list: list of volume ids, or a volume id
        :type id_list: Union[list[str], str]
        """
        payload = {
            'id': id_list,
            'action': VolumeActions.DETACH,
        }

        self._http_client.put(VOLUMES_ENDPOINT, json=payload)
        return

    def clone(self, id: str, name: str | None = None, type: str | None = None) -> Volume:
        """Clone a volume or multiple volumes.

        :param id: volume id or list of volume ids
        :type id: str or list[str]
        :param name: new volume name
        :type name: str
        :param type: volume type
        :type type: str, optional
        :return: the new volume object, or a list of volume objects if cloned mutliple volumes
        :rtype: Volume or list[Volume]
        """
        payload = {'id': id, 'action': VolumeActions.CLONE, 'name': name, 'type': type}

        # clone volume(s)
        volume_ids_array = self._http_client.put(VOLUMES_ENDPOINT, json=payload).json()

        # map the IDs into Volume objects
        volumes_array = [self.get_by_id(volume_id) for volume_id in volume_ids_array]

        # if the array has only one element, return that element
        if len(volumes_array) == 1:
            return volumes_array[0]

        # otherwise return the volumes array
        return volumes_array

    def rename(self, id_list: list[str] | str, name: str) -> None:
        """Rename multiple volumes or single volume.

        :param id_list: list of volume ids, or a volume id
        :type id_list: Union[list[str], str]
        :param name: new name
        :type name: str
        """
        payload = {'id': id_list, 'action': VolumeActions.RENAME, 'name': name}

        self._http_client.put(VOLUMES_ENDPOINT, json=payload)
        return

    def increase_size(self, id_list: list[str] | str, size: int) -> None:
        """Increase size of multiple volumes or single volume.

        :param id_list: list of volume ids, or a volume id
        :type id_list: Union[list[str], str]
        :param size: new size in GB
        :type size: int
        """
        payload = {
            'id': id_list,
            'action': VolumeActions.INCREASE_SIZE,
            'size': size,
        }

        self._http_client.put(VOLUMES_ENDPOINT, json=payload)
        return

    def delete_by_id(self, volume_id: str, is_permanent: bool = False) -> None:
        """Delete a single volume by id using the DELETE endpoint.

        :param volume_id: volume id
        :type volume_id: str
        :param is_permanent: if True, volume is removed permanently; if False, moves to trash
        :type is_permanent: bool, optional
        """
        payload = {'is_permanent': is_permanent}
        self._http_client.delete(VOLUMES_ENDPOINT + f'/{volume_id}', json=payload)
        return

    def delete(self, id_list: list[str] | str, is_permanent: bool = False) -> None:
        """Delete multiple volumes or single volume.

        Note: if attached to any instances, they need to be shut-down (offline)

        :param id_list: list of volume ids, or a volume id
        :type id_list: Union[list[str], str]
        """
        payload = {
            'id': id_list,
            'action': VolumeActions.DELETE,
            'is_permanent': is_permanent,
        }

        self._http_client.put(VOLUMES_ENDPOINT, json=payload)
        return
