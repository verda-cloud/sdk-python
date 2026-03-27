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
        pseudo_path: str | None = None,
        mount_command: str | None = None,
        create_directory_command: str | None = None,
        filesystem_to_fstab_command: str | None = None,
        instances: list[dict] | None = None,
        contract: str | None = None,
        base_hourly_cost: float | None = None,
        monthly_price: float | None = None,
        currency: str | None = None,
        long_term: dict | None = None,
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
        :param pseudo_path: volume pseudo path for NFS export, defaults to None
        :type pseudo_path: str, optional
        :param mount_command: ready-to-use NFS mount command, defaults to None
        :type mount_command: str, optional
        :param create_directory_command: mkdir command for mount point, defaults to None
        :type create_directory_command: str, optional
        :param filesystem_to_fstab_command: fstab entry command for persistent mounts, defaults to None
        :type filesystem_to_fstab_command: str, optional
        :param instances: list of attached instance details, defaults to None
        :type instances: list[dict], optional
        :param contract: volume contract type e.g. "LONG_TERM", "PAY_AS_YOU_GO", defaults to None
        :type contract: str, optional
        :param base_hourly_cost: volume base hourly cost, defaults to None
        :type base_hourly_cost: float, optional
        :param monthly_price: volume monthly price, defaults to None
        :type monthly_price: float, optional
        :param currency: volume currency e.g. "usd", "eur", defaults to None
        :type currency: str, optional
        :param long_term: long term contract details, defaults to None
        :type long_term: dict, optional
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
        self._pseudo_path = pseudo_path
        self._mount_command = mount_command
        self._create_directory_command = create_directory_command
        self._filesystem_to_fstab_command = filesystem_to_fstab_command
        self._instances = instances
        self._contract = contract
        self._base_hourly_cost = base_hourly_cost
        self._monthly_price = monthly_price
        self._currency = currency
        self._long_term = long_term

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

    @property
    def pseudo_path(self) -> str | None:
        """Get the volume pseudo path for NFS export.

        :return: volume pseudo path
        :rtype: str, optional
        """
        return self._pseudo_path

    @property
    def mount_command(self) -> str | None:
        """Get the ready-to-use NFS mount command.

        :return: mount command
        :rtype: str, optional
        """
        return self._mount_command

    @property
    def create_directory_command(self) -> str | None:
        """Get the mkdir command for creating the mount point directory.

        :return: create directory command
        :rtype: str, optional
        """
        return self._create_directory_command

    @property
    def filesystem_to_fstab_command(self) -> str | None:
        """Get the fstab entry command for persistent mounts.

        :return: fstab command
        :rtype: str, optional
        """
        return self._filesystem_to_fstab_command

    @property
    def instances(self) -> list[dict] | None:
        """Get the list of attached instance details.

        :return: list of instance details
        :rtype: list[dict], optional
        """
        return self._instances

    @property
    def contract(self) -> str | None:
        """Get the volume contract type.

        :return: contract type e.g. "LONG_TERM", "PAY_AS_YOU_GO"
        :rtype: str, optional
        """
        return self._contract

    @property
    def base_hourly_cost(self) -> float | None:
        """Get the volume base hourly cost.

        :return: base hourly cost
        :rtype: float, optional
        """
        return self._base_hourly_cost

    @property
    def monthly_price(self) -> float | None:
        """Get the volume monthly price.

        :return: monthly price
        :rtype: float, optional
        """
        return self._monthly_price

    @property
    def currency(self) -> str | None:
        """Get the volume currency.

        :return: currency e.g. "usd", "eur"
        :rtype: str, optional
        """
        return self._currency

    @property
    def long_term(self) -> dict | None:
        """Get the long term contract details.

        :return: long term contract details
        :rtype: dict, optional
        """
        return self._long_term

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
            pseudo_path=volume_dict.get('pseudo_path'),
            mount_command=volume_dict.get('mount_command'),
            create_directory_command=volume_dict.get('create_directory_command'),
            filesystem_to_fstab_command=volume_dict.get('filesystem_to_fstab_command'),
            instances=volume_dict.get('instances'),
            contract=volume_dict.get('contract'),
            base_hourly_cost=volume_dict.get('base_hourly_cost'),
            monthly_price=volume_dict.get('monthly_price'),
            currency=volume_dict.get('currency'),
            long_term=volume_dict.get('long_term'),
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
