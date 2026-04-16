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
    'SSHKeysService',
    'StartupScriptsService',
    'VolumeTypesService',
    'VolumesService',
    '__version__',
]
