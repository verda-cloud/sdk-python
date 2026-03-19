# Compatibility layer for deprecated `datacrunch.datacrunch` package

from verda import VerdaClient as DataCrunchClient
from verda._version import __version__
from verda.authentication import AuthenticationService
from verda.balance import BalanceService
from verda.cluster_types import ClusterTypesService
from verda.constants import Constants
from verda.container_types import ContainerTypesService
from verda.containers import ContainersService
from verda.http_client import HTTPClient
from verda.images import ImagesService
from verda.instance_types import InstanceTypesService
from verda.instances import InstancesService
from verda.job_deployments import JobDeploymentsService
from verda.locations import LocationsService
from verda.long_term import LongTermService
from verda.ssh_keys import SSHKeysService
from verda.startup_scripts import StartupScriptsService
from verda.volume_types import VolumeTypesService
from verda.volumes import VolumesService

# for `from datacrunch.datacrunch import *`
__all__ = [
    'AuthenticationService',
    'BalanceService',
    'ClusterTypesService',
    'Constants',
    'ContainerTypesService',
    'ContainersService',
    'DataCrunchClient',
    'HTTPClient',
    'ImagesService',
    'InstanceTypesService',
    'InstancesService',
    'JobDeploymentsService',
    'LocationsService',
    'LongTermService',
    'SSHKeysService',
    'StartupScriptsService',
    'VolumeTypesService',
    'VolumesService',
    '__version__',
]
