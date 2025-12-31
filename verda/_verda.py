from verda._version import __version__
from verda.authentication import AuthenticationService
from verda.balance import BalanceService
from verda.clusters import ClustersService
from verda.constants import Constants
from verda.containers import ContainersService
from verda.http_client import HTTPClient
from verda.images import ImagesService
from verda.instance_types import InstanceTypesService
from verda.instances import InstancesService
from verda.locations import LocationsService
from verda.ssh_keys import SSHKeysService
from verda.startup_scripts import StartupScriptsService
from verda.volume_types import VolumeTypesService
from verda.volumes import VolumesService


class VerdaClient:
    """Client for interacting with Verda public API."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        base_url: str = 'https://api.verda.com/v1',
        inference_key: str | None = None,
    ) -> None:
        """Verda client.

        :param client_id: client id
        :type client_id: str
        :param client_secret: client secret
        :type client_secret: str
        :param base_url: base url for all the endpoints, optional, defaults to "https://api.verda.com/v1"
        :type base_url: str, optional
        :param inference_key: inference key, optional
        :type inference_key: str, optional
        """
        # Validate that client_id and client_secret are not empty
        if not client_id or not client_secret:
            raise ValueError('client_id and client_secret must be provided')

        # Constants
        self.constants: Constants = Constants(base_url, __version__)
        """Constants"""

        # Services
        self._authentication: AuthenticationService = AuthenticationService(
            client_id, client_secret, self.constants.base_url
        )
        self._http_client: HTTPClient = HTTPClient(self._authentication, self.constants.base_url)

        self.balance: BalanceService = BalanceService(self._http_client)
        """Balance service. Get client balance"""

        self.images: ImagesService = ImagesService(self._http_client)
        """Image service"""

        self.instance_types: InstanceTypesService = InstanceTypesService(self._http_client)
        """Instance type service"""

        self.instances: InstancesService = InstancesService(self._http_client)
        """Instances service. Deploy, delete, hibernate (etc) instances"""

        self.ssh_keys: SSHKeysService = SSHKeysService(self._http_client)
        """SSH keys service"""

        self.startup_scripts: StartupScriptsService = StartupScriptsService(self._http_client)
        """Startup Scripts service"""

        self.volume_types: VolumeTypesService = VolumeTypesService(self._http_client)
        """Volume type service"""

        self.volumes: VolumesService = VolumesService(self._http_client)
        """Volume service. Create, attach, detach, get, rename, delete volumes"""

        self.locations: LocationsService = LocationsService(self._http_client)
        """Locations service. Get locations"""

        self.containers: ContainersService = ContainersService(self._http_client, inference_key)
        """Containers service. Deploy, manage, and monitor container deployments"""

        self.clusters: ClustersService = ClustersService(self._http_client)
        """Clusters service. Create and manage compute clusters"""


__all__ = ['VerdaClient']
