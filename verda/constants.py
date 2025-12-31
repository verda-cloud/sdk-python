class Actions:
    """Instance actions."""

    START = 'start'
    SHUTDOWN = 'shutdown'
    DELETE = 'delete'
    HIBERNATE = 'hibernate'
    RESTORE = 'restore'

    def __init__(self):
        return


class VolumeActions:
    """Storage volume actions."""

    ATTACH = 'attach'
    DETACH = 'detach'
    RENAME = 'rename'
    INCREASE_SIZE = 'resize'
    DELETE = 'delete'
    CLONE = 'clone'

    def __init__(self):
        return


class InstanceStatus:
    """Instance status."""

    ORDERED = 'ordered'
    RUNNING = 'running'
    PROVISIONING = 'provisioning'
    OFFLINE = 'offline'
    STARTING_HIBERNATION = 'starting_hibernation'
    HIBERNATING = 'hibernating'
    RESTORING = 'restoring'
    ERROR = 'error'

    def __init__(self):
        return


class VolumeStatus:
    """Storage volume status."""

    ORDERED = 'ordered'
    CREATING = 'creating'
    ATTACHED = 'attached'
    DETACHED = 'detached'
    DELETING = 'deleting'
    DELETED = 'deleted'
    CLONING = 'cloning'

    def __init__(self):
        return


class ClusterStatus:
    """Cluster status."""

    ORDERED = 'ordered'
    PROVISIONING = 'provisioning'
    RUNNING = 'running'
    DISCONTINUED = 'discontinued'
    ERROR = 'error'

    def __init__(self):
        return


class VolumeTypes:
    """Storage volume types."""

    NVMe = 'NVMe'
    HDD = 'HDD'
    SFS = 'NVMe_Shared'

    def __init__(self):
        return


class Locations:
    """Datacenter locations."""

    FIN_01: str = 'FIN-01'
    FIN_02: str = 'FIN-02'
    FIN_03: str = 'FIN-03'
    ICE_01: str = 'ICE-01'

    def __init__(self):
        return


class ErrorCodes:
    """Error codes."""

    INVALID_REQUEST = 'invalid_request'
    UNAUTHORIZED_REQUEST = 'unauthorized_request'
    INSUFFICIENT_FUNDS = 'insufficient_funds'
    FORBIDDEN_ACTION = 'forbidden_action'
    NOT_FOUND = 'not_found'
    SERVER_ERROR = 'server_error'
    SERVICE_UNAVAILABLE = 'service_unavailable'

    def __init__(self):
        return


class Constants:
    """Constants."""

    def __init__(self, base_url, version):
        self.instance_actions: Actions = Actions()
        """Available actions to perform on an instance"""

        self.volume_actions: VolumeActions = VolumeActions()
        """Available actions to perform on a volume"""

        self.instance_status: InstanceStatus = InstanceStatus()
        """Possible instance statuses"""

        self.volume_status: VolumeStatus = VolumeStatus()
        """Possible volume statuses"""

        self.cluster_status: ClusterStatus = ClusterStatus()
        """Possible cluster statuses"""

        self.volume_types: VolumeTypes = VolumeTypes()
        """Available volume types"""

        self.locations: Locations = Locations()
        """Available locations"""

        self.error_codes: ErrorCodes = ErrorCodes()
        """Available error codes"""

        self.base_url: str = base_url
        """Verda Public API URL"""

        self.version: str = version
        """Current SDK Version"""
