# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.19.0] - 2025-02-05

### Added

- Add `on_spot_discontinue` parameter for instance OS volumes. Previously the policy was always `'keep_detached'`, now it can be set to `'move_to_trash'` or `'delete_permanently'`:
    ```python
    instance = verda_client.instances.create(
        hostname='test-instance',
        location=Locations.FIN_03,
        instance_type='CPU.4V.16G',
        description='test cpu instance',
        image='ubuntu-22.04',
        is_spot=True,
        ssh_key_ids=[ssh_key.id],
        os_volume=OSVolume(
            name='test-os-volume-spot',
            size=56,
            on_spot_discontinue='delete_permanently',
        ),
    )
    ```
- Add `delete_permanently` parameter for instance delete action. When set, `volume_ids` will be deleted in one go, skipping trash:
    ```python
    verda.instances.action(
        instance.id, 'delete',
        volume_ids=[instance.os_volume_id],
        delete_permanently=True,
    )
    ```

## [1.18.0] - 2025-12-31

### Added

- Add shared_volumes attribute to Cluster class

## [1.18.0] - 2025-12-31

### Added

- Clusters support

## [1.17.4] - 2025-11-28

### Added

- Add `datacrunch` -> `verda` migration guide

## [1.17.3] - 2025-11-27

### Fixed

- `datacrunch`: fix imports from `datacrunch.instances.instances` and other similar modules

### Changed

- `verda`: removed repeating submodules like `.instances.instances`.
- `verda`: renamed `.InferenceClient.inference_client` module to `.inference_client`.

Was:

```python
from datacrunch.instances.instances import InstancesService
from datacrunch.InferenceClient.inference_client import InferenceClient
```

Now:

```python
from verda.instances import InstancesService
from verda.inference_client import InferenceClient
```

## [1.17.2] - 2025-11-27

### Fixed

- Fix imports from `datacrunch.*` modules

## [1.17.1] - 2025-11-27

### Changed

- `datacrunch` package now imports `verda`, tracking its releases
- Moved `DataCrunchClient` and `.datacrunch` sub-module into compatibility `datacrunch` package

## [1.17.0] - 2025-11-26

### Highlights

- `datacrunch` package is now `verda`, because [DataCrunch company changed its name to Verda](https://verda.com/blog/datacrunch-is-changing-its-name-to-verda). Original `datacrunch` package is deprecated, but it would continue tracking `verda` releases.

### Deprecated

- `DataCrunchClient` and `datacrunch` are deprecated, please change your imports to `VerdaClient` and `verda`.

Was:

```shell
uv add datacrunch
pip install datacrunch
```

```python
from datacrunch import DataCrunchClient

datacrunch = DataCrunchClient(...)
datacrunch.instances.create(...)
```

Now:

```shell
uv add verda
pip install verda
```

```python
from verda import VerdaClient

verda = VerdaClient(...)
verda.instances.create(...)
```

### Added

- Added shared filesystem (SFS) type constant and example

### Changed

- Refactor `instance_types.py` to use dataclass
- Put back support for Python 3.10
- Default API base URL is now `https://api.verda.com/v1`

## [1.16.0] - 2025-10-27

### Changed

- Changed default datacenter location to `FIN-03`
- Migrated to `uv`
- Removed `datacrunch.__version__.VERSION`. Use standard [importlib.metadata.version()](https://docs.python.org/3/library/importlib.metadata.html#importlib.metadata.version) instead:
  ```python
  from importlib.metadata import version
  print(version('datacrunch'))
  ```
- Migrated to Ruff for linting
- Upgraded pytest

If you are working on the library itself, do a fresh clone or upgrade your local development environment in-place:
  ```bash
  # remove old environment
  rm -rf datacrunch.egg-info/ .venv/ datacrunch_env/

  # create new environment and install dependencies
  uv sync

  # run example
  uv run python examples/simple_create_instance.py
  ```

### Added

- Added constants for `FIN-02` and `FIN-03`.

## [1.15.0] - 2025-10-23

### Added

- Added `max_wait_time`, `initial_interval`, `max_interval`, `backoff_coefficient` keyword arguments to `instances.create()`

### Changed

- Cap `instances.create()` retry interval to 5 seconds; add exponential backoff; increase default `max_wait_time` from 60 to 180 seconds

## [1.14.0] - 2025-08-15

### Added

- Added `SharedFileSystemMount` class for container sfs support
- Added `SecretMount` and `GeneralStorageMount` classes that inherit from base `VolumeMount`

### Changed

- Removed support for python 3.9 as it doesn't support `kw_only` and reaches EOS state in 2 months

## [1.13.2] - 2025-06-04

### Changed

- Add `SecretMount` class for container deployments

## [1.13.1] - 2025-05-22

### Changed

- Trigger publish package github action only when a released is published
- Async inference example: longer `sleep()` duration when polling for inference status

### Fixed

- Removed a forgotten and redundant `print`

## [1.13.0] - 2025-05-21

### Changed

- This file and CONTRIBUTING.rst to markdown
- Updated inference status enum from numerical to meaningful string values

### Fixed

- Github action publish package release trigger value

## [1.12.1] - 2025-05-13

### Fixed

- Inference examples docs generation

### Changed

- Inference status enum from numerical to meaningful string values

## [1.12.0] - 2025-05-12

### Added

- Support for fileset secrets

## [1.11.0] - 2025-04-28

### Added

- Example for calling the inference endpoint with a minimal client
- Missing doc generation for inference examples

### Changed

- Refactored instances.py to use dataclasses and google docstring style

## [1.10.0] - 2025-04-17

### Changed

- Updated version for release

## [1.9.1] - 2025-04-17

### Added

- Inference client to run inference requests and get status and results
- Support for asynchronous inference

## [1.9.0] - 2025-04-04

### Added

- Environment variables to container deployment example
- `size_in_mb` parameter to `VolumeMount` class
- Memory volume mount type

### Changed

- Updated examples image from `fastai` to `ubuntu-24.04-cuda-12.8-open-docker`
- Consistent naming and load of credentials from env variables in examples

## [1.8.4] - 2025-03-25

### Added

- Readthedocs configuration file

## [1.8.3] - 2025-03-25

### Changed

- Updated documentation

## [1.8.2] - 2025-03-25

### Added

- Missing packages to setup requirements

## [1.8.1] - 2025-03-24 [YANKED]

### Removed

- Container name from deployment creation

## [1.8.0] - 2025-03-24 [YANKED]

### Added

- Support for containers

## [1.7.3] - 2025-03-07

### Fixed

- Type for contract and pricing parameters

## [1.7.1] - 2025-03-06

### Added

- Contract and pricing parameters in `datacrunch.instances.create()`

## [1.7.0] - 2024-11-21

### Fixed

- Methods `volumes.increase_size()` and `volumes.get()`

## [1.6.1] - 2023-10-02

### Added

- Spot price to instance types

## [1.6.0] - 2023-09-15

### Added

- Locations endpoint and location code parameter to the availability endpoints

## [1.5.0] - 2023-06-28

### Added

- Location constants

### Changed

- Refactored the code to send `location_code` instead of `location` when creating an instance or a volume

## [1.4.1] - 2023-06-20

### Fixed

- Bug where token refresh failed

## [1.4.0] - 2023-06-14

### Added

- Support for permanent deletion of volumes
- Volume class method that inits a new Volume instance from a dict
- Integration tests for permanent deletion of volumes

## [1.3.0] - 2023-05-25

### Added

- Support for volume cloning

## [1.2.0] - 2023-04-24

### Added

- Support for deploying a new instance with existing volumes

## [1.1.2] - 2023-03-02

### Fixed

- Bug where the wrong property name was used

## [1.1.1] - 2023-02-23

### Fixed

- Bug where the authentication refresh token flow did not update the token values

## [1.1.0] - 2023-01-20

### Added

- Support for checking availability for a spot instance

### Changed

- Updated two github actions to run on fixed version of ubuntu because the latest one is missing python 3.6
- Added more versions of python to be used on two github actions

## [1.0.10] - 2022-10-18

### Added

- Support for adding a coupon code when deploying a new instance

## [1.0.9] - 2022-09-16

### Added

- `is_spot` property to the `Instance` class, now possible to deploy a spot instance
- Implemented `__str__` method for `Instance`, `Volume` and `Image` Classes, now possible to print instances

## [1.0.8] - 2021-12-20

### Added

- `ssh_key_ids` property for Volume entity
- Test coverage for `ssh_key_ids`

## [1.0.7] - 2021-10-13

### Fixed

- The previous bug in a different method

## [1.0.6] - 2021-10-12

### Fixed

- Bug where initializing an instance without ssh keys raises an exception

## [1.0.5] - 2021-09-27

### Added

- Option to set OS volume size and name on instance creation

## [1.0.4] - 2021-07-01

### Added

- Constants documentation

## [1.0.3] - 2021-07-01

### Added

- Missing volumes documentation

## [1.0.2] - 2021-06-16

### Added

- Examples to documentation

## [1.0.1] - 2021-06-16

### Changed

- Updated version

## [1.0.0] - 2021-06-16

### Added

- Support for storage volumes

### Changed

- Breaking change: moved all constants under DataCrunchClient to DataCrunchClient.constants

## [0.1.0] - 2021-01-05

### Added

- First release, still in beta.

[unreleased]: https://github.com/DataCrunch-io/datacrunch-python/compare/v1.12.1...HEAD
[1.12.1]: https://github.com/DataCrunch-io/datacrunch-python/compare/v1.12.0...v1.12.1
[1.12.0]: https://github.com/DataCrunch-io/datacrunch-python/compare/v1.11.0...v1.12.0
[1.11.0]: https://github.com/DataCrunch-io/datacrunch-python/compare/v1.10.0...v1.11.0
[1.10.0]: https://github.com/DataCrunch-io/datacrunch-python/compare/v1.9.1...v1.10.0
[1.9.1]: https://github.com/DataCrunch-io/datacrunch-python/compare/v1.9.0...v1.9.1
[1.9.0]: https://github.com/DataCrunch-io/datacrunch-python/compare/v1.8.4...v1.9.0
[1.8.4]: https://github.com/DataCrunch-io/datacrunch-python/compare/v1.8.3...v1.8.4
[1.8.3]: https://github.com/DataCrunch-io/datacrunch-python/compare/v1.8.2...v1.8.3
[1.8.2]: https://github.com/DataCrunch-io/datacrunch-python/compare/v1.8.1...v1.8.2
[1.8.1]: https://github.com/DataCrunch-io/datacrunch-python/compare/v1.8.0...v1.8.1
[1.8.0]: https://github.com/DataCrunch-io/datacrunch-python/compare/v1.7.3...v1.8.0
[1.7.3]: https://github.com/DataCrunch-io/datacrunch-python/compare/v1.7.1...v1.7.3
[1.7.1]: https://github.com/DataCrunch-io/datacrunch-python/compare/v1.7.0...v1.7.1
[1.7.0]: https://github.com/DataCrunch-io/datacrunch-python/compare/v1.6.1...v1.7.0
[1.6.1]: https://github.com/DataCrunch-io/datacrunch-python/compare/v1.6.0...v1.6.1
[1.6.0]: https://github.com/DataCrunch-io/datacrunch-python/compare/v1.5.0...v1.6.0
[1.5.0]: https://github.com/DataCrunch-io/datacrunch-python/compare/v1.4.1...v1.5.0
[1.4.1]: https://github.com/DataCrunch-io/datacrunch-python/compare/v1.4.0...v1.4.1
[1.4.0]: https://github.com/DataCrunch-io/datacrunch-python/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/DataCrunch-io/datacrunch-python/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/DataCrunch-io/datacrunch-python/compare/v1.1.2...v1.2.0
[1.1.2]: https://github.com/DataCrunch-io/datacrunch-python/compare/v1.1.1...v1.1.2
[1.1.1]: https://github.com/DataCrunch-io/datacrunch-python/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/DataCrunch-io/datacrunch-python/compare/v1.0.10...v1.1.0
[1.0.10]: https://github.com/DataCrunch-io/datacrunch-python/compare/v1.0.9...v1.0.10
[1.0.9]: https://github.com/DataCrunch-io/datacrunch-python/compare/v1.0.8...v1.0.9
[1.0.8]: https://github.com/DataCrunch-io/datacrunch-python/compare/v1.0.7...v1.0.8
[1.0.7]: https://github.com/DataCrunch-io/datacrunch-python/compare/v1.0.6...v1.0.7
[1.0.6]: https://github.com/DataCrunch-io/datacrunch-python/compare/v1.0.5...v1.0.6
[1.0.5]: https://github.com/DataCrunch-io/datacrunch-python/compare/v1.0.4...v1.0.5
[1.0.4]: https://github.com/DataCrunch-io/datacrunch-python/compare/v1.0.3...v1.0.4
[1.0.3]: https://github.com/DataCrunch-io/datacrunch-python/compare/v1.0.2...v1.0.3
[1.0.2]: https://github.com/DataCrunch-io/datacrunch-python/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/DataCrunch-io/datacrunch-python/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/DataCrunch-io/datacrunch-python/compare/v0.1.0...v1.0.0
[0.1.0]: https://github.com/DataCrunch-io/datacrunch-python/releases/tag/v0.1.0
