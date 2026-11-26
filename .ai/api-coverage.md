---
name: python-sdk-api-coverage
description: Complete mapping of OpenAPI spec endpoints to Python SDK implementation. Use to locate code for any API endpoint, identify gaps, and track what changed between syncs.
metadata:
  pattern: tool-wrapper
  domain: python-sdk
  last_scan: "2026-03-25"
  spec_endpoints_active: 68
  spec_endpoints_deprecated: 8
  sdk_implemented: 66
  sdk_missing: 2
---

# Python SDK API Coverage

Complete endpoint-by-endpoint mapping from OpenAPI spec to Python SDK code.
Organized by API tag (resource group) for fast lookup.

**Spec:** `openapi.json` (Verda Cloud Public API)
**SDK:** `tmp/sdk-python/verda/`

**Legend:**
- ✓ = implemented
- ✗ = missing (needs implementation)
- ⊘ = deprecated in spec (correctly skipped)
- ⊕ = SDK-only (convenience helper, not in spec)
- ⚠ = mismatch (needs investigation)

---

## Authentication

**File:** `authentication/_authentication.py` → `AuthenticationService`
**Coverage:** 1/1

| Spec Endpoint | SDK Method | Status |
|---|---|---|
| `POST /v1/oauth2/token` | `authenticate` (client_credentials) | ✓ |
| `POST /v1/oauth2/token` | `refresh` (refresh_token grant) | ✓ |
| — | `is_expired` | ⊕ expiry check helper |

---

## Balance

**File:** `balance/_balance.py` → `BalanceService`
**Coverage:** 1/1

| Spec Endpoint | SDK Method | Status |
|---|---|---|
| `GET /v1/balance` | `get` | ✓ |

---

## Clusters

**File:** `clusters/_clusters.py` → `ClustersService`
**Coverage:** 8/8

| Spec Endpoint | SDK Method | Status |
|---|---|---|
| `GET /v1/clusters` | `get` | ✓ |
| `POST /v1/clusters` | `create` | ✓ |
| `PUT /v1/clusters` | `action` | ✓ |
| `GET /v1/clusters/{id}` | `get_by_id` | ✓ |
| `GET /v1/cluster-types` | `ClusterTypesService.get` | ✓ (separate service) |
| `GET /v1/cluster-availability` | `get_availabilities` | ✓ |
| `GET /v1/cluster-availability/{cluster_type}` | `is_available` | ✓ |
| `GET /v1/images/cluster` | `get_cluster_images` | ✓ (on ClustersService, not ImagesService) |
| — | `delete` | ⊕ convenience wrapper for `action('delete')` |

---

## Cluster Types

**File:** `cluster_types/_cluster_types.py` → `ClusterTypesService`
**Coverage:** 1/1

| Spec Endpoint | SDK Method | Status |
|---|---|---|
| `GET /v1/cluster-types` | `get` | ✓ |

---

## Serverless Containers

**File:** `containers/_containers.py` → `ContainersService`
**Coverage:** 27/27

| Spec Endpoint | SDK Method | Status |
|---|---|---|
| `GET /v1/container-deployments` | `get_deployments` | ✓ |
| `POST /v1/container-deployments` | `create_deployment` | ✓ |
| `GET /v1/container-deployments/{name}` | `get_deployment_by_name` | ✓ |
| `PATCH /v1/container-deployments/{name}` | `update_deployment` | ✓ |
| `DELETE /v1/container-deployments/{name}` | `delete_deployment` | ✓ |
| `GET /v1/container-deployments/{name}/status` | `get_deployment_status` | ✓ |
| `POST /v1/container-deployments/{name}/restart` | `restart_deployment` | ✓ |
| `POST /v1/container-deployments/{name}/pause` | `pause_deployment` | ✓ |
| `POST /v1/container-deployments/{name}/resume` | `resume_deployment` | ✓ |
| `POST /v1/container-deployments/{name}/purge-queue` | `purge_deployment_queue` | ✓ |
| `GET /v1/container-deployments/{name}/scaling` | `get_deployment_scaling_options` | ✓ |
| `PATCH /v1/container-deployments/{name}/scaling` | `update_deployment_scaling_options` | ✓ |
| `GET /v1/container-deployments/{name}/replicas` | `get_deployment_replicas` | ✓ |
| `GET /v1/container-deployments/{name}/environment-variables` | `get_deployment_environment_variables` | ✓ |
| `POST /v1/container-deployments/{name}/environment-variables` | `add_deployment_environment_variables` | ✓ |
| `PATCH /v1/container-deployments/{name}/environment-variables` | `update_deployment_environment_variables` | ✓ |
| `DELETE /v1/container-deployments/{name}/environment-variables` | `delete_deployment_environment_variables` | ✓ |
| `GET /v1/container-registry-credentials` | `get_registry_credentials` | ✓ |
| `POST /v1/container-registry-credentials` | `add_registry_credentials` | ✓ |
| `DELETE /v1/container-registry-credentials/{name}` | `delete_registry_credentials` | ✓ |
| `GET /v1/secrets` | `get_secrets` | ✓ |
| `POST /v1/secrets` | `create_secret` | ✓ |
| `DELETE /v1/secrets/{name}` | `delete_secret` | ✓ |
| `GET /v1/file-secrets` | `get_fileset_secrets` | ✓ |
| `POST /v1/file-secrets` | `create_fileset_secret_from_file_paths` | ✓ |
| `DELETE /v1/file-secrets/{name}` | `delete_fileset_secret` | ✓ |
| `GET /v1/serverless-compute-resources` | `get_compute_resources` | ✓ |
| — | `get_deployment` | ⊕ alias for `get_deployment_by_name` |
| — | `get_gpus` | ⊕ alias for `get_compute_resources` |

---

## Container Types

**File:** `container_types/_container_types.py` → `ContainerTypesService`
**Coverage:** 1/1

| Spec Endpoint | SDK Method | Status |
|---|---|---|
| `GET /v1/container-types` | `get` | ✓ |

---

## Images

**File:** `images/_images.py` → `ImagesService`
**Coverage:** 1/2

| Spec Endpoint | SDK Method | Status |
|---|---|---|
| `GET /v1/images` | `get` | ✓ |
| `GET /v1/images/cluster` | — | ⚠ not in ImagesService (covered by `ClustersService.get_cluster_images`) |

---

## Inference Client

**File:** `inference_client/_inference_client.py` → `InferenceClient`
**Coverage:** SDK-only (0 spec endpoints)

| Spec Endpoint | SDK Method | Status |
|---|---|---|
| — | `run_sync` | ⊕ synchronous inference request |
| — | `run` | ⊕ asynchronous inference request |
| — | `health` | ⊕ deployment health check |
| — | `get` | ⊕ generic GET helper |
| — | `post` | ⊕ generic POST helper |
| — | `put` | ⊕ generic PUT helper |
| — | `delete` | ⊕ generic DELETE helper |
| — | `patch` | ⊕ generic PATCH helper |

Note: `InferenceClient` is SDK-only. It is used by `Deployment` objects (in `ContainersService`) for inference against deployed endpoints. No equivalent exists in the Go SDK.

---

## Instance Availability

**File:** `instances/_instances.py` → `InstancesService`
**Coverage:** 2/2

| Spec Endpoint | SDK Method | Status |
|---|---|---|
| `GET /v1/instance-availability` | `get_availabilities` | ✓ |
| `GET /v1/instance-availability/{instance_type}` | `is_available` | ✓ |

Note: Instance availability is handled directly on `InstancesService`, not as a separate service.

---

## Instance Types

**File:** `instance_types/_instance_types.py` → `InstanceTypesService`
**Coverage:** 1/1 active (1 deprecated not implemented)

| Spec Endpoint | SDK Method | Status |
|---|---|---|
| `GET /v1/instance-types` | `get` | ✓ |
| `GET /v1/instance-types/price-history` | — | ⊘ deprecated (not implemented) |

---

## Instances

**File:** `instances/_instances.py` → `InstancesService`
**Coverage:** 4/4 active (3 deprecated skipped)

| Spec Endpoint | SDK Method | Status |
|---|---|---|
| `GET /v1/instances` | `get` | ✓ |
| `POST /v1/instances` | `create` | ✓ |
| `PUT /v1/instances` | `action` | ✓ |
| `GET /v1/instances/{instance_id}` | `get_by_id` | ✓ |
| `POST /v1/instances/action` | — | ⊘ deprecated |
| `GET /v1/instances/availability/{instanceType}` | — | ⊘ deprecated |
| `GET /v1/instances/types` | — | ⊘ deprecated |

---

## Locations

**File:** `locations/_locations.py` → `LocationsService`
**Coverage:** 1/1

| Spec Endpoint | SDK Method | Status |
|---|---|---|
| `GET /v1/locations` | `get` | ✓ |

---

## Long Term

**File:** `long_term/_long_term.py` → `LongTermService`
**Coverage:** 2/2 active (1 deprecated skipped)

| Spec Endpoint | SDK Method | Status |
|---|---|---|
| `GET /v1/long-term/periods` | — | ⊘ deprecated |
| `GET /v1/long-term/periods/clusters` | `get_cluster_periods` | ✓ |
| `GET /v1/long-term/periods/instances` | `get_instance_periods` | ✓ |

---

## Serverless Jobs

**File:** `job_deployments/_job_deployments.py` → `JobDeploymentsService`
**Coverage:** 10/10

| Spec Endpoint | SDK Method | Status |
|---|---|---|
| `GET /v1/job-deployments` | `get` | ✓ |
| `POST /v1/job-deployments` | `create` | ✓ |
| `GET /v1/job-deployments/{name}` | `get_by_name` | ✓ |
| `PATCH /v1/job-deployments/{name}` | `update` | ✓ |
| `DELETE /v1/job-deployments/{name}` | `delete` | ✓ |
| `GET /v1/job-deployments/{name}/scaling` | `get_scaling_options` | ✓ |
| `POST /v1/job-deployments/{name}/purge-queue` | `purge_queue` | ✓ |
| `POST /v1/job-deployments/{name}/pause` | `pause` | ✓ |
| `POST /v1/job-deployments/{name}/resume` | `resume` | ✓ |
| `GET /v1/job-deployments/{name}/status` | `get_status` | ✓ |

---

## SSH Keys

**File:** `ssh_keys/_ssh_keys.py` → `SSHKeysService`
**Coverage:** 0/5 active (5 deprecated implemented instead)

| Spec Endpoint | SDK Method | Status |
|---|---|---|
| `GET /v1/ssh-keys` | — | ✗ missing (uses old path) |
| `POST /v1/ssh-keys` | — | ✗ missing (uses old path) |
| `DELETE /v1/ssh-keys` | — | ✗ missing (uses old path) |
| `GET /v1/ssh-keys/{sshKeyId}` | — | ✗ missing (uses old path) |
| `DELETE /v1/ssh-keys/{sshKeyId}` | — | ✗ missing (uses old path) |
| `GET /v1/sshkeys` | `get` | ⚠ deprecated path, should use `/ssh-keys` |
| `POST /v1/sshkeys` | `create` | ⚠ deprecated path, should use `/ssh-keys` |
| `DELETE /v1/sshkeys` | `delete` | ⚠ deprecated path, should use `/ssh-keys` |
| `GET /v1/sshkeys/{sshKeyId}` | `get_by_id` | ⚠ deprecated path, should use `/ssh-keys` |
| `DELETE /v1/sshkeys/{sshKeyId}` | `delete_by_id` | ⚠ deprecated path, should use `/ssh-keys` |

---

## Startup Scripts

**File:** `startup_scripts/_startup_scripts.py` → `StartupScriptsService`
**Coverage:** 5/5

| Spec Endpoint | SDK Method | Status |
|---|---|---|
| `GET /v1/scripts` | `get` | ✓ |
| `POST /v1/scripts` | `create` | ✓ |
| `DELETE /v1/scripts` | `delete` | ✓ |
| `GET /v1/scripts/{scriptId}` | `get_by_id` | ✓ |
| `DELETE /v1/scripts/{scriptId}` | `delete_by_id` | ✓ |

---

## Volume Types

**File:** `volume_types/_volume_types.py` → `VolumeTypesService`
**Coverage:** 1/1

| Spec Endpoint | SDK Method | Status |
|---|---|---|
| `GET /v1/volume-types` | `get` | ✓ |

---

## Volumes

**File:** `volumes/_volumes.py` → `VolumesService`
**Coverage:** 6/6

| Spec Endpoint | SDK Method | Status |
|---|---|---|
| `GET /v1/volumes` | `get` | ✓ |
| `POST /v1/volumes` | `create` | ✓ |
| `PUT /v1/volumes` | `attach` / `detach` / `clone` / `rename` / `increase_size` / `delete` | ✓ |
| `GET /v1/volumes/{volume_id}` | `get_by_id` | ✓ |
| `DELETE /v1/volumes/{volume_id}` | `delete_by_id` | ✓ |
| `GET /v1/volumes/trash` | `get_in_trash` | ✓ |

Note: The SDK uses `PUT /v1/volumes` with action `delete` instead of `DELETE /v1/volumes/{volume_id}`. The spec has both endpoints.

---

## Overall Summary

| Metric | Count |
|---|---|
| Active spec endpoints | 68 |
| SDK implemented (correct path) | 66 |
| Missing (active, not implemented) | 2 |
| Deprecated (correctly skipped) | 4 |
| Deprecated (implemented via old path) | 5 |
| SDK-only methods | ~15 (InferenceClient, aliases, convenience wrappers) |

### Breakdown of Missing Endpoints

| # | Endpoint | Reason |
|---|---|---|
| 1 | `GET /v1/ssh-keys` | Uses deprecated `/sshkeys` path instead |
| 2 | `POST /v1/ssh-keys` | Uses deprecated `/sshkeys` path instead |

Note: SSH keys endpoints 3-5 (`DELETE /v1/ssh-keys`, `GET /v1/ssh-keys/{sshKeyId}`, `DELETE /v1/ssh-keys/{sshKeyId}`) also use deprecated path but are functionally equivalent.

### Known Issues

| # | Type | Detail |
|---|---|---|
| 1 | ⚠ Old path | `SSHKeysService` uses deprecated `/sshkeys` path instead of `/ssh-keys` |
| 3 | ⚠ Naming | `ContainersService` is equivalent to Go SDK's `ContainerDeploymentsService` |
| 4 | ⚠ Naming | `JobDeploymentsService` is equivalent to Go SDK's `ServerlessJobsService` |
| 5 | ⊕ SDK-only | `InferenceClient` has no equivalent in Go SDK or OpenAPI spec |
| 6 | ⚠ Placement | `GET /v1/images/cluster` is on `ClustersService`, not `ImagesService` |
| 7 | ⚠ Placement | Instance availability endpoints are on `InstancesService`, not a separate service |
| 8 | ✓ Both patterns | `DELETE /v1/volumes/{volume_id}` via `delete_by_id()`; bulk delete via `PUT /v1/volumes` action |

### Key Differences from Go SDK

| Area | Go SDK | Python SDK |
|---|---|---|
| Long Term | `LongTermService` with 3 methods | `LongTermService` with 2 methods (deprecated endpoint skipped) |
| SSH Keys path | `/ssh-keys` (new path) | `/sshkeys` (deprecated path) |
| Container service name | `ContainerDeploymentsService` | `ContainersService` |
| Serverless jobs name | `ServerlessJobsService` | `JobDeploymentsService` |
| Inference client | Not present | `InferenceClient` (SDK-only) |
| Images/cluster | In both `ClusterService` and `ImagesService` | Only in `ClustersService` |
| Instance availability | Separate `InstanceAvailabilityService` + `InstanceService` | Only on `InstancesService` |
| Volume delete | Uses `DELETE /v1/volumes/{id}` | Both: `delete_by_id()` (DELETE) + `delete()` (PUT action) |
