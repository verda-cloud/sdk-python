# Compatibility layer for deprecated `datacrunch` package

from verda import VerdaClient as DataCrunchClient
from verda import (
    __version__,
    authentication,
    balance,
    cluster_types,
    constants,
    container_types,
    containers,
    exceptions,
    helpers,
    http_client,
    images,
    instance_types,
    instances,
    job_deployments,
    locations,
    long_term,
    ssh_keys,
    startup_scripts,
    volume_types,
    volumes,
)
from verda import inference_client as Inference_client

# For old `from datacrunch import *``
__all__ = [
    'DataCrunchClient',
    'Inference_client',
    '__version__',
    'authentication',
    'balance',
    'cluster_types',
    'constants',
    'container_types',
    'containers',
    'datacrunch',
    'exceptions',
    'helpers',
    'http_client',
    'images',
    'instance_types',
    'instances',
    'job_deployments',
    'locations',
    'long_term',
    'ssh_keys',
    'startup_scripts',
    'volume_types',
    'volumes',
]

import warnings

warnings.warn(
    'datacrunch is deprecated; use verda package instead: https://github.com/verda-cloud/sdk-python/blob/master/MIGRATION.md',
    DeprecationWarning,
    stacklevel=2,
)
