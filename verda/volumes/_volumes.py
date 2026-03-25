from verda.constants import Locations, VolumeActions
from verda.helpers import stringify_class_object_properties

VOLUMES_ENDPOINT = '/volumes'


class Volume:
    """A volume model class."""

    def __init__(
        self,
        id: str,
        status: str,
        name: str,
        size: int,
        type: str,
        is_os_volume: bool,
        created_at: str,
        target: str | None = None,
        location: str = Locations.FIN_03,
        instance_id: str | None = None,
        ssh_key_ids: list[str] = [],
        deleted_at: str | None = None,
    ) -> None:
        """Initialize the volume object.

        :param id: volume id
        :type id: str
        :param status: volume status
        :type status: str
        :param name: volume name
        :type name: str
        :param size: volume size in GB
        :type size: int
        :param type: volume type
        :type type: str
        :param is_os_volume: indication whether this is an operating systen volume
        :type is_os_volume: bool
        :param created_at: the time the volume was created (UTC)
        :type created_at: str
        :param target: target device e.g. vda
        :type target: str, optional
        :param location: datacenter location, defaults to "FIN-03"
        :type location: str, optional
        :param instance_id: the instance id the volume is attached to, None if detached
        :type instance_id: str
        :param ssh_key_ids: list of ssh keys ids
        :type ssh_key_ids: list[str]
        :param deleted_at: the time the volume was deleted (UTC), defaults to None
        :type deleted_at: str, optional
        """
        self._id = id
        self._status = status
        self._name = name
        self._size = size
        self._type = type
        self._is_os_volume = is_os_volume
        self._created_at = created_at
        self._target = target
        self._location = location
        self._instance_id = instance_id
        self._ssh_key_ids = ssh_key_ids
        self._deleted_at = deleted_at

    @property
    def id(self) -> str:
        """Get the volume id.

        :return: volume id
        :rtype: str
        """
        return self._id

    @property
    def status(self) -> str:
        """Get the volume status.

        :return: volume status
        :rtype: str
        """
        return self._status

    @property
    def name(self) -> str:
        """Get the volume name.

        :return: volume name
        :rtype: str
        """
        return self._name

    @property
    def size(self) -> int:
        """Get the volume size.

        :return: volume size
        :rtype: int
        """
        return self._size

    @property
    def type(self) -> int:
        """Get the volume type.

        :return: volume type
        :rtype: string
        """
        return self._type

    @property
    def is_os_volume(self) -> bool:
        """Return true iff the volume contains an operating system.

        :return: true iff the volume contains an OS
        :rtype: bool
        """
        return self._is_os_volume

    @property
    def created_at(self) -> str:
        """Get the time when the volume was created (UTC).

        :return: time
        :rtype: str
        """
        return self._created_at

    @property
    def target(self) -> str | None:
        """Get the target device.

        :return: target device
        :rtype: str, optional
        """
        return self._target

    @property
    def location(self) -> str:
        """Get the volume datacenter location.

        :return: datacenter location
        :rtype: str
        """
        return self._location

    @property
    def instance_id(self) -> str | None:
        """Get the instance id the volume is attached to, if attached. Otherwise None.

        :return: instance id if attached, None otherwise
        :rtype: str, optional
        """
        return self._instance_id

    @property
    def ssh_key_ids(self) -> list[str]:
        """Get the SSH key IDs of the instance.

        :return: SSH key IDs
        :rtype: list[str]
        """
        return self._ssh_key_ids

    @property
    def deleted_at(self) -> str | None:
        """Get the time when the volume was deleted (UTC).

        :return: time
        :rtype: str
        """
        return self._deleted_at

    @classmethod
    def create_from_dict(cls: 'Volume', volume_dict: dict) -> 'Volume':
        """Create a Volume object from a dictionary.

        :param volume_dict: dictionary representing the volume
        :type volume_dict: dict
        :return: Volume
        :rtype: Volume
        """
        return cls(
            id=volume_dict['id'],
            status=volume_dict['status'],
            name=volume_dict['name'],
            size=volume_dict['size'],
            type=volume_dict['type'],
            is_os_volume=volume_dict['is_os_volume'],
            created_at=volume_dict['created_at'],
            target=volume_dict['target'],
            location=volume_dict['location'],
            instance_id=volume_dict['instance_id'],
            ssh_key_ids=volume_dict['ssh_key_ids'],
            deleted_at=volume_dict.get('deleted_at'),
        )

    def __str__(self) -> str:
        """Returns a string of the json representation of the volume.

        :return: json representation of the volume
        :rtype: str
        """
        return stringify_class_object_properties(self)


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
        return list(map(Volume.create_from_dict, volumes_dict))

    def get_by_id(self, id: str) -> Volume:
        """Get a specific volume by its.

        :param id: volume id
        :type id: str
        :return: Volume details object
        :rtype: Volume
        """
        volume_dict = self._http_client.get(VOLUMES_ENDPOINT + f'/{id}').json()

        return Volume.create_from_dict(volume_dict)

    def get_in_trash(self) -> list[Volume]:
        """Get all volumes that are in trash.

        :return: list of volume details objects
        :rtype: list[Volume]
        """
        volumes_dicts = self._http_client.get(VOLUMES_ENDPOINT + '/trash').json()

        return list(map(Volume.create_from_dict, volumes_dicts))

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
