---
name: python-sdk-patterns
description: Reference guide for sdk-python code conventions — models, services, tests, client wiring. Use when writing or modifying Python SDK code.
metadata:
  pattern: tool-wrapper
  domain: python-sdk
---

# Verda Cloud Python SDK Patterns

**Repo:** `tmp/sdk-python/`
**Package root:** `verda/`
**Test root:** `tests/unit_tests/`

---

## 1. Project Structure

```
verda/
  __init__.py              # Re-exports VerdaClient
  _verda.py                # VerdaClient class — wires all services together
  _version.py              # __version__ string
  constants.py             # Plain-class constants (Actions, Locations, etc.)
  exceptions.py            # APIException
  helpers.py               # stringify_class_object_properties, strip_none_values
  authentication/          # AuthenticationService (OAuth2 client credentials)
  http_client/             # HTTPClient wrapper around requests
  balance/                 # BalanceService (legacy manual model)
  images/                  # ImagesService (legacy manual model)
  instances/               # InstancesService (dataclass_json model)
  instance_types/          # InstanceTypesService (dataclass_json model)
  clusters/                # ClustersService (dataclass_json model)
  cluster_types/           # ClusterTypesService (dataclass_json model)
  containers/              # ContainersService (dataclass_json model, many sub-models)
  container_types/         # ContainerTypesService
  job_deployments/         # JobDeploymentsService (dataclass_json model)
  locations/               # LocationsService (raw dict pass-through)
  ssh_keys/                # SSHKeysService (legacy manual model)
  startup_scripts/         # StartupScriptsService (legacy manual model)
  volumes/                 # VolumesService (legacy manual model)
  volume_types/            # VolumeTypesService (legacy manual model)
  inference_client/        # InferenceClient for container deployment inference
```

Each service lives in its own package directory with:
- `_<service>.py` — model classes + service class
- `__init__.py` — re-exports public symbols

### Smart Scan Strategy

**Scope:** Only scan `verda/` and `examples/` (if examples need updating).

To build the full coverage map without reading every file:

```bash
# 1. Endpoint-to-file mapping (one grep)
grep -rn '_ENDPOINT\s*=' verda/

# 2. Method inventory per service
grep -rn 'def ' verda/<resource>/_<resource>.py

# 3. Model inventory per service
grep -rn 'class ' verda/<resource>/_<resource>.py
```

Three greps → complete lookup table for api-coverage.md.

---

## 2. Model Patterns

### 2a. `@dataclass_json` + `@dataclass` (preferred for new code)

Used by: **instances, clusters, containers, job_deployments, instance_types, cluster_types**

```python
from dataclasses import dataclass
from dataclasses_json import Undefined, dataclass_json

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class OSVolume:
    name: str
    size: int
    on_spot_discontinue: OnSpotDiscontinue | None = None

@dataclass_json
@dataclass
class Instance:
    id: str
    instance_type: str
    price_per_hour: float
    hostname: str
    description: str
    status: str
    created_at: str
    ssh_key_ids: list[str]
    cpu: dict
    gpu: dict
    memory: dict
    storage: dict
    gpu_memory: dict
    ip: str | None = None
    os_volume_id: str | None = None
    location: str = Locations.FIN_03
    image: str | None = None
    is_spot: bool = False
```

Key conventions:
- **Decorator order matters:** `@dataclass_json` on top, `@dataclass` below.
- Use `undefined=Undefined.EXCLUDE` when the API may return unknown fields you want to silently ignore.
- Omit `Undefined.EXCLUDE` when the model fields are exhaustive.
- Required fields first, optional fields (with defaults) after.
- Deserialization: `Instance.from_dict(data, infer_missing=True)` — `infer_missing=True` fills missing optional fields with defaults.
- Serialization: `instance.to_dict()`.
- Use `str | None` union syntax (Python 3.10+), not `Optional[str]`.

### 2b. Manual class with properties + `create_from_dict` (legacy)

Used by: **volumes, ssh_keys, startup_scripts, images, balance, volume_types**

```python
class Volume:
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
        self._id = id
        self._status = status
        self._name = name
        # ... store all as private attributes

    @property
    def id(self) -> str:
        return self._id

    @property
    def status(self) -> str:
        return self._status

    # ... read-only properties for every field

    @classmethod
    def create_from_dict(cls: 'Volume', volume_dict: dict) -> 'Volume':
        return cls(
            id=volume_dict['id'],
            status=volume_dict['status'],
            name=volume_dict['name'],
            # ... explicit key mapping
        )

    def __str__(self) -> str:
        return stringify_class_object_properties(self)
```

Key conventions:
- All attributes stored as `self._name` (private), exposed via read-only `@property`.
- Class method `create_from_dict(cls, data_dict)` handles deserialization (explicit key access, no `infer_missing`).
- `__str__` delegates to `helpers.stringify_class_object_properties(self)`.
- Some simpler legacy models (SSHKey, StartupScript) skip `create_from_dict` and construct directly in the service layer: `SSHKey(key['id'], key['name'], key['key'])`.

### 2c. Raw dict pass-through

Used by: **locations**

```python
class LocationsService:
    def __init__(self, http_client) -> None:
        self._http_client = http_client

    def get(self) -> list[dict]:
        locations = self._http_client.get(LOCATIONS_ENDPOINT).json()
        return locations
```

No model class at all. The API response dicts are returned as-is.

### When adding new models, use style (a). Only use manual classes if extending an existing service that uses that style.

---

## 3. Service Pattern

Every service follows this structure:

```python
INSTANCES_ENDPOINT = '/instances'

class InstancesService:
    def __init__(self, http_client) -> None:
        self._http_client = http_client

    def get(self, status: str | None = None) -> list[Instance]:
        instances_dict = self._http_client.get(
            INSTANCES_ENDPOINT, params={'status': status}
        ).json()
        return [
            Instance.from_dict(instance_dict, infer_missing=True)
            for instance_dict in instances_dict
        ]

    def get_by_id(self, id: str) -> Instance:
        instance_dict = self._http_client.get(
            INSTANCES_ENDPOINT + f'/{id}'
        ).json()
        return Instance.from_dict(instance_dict, infer_missing=True)

    def create(self, instance_type: str, image: str, ...) -> Instance:
        payload = { ... }
        id = self._http_client.post(INSTANCES_ENDPOINT, json=payload).text
        return self.get_by_id(id)

    def action(self, id_list: list[str] | str, action: str, ...) -> None:
        if type(id_list) is str:
            id_list = [id_list]
        payload = {'id': id_list, 'action': action}
        self._http_client.put(INSTANCES_ENDPOINT, json=payload)
        return
```

Key conventions:
- Endpoint constant is a module-level `UPPER_SNAKE_CASE` string (relative path, no base URL).
- Constructor takes `http_client` (or `http_client: HTTPClient` with type hint). Store as `self._http_client`.
- Exception: `ContainersService` stores it as `self.client` (not `self._http_client`) and also takes `inference_key`.
- Methods return model objects, not raw dicts (except locations).
- Void actions (`delete`, `action`, etc.) return `None` explicitly with bare `return`.

---

## 4. HTTP Client Methods

All methods live on `HTTPClient` and return `requests.Response`. Error handling (status >= 400) is automatic via `handle_error()` which raises `APIException`.

| Method   | Signature                                                                 |
|----------|---------------------------------------------------------------------------|
| `get`    | `get(self, url: str, params: dict \| None = None, **kwargs)`             |
| `post`   | `post(self, url: str, json: dict \| None = None, params: dict \| None = None, **kwargs)` |
| `put`    | `put(self, url: str, json: dict \| None = None, params: dict \| None = None, **kwargs)` |
| `patch`  | `patch(self, url: str, json: dict \| None = None, params: dict \| None = None, **kwargs)` |
| `delete` | `delete(self, url: str, json: dict \| None = None, params: dict \| None = None, **kwargs)` |

Notes:
- `url` is always the relative path (e.g. `/instances`). `HTTPClient._add_base_url()` prepends the base URL.
- `json=` parameter is the request body (dict). Some services pass positional dict instead of `json=` keyword (containers: `self.client.post(URL, deployment.to_dict())`).
- All methods refresh the auth token if expired before making the request.
- Error responses (status >= 400) raise `APIException(code, message)` automatically.

---

## 5. Client Wiring (`_verda.py`)

To add a new service:

1. **Create the service package** (e.g. `verda/new_service/`):
   - `_new_service.py` with model classes and `NewServiceService` class
   - `__init__.py` re-exporting public symbols

2. **Import in `_verda.py`**:
   ```python
   from verda.new_service import NewServiceService
   ```

3. **Add attribute in `VerdaClient.__init__`**:
   ```python
   self.new_service: NewServiceService = NewServiceService(self._http_client)
   """New service description"""
   ```

4. **Update top-level `verda/__init__.py`** if the service or its models should be importable from `verda` directly (currently only `VerdaClient` and `__version__` are exported at the top level).

The `VerdaClient.__init__` signature:
```python
def __init__(
    self,
    client_id: str,
    client_secret: str,
    base_url: str = 'https://api.verda.com/v1',
    inference_key: str | None = None,
) -> None:
```

Services are plain attributes on the client (no lazy loading, no registry).

---

## 6. Method Naming -- INCONSISTENT across services

| Service                | List all            | Get one               | Create                       | Delete                         | Other actions                    |
|------------------------|---------------------|-----------------------|------------------------------|--------------------------------|----------------------------------|
| `InstancesService`     | `get(status)`       | `get_by_id(id)`       | `create(...)`                | via `action(ids, 'delete')`    | `action(ids, action)`, `is_available()`, `get_availabilities()` |
| `VolumesService`       | `get(status)`       | `get_by_id(id)`       | `create(...)`                | `delete(ids)`                  | `attach()`, `detach()`, `clone()`, `rename()`, `increase_size()`, `get_in_trash()` |
| `ClustersService`      | `get(status)`       | `get_by_id(id)`       | `create(...)`                | `delete(id)` / `action(ids, action)` | `is_available()`, `get_availabilities()`, `get_cluster_images()` |
| `ContainersService`    | `get_deployments()` | `get_deployment_by_name(name)` | `create_deployment(d)` | `delete_deployment(name)`      | `update_deployment()`, `restart_deployment()`, `pause/resume_deployment()`, secrets, registry creds, env vars, scaling, replicas |
| `JobDeploymentsService`| `get()`             | `get_by_name(name)`   | `create(d)`                  | `delete(name)`                 | `update()`, `get_status()`, `pause()`, `resume()`, `purge_queue()`, `get_scaling_options()` |
| `SSHKeysService`       | `get()`             | `get_by_id(id)`       | `create(name, key)`          | `delete(ids)` / `delete_by_id(id)` | -- |
| `StartupScriptsService`| `get()`             | `get_by_id(id)`       | `create(name, script)`       | `delete(ids)` / `delete_by_id(id)` | -- |
| `InstanceTypesService` | `get(currency)`     | --                    | --                           | --                             | -- |
| `LocationsService`     | `get()`             | --                    | --                           | --                             | -- |

**When adding to an existing service, match its style. New services should use the short style: `get`, `get_by_id` (or `get_by_name`), `create`, `delete`.**

---

## 7. Constants Pattern

Constants in `constants.py` use plain classes with class-level attributes (not Enums):

```python
class Actions:
    START = 'start'
    SHUTDOWN = 'shutdown'
    DELETE = 'delete'
    HIBERNATE = 'hibernate'
    RESTORE = 'restore'

    def __init__(self):
        return

class Locations:
    FIN_01: str = 'FIN-01'
    FIN_02: str = 'FIN-02'
    FIN_03: str = 'FIN-03'
    ICE_01: str = 'ICE-01'

    def __init__(self):
        return
```

All constant classes have a no-op `__init__`. They are instantiated in the `Constants` class and exposed on `VerdaClient.constants`.

**Container-specific enums** use `class Name(str, Enum)` instead (defined in `containers/_containers.py`):

```python
from enum import Enum

class EnvVarType(str, Enum):
    PLAIN = 'plain'
    SECRET = 'secret'

class ContainerDeploymentStatus(str, Enum):
    INITIALIZING = 'initializing'
    HEALTHY = 'healthy'
    DEGRADED = 'degraded'
    # ...
```

Also in `job_deployments/_job_deployments.py`:
```python
class JobDeploymentStatus(str, Enum):
    PAUSED = 'paused'
    TERMINATING = 'terminating'
    RUNNING = 'running'
```

**Literal types** are used for constrained string parameters (not for constants):
```python
from typing import Literal
Contract = Literal['LONG_TERM', 'PAY_AS_YOU_GO', 'SPOT']
Currency = Literal['usd', 'eur']
```

---

## 8. Polymorphic Parameters

Services that accept either a single ID or a list of IDs use `str | list[str]` and normalize at the top of the method:

```python
def action(self, id_list: list[str] | str, action: str, ...) -> None:
    if type(id_list) is str:
        id_list = [id_list]
    payload = {'id': id_list, 'action': action}
    self._http_client.put(INSTANCES_ENDPOINT, json=payload)
```

Note: uses `type(id_list) is str` (identity check), not `isinstance()`. This is the established pattern; keep it consistent when extending existing services.

Clusters service uses `isinstance()` instead:
```python
if isinstance(id_list, str):
    payload = {'actions': [{'id': id_list, 'action': action}]}
else:
    payload = {'actions': [{'id': id, 'action': action} for id in id_list]}
```

---

## 9. POST Returning Plain Text ID

When a POST endpoint returns a plain-text ID (not JSON), the pattern is:

```python
def create(self, type: str, name: str, size: int, ...) -> Volume:
    payload = { ... }
    id = self._http_client.post(VOLUMES_ENDPOINT, json=payload).text
    volume = self.get_by_id(id)
    return volume
```

Used by: instances, volumes, ssh_keys, startup_scripts.

Some services return JSON from POST instead (containers, job_deployments, clusters):
```python
def create_deployment(self, deployment: Deployment) -> Deployment:
    response = self.client.post(CONTAINER_DEPLOYMENTS_ENDPOINT, deployment.to_dict())
    return Deployment.from_dict_with_inference_key(response.json(), self._inference_key)
```

```python
# clusters - POST returns JSON with 'id' field
response = self._http_client.post(CLUSTERS_ENDPOINT, json=payload).json()
id = response['id']
```

---

## 10. Test Pattern

Tests use `pytest` + `responses` library for HTTP mocking.

### Shared fixtures (`tests/unit_tests/conftest.py`)

```python
from unittest.mock import Mock
import pytest
from verda.http_client import HTTPClient

BASE_URL = 'https://api.example.com/v1'
ACCESS_TOKEN = 'test-token'
CLIENT_ID = '0123456789xyz'
CLIENT_SECRET = '0123456789xyz'

@pytest.fixture
def http_client():
    auth_service = Mock()
    auth_service._access_token = ACCESS_TOKEN
    auth_service.is_expired = Mock(return_value=True)
    auth_service.refresh = Mock(return_value=None)
    auth_service._client_id = CLIENT_ID
    auth_service._client_secret = CLIENT_SECRET
    return HTTPClient(auth_service, BASE_URL)
```

### Standard test class structure

```python
import pytest
import responses
from responses import matchers

from verda.constants import Actions, ErrorCodes
from verda.exceptions import APIException
from verda.instances import Instance, InstancesService

INSTANCE_ID = 'deadc0de-a5d2-4972-ae4e-d429115d055b'
PAYLOAD = [{ ... }]  # response fixture data

class TestInstancesService:
    @pytest.fixture
    def instances_service(self, http_client):
        return InstancesService(http_client)

    @pytest.fixture
    def endpoint(self, http_client):
        return http_client._base_url + '/instances'

    @responses.activate
    def test_get_instances(self, instances_service, endpoint):
        # arrange
        responses.add(responses.GET, endpoint, json=PAYLOAD, status=200)

        # act
        instances = instances_service.get()
        instance = instances[0]

        # assert
        assert isinstance(instances, list)
        assert isinstance(instance, Instance)
        assert instance.id == INSTANCE_ID
        assert responses.assert_call_count(endpoint, 1) is True

    @responses.activate
    def test_get_instances_failed(self, instances_service, endpoint):
        # arrange
        responses.add(
            responses.GET,
            endpoint + '?status=invalid',
            json={'code': 'invalid_request', 'message': 'Bad status'},
            status=400,
        )

        # act + assert
        with pytest.raises(APIException) as excinfo:
            instances_service.get(status='invalid')

        assert excinfo.value.code == 'invalid_request'
        assert excinfo.value.message == 'Bad status'

    @responses.activate
    def test_create_instance(self, instances_service, endpoint):
        # arrange - POST returns plain text ID, then GET returns the object
        responses.add(responses.POST, endpoint, body=INSTANCE_ID, status=200)
        responses.add(
            responses.GET,
            endpoint + '/' + INSTANCE_ID,
            json=PAYLOAD[0],
            status=200,
        )

        # act
        instance = instances_service.create(
            instance_type='1V100.6V',
            image='ubuntu-24.04-cuda-12.8-open-docker',
            hostname='test',
            description='test instance',
        )

        # assert
        assert isinstance(instance, Instance)
        assert responses.assert_call_count(endpoint, 1) is True
```

### Request body matching with `matchers`

```python
from responses import matchers

@responses.activate
def test_attach_volume(self, volumes_service, endpoint):
    responses.add(
        responses.PUT,
        endpoint,
        status=202,
        match=[
            matchers.json_params_matcher({
                'id': VOLUME_ID,
                'action': VolumeActions.ATTACH,
                'instance_id': INSTANCE_ID,
            })
        ],
    )

    result = volumes_service.attach(VOLUME_ID, INSTANCE_ID)
    assert result is None
    assert responses.assert_call_count(endpoint, 1) is True
```

Key conventions:
- **Every test method** in the test file must be decorated with `@responses.activate`.
- Use `responses.add(METHOD, url, json=..., status=...)` for JSON responses.
- Use `responses.add(METHOD, url, body=..., status=...)` for plain text responses (e.g. POST returning ID).
- Use `responses.assert_call_count(url, N)` to verify the correct number of API calls.
- Use `pytest.raises(APIException)` for error scenarios, checking both `.code` and `.message`.
- Use `matchers.json_params_matcher(expected_dict)` in the `match=` parameter to assert request body contents.
- Test classes follow `Test<ServiceName>Service` naming.
- Module-level constants define fixture data (IDs, payloads).
- Each test class has its own `service` and `endpoint` fixtures.
- Tests follow arrange/act/assert pattern with comments.

---

## 11. Module `__init__.py` Pattern

Each service package exports its service class and model classes:

```python
# verda/instances/__init__.py
from ._instances import (
    Contract,
    Instance,
    InstancesService,
    OnSpotDiscontinue,
    OSVolume,
    Pricing,
)
```

```python
# verda/volumes/__init__.py
from ._volumes import Volume, VolumesService
```

```python
# verda/containers/__init__.py
from ._containers import (
    AWSECRCredentials,
    BaseRegistryCredentials,
    ComputeResource,
    Container,
    ContainerDeploymentStatus,
    ContainerRegistryCredentials,
    ContainerRegistrySettings,
    ContainerRegistryType,
    ContainersService,
    CustomRegistryCredentials,
    Deployment,
    DockerHubCredentials,
    # ... all public model classes
)
```

The top-level `verda/__init__.py` only re-exports the client:
```python
from verda._verda import VerdaClient
from verda._version import __version__

__all__ = ['VerdaClient']
```

Convention: imports use the private module name (`._instances`), and every public class in the module must be listed in the `__init__.py` import.
