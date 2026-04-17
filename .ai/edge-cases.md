# Python SDK Implementation Edge Cases

Non-obvious patterns discovered from the real Python SDK codebase. Check these
before writing SDK code -- the OpenAPI spec does not surface these behaviors.

## POST Endpoints Returning Plain Text IDs

Some POST endpoints return a plain text ID string instead of JSON. The SDK
reads `.text` from the response and then fetches the full object.

**Affected services:** InstancesService.create(), VolumesService.create(),
SSHKeysService.create(), StartupScriptsService.create()

**Pattern:**

```python
# instances/_instances.py — create returns plain text ID, then fetches object
id = self._http_client.post(INSTANCES_ENDPOINT, json=payload).text
return self.get_by_id(id)

# volumes/_volumes.py — same pattern
id = self._http_client.post(VOLUMES_ENDPOINT, json=payload).text
volume = self.get_by_id(id)
return volume

# ssh_keys/_ssh_keys.py — constructs object directly (no re-fetch)
id = self._http_client.post(SSHKEYS_ENDPOINT, json=payload).text
return SSHKey(id, name, key)
```

**Not affected:** ClustersService.create() returns JSON with `response.json()['id']`.
ContainersService.create_deployment() returns full JSON object.

## Three Model Serialization Styles

The SDK uses three different model patterns. **Always match the existing style**
when modifying a service.

### Style 1: dataclass_json (from_dict with infer_missing)

Uses `@dataclass_json` + `@dataclass` decorators. Deserialized via
`Model.from_dict(data, infer_missing=True)`.

**Models:** Instance, Cluster, ClusterWorkerNode, SharedVolume, Deployment,
JobDeployment, JobDeploymentSummary, InstanceType, ClusterType, all Container
dataclasses (Container, HealthcheckSettings, ScalingOptions, etc.)

```python
# instances/_instances.py
@dataclass_json
@dataclass
class Instance:
    id: str
    instance_type: str
    ...

# Deserialization
Instance.from_dict(instance_dict, infer_missing=True)
```

### Style 2: Manual class with create_from_dict or constructor

Plain classes with `__init__`, `@property` accessors, and private `_field`
storage. Some have a `create_from_dict` classmethod; others construct inline.

**Models with create_from_dict:** Volume

```python
# volumes/_volumes.py
class Volume:
    def __init__(self, id, status, name, size, ...):
        self._id = id
        ...

    @classmethod
    def create_from_dict(cls, volume_dict):
        return cls(
            id=volume_dict['id'],
            status=volume_dict['status'],
            ...
        )

# Deserialization
Volume.create_from_dict(volume_dict)
```

**Models constructed inline:** SSHKey, StartupScript, Image, Balance, VolumeType

```python
# ssh_keys/_ssh_keys.py — constructed field-by-field in service methods
keys = [SSHKey(key['id'], key['name'], key['key']) for key in keys]

# balance/_balance.py
Balance(balance['amount'], balance['currency'])
```

### Style 3: Raw dict (no model)

**Services:** LocationsService

```python
# locations/_locations.py
def get(self) -> list[dict]:
    locations = self._http_client.get(LOCATIONS_ENDPOINT).json()
    return locations
```

## Single-Item Lookup Returning Array

Some GET-by-ID endpoints return a JSON array. The SDK unwraps with `[0]`.

**Affected:** SSHKeysService.get_by_id(), StartupScriptsService.get_by_id()

```python
# ssh_keys/_ssh_keys.py
def get_by_id(self, id: str) -> SSHKey:
    key_dict = self._http_client.get(SSHKEYS_ENDPOINT + f'/{id}').json()[0]
    key_object = SSHKey(key_dict['id'], key_dict['name'], key_dict['key'])
    return key_object

# startup_scripts/_startup_scripts.py
def get_by_id(self, id) -> StartupScript:
    script = self._http_client.get(STARTUP_SCRIPTS_ENDPOINT + f'/{id}').json()[0]
    return StartupScript(script['id'], script['name'], script['script'])
```

**Not affected:** InstancesService.get_by_id(), VolumesService.get_by_id(),
ClustersService.get_by_id() -- these return a single JSON object.

## Polymorphic ID Parameters

Several action methods accept `str | list[str]`. The service normalizes to list
internally using `type()` check (not `isinstance()`).

**Affected:** InstancesService.action(), VolumesService.attach/detach/rename/
increase_size/delete

```python
# instances/_instances.py
def action(self, id_list: list[str] | str, action: str, ...) -> None:
    if type(id_list) is str:
        id_list = [id_list]
    payload = {'id': id_list, 'action': action, ...}
    self._http_client.put(INSTANCES_ENDPOINT, json=payload)
```

**Exception:** ClustersService.action() uses `isinstance()` and builds a
different payload structure with an `actions` array:

```python
# clusters/_clusters.py
if isinstance(id_list, str):
    payload = {'actions': [{'id': id_list, 'action': action}]}
else:
    payload = {'actions': [{'id': id, 'action': action} for id in id_list]}
```

## Action-Based Mutations via PUT

Instance and Volume mutations use PUT with an action payload instead of
resource-specific endpoints. The action string determines the operation.

**Pattern:**

```python
# volumes/_volumes.py — all mutations go through PUT /volumes
payload = {'id': id_list, 'action': VolumeActions.ATTACH, 'instance_id': instance_id}
self._http_client.put(VOLUMES_ENDPOINT, json=payload)

# instances/_instances.py — same pattern for instance actions
payload = {'id': id_list, 'action': action, ...}
self._http_client.put(INSTANCES_ENDPOINT, json=payload)
```

**Cluster mutations** use a different structure with an `actions` array (see
Polymorphic ID Parameters above).

## SSH Keys Endpoint Path

SSHKeysService uses the deprecated `/sshkeys` path (no hyphen).

```python
# ssh_keys/_ssh_keys.py
SSHKEYS_ENDPOINT = '/sshkeys'
```

The OpenAPI spec uses `/ssh-keys`. When syncing, do NOT change the endpoint
path unless explicitly instructed -- the old path still works and changing it
is a breaking change for users.

## Exponential Backoff Polling

InstancesService.create() and ClustersService.create() include inline
exponential backoff polling to wait for provisioning status.

```python
# instances/_instances.py — backoff polling loop
deadline = time.monotonic() + max_wait_time
for i in itertools.count():
    instance = self.get_by_id(id)
    if callable(wait_for_status):
        if wait_for_status(instance.status):
            return instance
    elif instance.status == wait_for_status:
        return instance

    now = time.monotonic()
    if now >= deadline:
        raise TimeoutError(...)

    interval = min(initial_interval * backoff_coefficient**i, max_interval, deadline - now)
    time.sleep(interval)
```

**Key differences between Instance and Cluster polling:**
- Instance: `wait_for_status` can be a `str` or `Callable[[str], bool]`; default is `lambda s: s != InstanceStatus.ORDERED`
- Cluster: `wait_for_status` is `str | None` only; also checks for ERROR and DISCONTINUED states, raising `APIException`

**Do NOT** add backoff polling to new endpoints unless the API returns an
async/provisioning status that requires it. There is a TODO comment in both
files to extract the shared backoff logic.

## ContainersService Uses self.client (Not self._http_client)

ContainersService stores the HTTP client as `self.client` instead of
`self._http_client` like every other service.

```python
# containers/_containers.py
class ContainersService:
    def __init__(self, http_client: HTTPClient, inference_key: str | None = None) -> None:
        self.client = http_client          # <-- public attribute, not _http_client
        self._inference_key = inference_key

    def get_deployments(self) -> list[Deployment]:
        response = self.client.get(CONTAINER_DEPLOYMENTS_ENDPOINT)
        ...
```

**All other services** use `self._http_client`:

```python
class InstancesService:
    def __init__(self, http_client) -> None:
        self._http_client = http_client
```

When adding methods to ContainersService, use `self.client`. When adding
methods to any other service, use `self._http_client`.

## strip_none_values Helper

JobDeploymentsService uses `strip_none_values()` from `verda.helpers` to clean
`None` values from dataclass-serialized payloads before sending to the API.

```python
# job_deployments/_job_deployments.py
from verda.helpers import strip_none_values

def create(self, deployment: JobDeployment) -> JobDeployment:
    response = self._http_client.post(
        JOB_DEPLOYMENTS_ENDPOINT,
        json=strip_none_values(deployment.to_dict()),
    )
    ...
```

This is needed because `dataclass_json.to_dict()` includes `None` values for
optional fields, and some API endpoints reject unexpected `null` values.
**Only** JobDeploymentsService uses this pattern currently. Use it for new
services that send dataclass payloads with optional fields.

## InstanceType Price Fields — Manual float() Conversion

InstanceTypesService.get() manually converts price fields from strings to
floats during deserialization, despite InstanceType being a `@dataclass_json`
model.

```python
# instance_types/_instance_types.py
InstanceType(
    ...
    price_per_hour=float(instance_type['price_per_hour']),
    spot_price_per_hour=float(instance_type['spot_price']),
    serverless_price=(
        float(instance_type['serverless_price'])
        if instance_type.get('serverless_price') is not None
        else None
    ),
    ...
)
```

The API returns these as strings. The InstanceType dataclass declares them as
`float`, but the service does NOT use `InstanceType.from_dict()` -- it
constructs the object manually with explicit `float()` casts.

## Long Term Periods -- Missing from Python SDK

The Go SDK has `LongTermService` covering `/long-term/periods` endpoints.
The Python SDK has no equivalent. If syncing this endpoint, a new service
file must be created at `verda/long_term/_long_term.py`.

## Inference Client -- SDK-Only, Not in OpenAPI Spec

The `Deployment` model in ContainersService includes an embedded
`InferenceClient` for running inference against deployed containers. This is
SDK-specific convenience functionality, not generated from the API spec.

```python
# containers/_containers.py
class Deployment:
    _inference_client: InferenceClient | None = None

    @classmethod
    def from_dict_with_inference_key(cls, data, inference_key=None):
        deployment = Deployment.from_dict(data, infer_missing=True)
        if inference_key and deployment.endpoint_base_url:
            deployment._inference_client = InferenceClient(
                inference_key=inference_key,
                endpoint_base_url=deployment.endpoint_base_url,
            )
        return deployment

    def run_sync(self, data, ...):
        self._validate_inference_client()
        return self._inference_client.run_sync(data, ...)
```

**Do NOT** add inference client methods to new services. Do NOT remove or
modify inference client wiring when syncing ContainersService changes.

## Startup Scripts Endpoint Path

StartupScriptsService uses `/scripts` as the endpoint path, not
`/startup-scripts`.

```python
# startup_scripts/_startup_scripts.py
STARTUP_SCRIPTS_ENDPOINT = '/scripts'
```

Match the existing path when modifying this service.

## VolumeType Nested Price Field

VolumeTypesService extracts price from a nested structure in the API response,
not a flat field:

```python
# volume_types/_volume_types.py
VolumeType(
    type=volume_type['type'],
    price_per_month_per_gb=volume_type['price']['price_per_month_per_gb'],
)
```

The API returns `{"type": "...", "price": {"price_per_month_per_gb": ...}}`
but the model flattens it to a single `price_per_month_per_gb` attribute.
