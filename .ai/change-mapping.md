# OpenAPI → Python SDK Change Mapping

How to translate OpenAPI spec changes into Python SDK code changes.
Read the language-specific patterns file (`.ai/sdks/python/patterns.md`) for conventions.

## Mapping Table

| OpenAPI Change | SDK Action | Files Affected |
|---|---|---|
| New path under existing tag | Add method to existing service | `verda/<resource>/_<resource>.py` + test |
| New tag (resource group) | Create new service module + wire into client | `verda/<resource>/__init__.py`, `verda/<resource>/_<resource>.py`, `verda/_verda.py`, test |
| New/modified request body schema | Add/update `@dataclass` model in service file | `verda/<resource>/_<resource>.py` |
| New/modified response schema | Add/update `@dataclass` model in service file | `verda/<resource>/_<resource>.py` |
| New enum/constant (resource-scoped) | Add `class Name(str, Enum)` in service file | `verda/<resource>/_<resource>.py` |
| New enum/constant (broadly shared) | Add `class Name(str, Enum)` in constants | `verda/constants.py` |
| Modified path parameters | Update method signature | `verda/<resource>/_<resource>.py` + test |
| Modified query parameters | Update `params=dict(...)` in method body | `verda/<resource>/_<resource>.py` + test |
| Removed path | **Log warning only** | None (manual review) |

## Implementation Order

For each SDK change, apply in this order:

1. **Models first** — Add or update `@dataclass_json` / `@dataclass` classes in the service file (or `constants.py` for shared enums)
2. **Service methods** — Add or update methods in the service file
3. **Module exports** — Update `__init__.py` to export new public symbols
4. **Client wiring** — If new service, import in `verda/_verda.py` and add to `VerdaClient.__init__`
5. **Tests** — Add or update tests in the test file
6. **Changelog** — Add concise entry to CHANGELOG.md under `## Unreleased`

## Change Plan Format

Output the plan as a numbered list before implementing:

```
  ---- CHANGE PLAN ----
  1. verda/volumes/_volumes.py  — Add VolumeInTrash dataclass, add fields to VolumeTypeInfo
  2. verda/volumes/_volumes.py  — Add get_volumes_in_trash(), delete_volume_permanently()
  3. verda/volumes/__init__.py  — Export new symbols
  4. tests/test_volumes.py      — Add tests for new methods
  ---- END ----
```

For a new resource/tag:

```
  ---- CHANGE PLAN ----
  1. verda/snapshots/__init__.py   — Create module init, export public symbols
  2. verda/snapshots/_snapshots.py — Add dataclasses + SnapshotsService with methods
  3. verda/_verda.py               — Import SnapshotsService, add to VerdaClient.__init__
  4. tests/test_snapshots.py       — Add tests for all new methods
  ---- END ----
```

## Removed Paths — Special Handling

**Never auto-delete SDK code for removed API paths.** Always:

1. Output a WARNING block
2. Flag for manual review in the sync report
3. Continue with remaining changes

## Python-Specific Notes

### Model Definitions

Models live inside the service file, not in a separate types file. Use the `@dataclass_json` and `@dataclass` decorators:

```python
from dataclasses import dataclass
from dataclasses_json import dataclass_json, Undefined

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class VolumeInfo:
    id: str
    name: str
    size_gb: int
    status: str | None = None
```

- Always use `Undefined.EXCLUDE` so the SDK tolerates extra fields the API may return.
- Place model classes above the service class that uses them.

### Enums and Constants

- **Resource-scoped enums** go in the service file:
  ```python
  from enum import Enum

  class VolumeStatus(str, Enum):
      ACTIVE = "active"
      DELETED = "deleted"
  ```
- **Broadly shared enums** (used by 2+ services) go in `verda/constants.py`.

### HTTP Calls

- Query parameters: pass as `params=dict(...)` to http_client methods.
- Request body: pass as `json=dict(...)` to http_client methods.
- Path parameters: use f-string interpolation in the URL.

```python
def get_volume(self, volume_id: str) -> VolumeInfo:
    resp = self._http_client.get(f"/v1/volumes/{volume_id}")
    return VolumeInfo.from_dict(resp.json())

def list_volumes(self, project_id: str, page: int = 1) -> list[VolumeInfo]:
    resp = self._http_client.get(
        "/v1/volumes",
        params=dict(project_id=project_id, page=page),
    )
    return [VolumeInfo.from_dict(v) for v in resp.json()["volumes"]]

def create_volume(self, name: str, size_gb: int) -> VolumeInfo:
    resp = self._http_client.post(
        "/v1/volumes",
        json=dict(name=name, size_gb=size_gb),
    )
    return VolumeInfo.from_dict(resp.json())
```

### New Service Wiring

When a new tag/resource group appears:

1. Create directory `verda/<resource>/`
2. Create `verda/<resource>/__init__.py` with public exports
3. Create `verda/<resource>/_<resource>.py` with models and service class
4. In `verda/_verda.py`:
   - Import the new service class
   - Add an attribute in `VerdaClient.__init__`: `self.<resource> = <Resource>Service(self._http_client)`

### Naming Conventions

| OpenAPI | Python SDK |
|---|---|
| `operationId: listInstances` | `def list_instances(self, ...)` |
| `operationId: getInstance` | `def get_instance(self, instance_id: str)` |
| Schema: `InstanceTypeInfo` | `class InstanceTypeInfo` (keep PascalCase for dataclasses) |
| Field: `sizeGb` | `size_gb` (snake_case) |
| Enum value: `ACTIVE` | `ACTIVE = "active"` |
