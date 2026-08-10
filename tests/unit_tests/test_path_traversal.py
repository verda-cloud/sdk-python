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

"""Regression tests: a caller-supplied name must stay inside its own path segment.

Resource names and IDs reach the SDK from application input. When they are
interpolated into the request path unencoded, `requests` resolves any relative
segments they contain while preparing the URL, which retargets the call at a
different API endpoint using the SDK's own credentials.
"""

import ast
import pathlib
import re

import pytest
import responses

import verda
from verda.clusters import ClustersService
from verda.containers import (
    ComputeResource,
    Container,
    ContainersService,
    Deployment,
    EnvVar,
    EnvVarType,
    QueueLoadScalingTrigger,
    ScalingOptions,
    ScalingPolicy,
    ScalingTriggers,
)
from verda.instances import InstancesService
from verda.job_deployments import JobDeployment, JobDeploymentsService
from verda.ssh_keys import SSHKeysService
from verda.startup_scripts import StartupScriptsService
from verda.volumes import VolumesService

BASE_PATH = '/v1'

# Names outside the RFC 3986 unreserved set, refused rather than encoded:
#  - '.' and '..' are dot-segments, and requests decodes '%2E' back to '.'
#  - a separator ('/', or '\' on servers that normalise it) addresses a different
#    endpoint, and '%2F' holds only until an intermediary unescapes it
#  - '?' and '#' start a query string or fragment
#  - '%' makes a name ambiguous with the two cases above
#  - an empty name turns a delete-one call into a delete-all call
REJECTED_NAMES = [
    '.',
    '..',
    '',
    None,
    '../../v1/instances',
    '../../../v1/instances',
    '../ssh-keys',
    '../../v1/balance',
    'nested/../../escape',
    '..\\..\\v1\\instances',
    'nested\\..\\..\\escape',
    'a/b',
    'docker.io/myorg',
    'x?force=true&',
    'name#frag',
    '%2E%2E',
    '..%2F..',
    'my%20deployment',
    'a b',
]

ANY_URL = re.compile(r'.*')

# Bodies for the methods that need more than a name; their content is irrelevant,
# only the request path is under test.
_CONTAINER = Container(image='img', exposed_port=80)
_COMPUTE = ComputeResource(name='General Purpose 2D:2v', size=1)
_DEPLOYMENT = Deployment(name='d', containers=[_CONTAINER], compute=_COMPUTE)
_JOB = JobDeployment(name='j', containers=[_CONTAINER], compute=_COMPUTE)
_SCALING = ScalingOptions(
    min_replica_count=1,
    max_replica_count=5,
    scale_down_policy=ScalingPolicy(delay_seconds=300),
    scale_up_policy=ScalingPolicy(delay_seconds=60),
    queue_message_ttl_seconds=3600,
    concurrent_requests_per_replica=10,
    scaling_triggers=ScalingTriggers(queue_load=QueueLoadScalingTrigger(threshold=0.75)),
)
_ENV_VARS = [EnvVar(name='K', value_or_reference_to_secret='v', type=EnvVarType.PLAIN)]


def _service_methods_taking_a_path_param() -> set[tuple[str, str]]:
    """(class, method) for every service method that passes a value as a path param.

    Derived from the source rather than hand-listed, so a newly added method cannot
    quietly escape the regression table below.
    """
    found = set()
    for path in sorted(pathlib.Path(verda.__file__).parent.rglob('*.py')):
        for node in ast.walk(ast.parse(path.read_text())):
            if not isinstance(node, ast.ClassDef) or not node.name.endswith('Service'):
                continue
            for method in node.body:
                if not isinstance(method, ast.FunctionDef):
                    continue
                for call in ast.walk(method):
                    if isinstance(call, ast.Call) and any(
                        keyword.arg == 'path_params' for keyword in call.keywords
                    ):
                        found.add((node.name, method.name))
    return found


def _service_methods_interpolating_a_url() -> set[tuple[str, str]]:
    """(class, method) for service methods that build a url with an f-string.

    The table below only knows about methods that already pass ``path_params``, so a
    newly added method that interpolates instead would be invisible to it. This finds
    those directly: it was an inline f-string url, not an endpoint constant, that hid
    ``is_available`` from every earlier search.
    """
    found = set()
    for path in sorted(pathlib.Path(verda.__file__).parent.rglob('*.py')):
        for node in ast.walk(ast.parse(path.read_text())):
            if not isinstance(node, ast.ClassDef) or not node.name.endswith('Service'):
                continue
            for method in node.body:
                if not isinstance(method, ast.FunctionDef):
                    continue
                for expression in ast.walk(method):
                    if not isinstance(expression, ast.JoinedStr):
                        continue
                    literal = ''.join(
                        part.value for part in expression.values if isinstance(part, ast.Constant)
                    )
                    interpolates = any(
                        isinstance(part, ast.FormattedValue) for part in expression.values
                    )
                    if interpolates and '/' in literal:
                        found.add((node.name, method.name))
    return found


def _call_sites(services, name):
    """Every single-resource call site that interpolates a caller-supplied value.

    Returns (label, callable, expected_path_prefix) triples.
    """
    containers = services['containers']
    jobs = services['jobs']
    deployments = f'{BASE_PATH}/container-deployments/'
    job_deployments = f'{BASE_PATH}/job-deployments/'

    return [
        (
            'containers.get_deployment_by_name',
            lambda: containers.get_deployment_by_name(name),
            deployments,
        ),
        ('containers.delete_deployment', lambda: containers.delete_deployment(name), deployments),
        (
            'containers.get_deployment_status',
            lambda: containers.get_deployment_status(name),
            deployments,
        ),
        ('containers.restart_deployment', lambda: containers.restart_deployment(name), deployments),
        (
            'containers.get_deployment_scaling_options',
            lambda: containers.get_deployment_scaling_options(name),
            deployments,
        ),
        (
            'containers.get_deployment_replicas',
            lambda: containers.get_deployment_replicas(name),
            deployments,
        ),
        (
            'containers.purge_deployment_queue',
            lambda: containers.purge_deployment_queue(name),
            deployments,
        ),
        ('containers.pause_deployment', lambda: containers.pause_deployment(name), deployments),
        ('containers.resume_deployment', lambda: containers.resume_deployment(name), deployments),
        (
            'containers.get_deployment_environment_variables',
            lambda: containers.get_deployment_environment_variables(name),
            deployments,
        ),
        (
            'containers.delete_secret',
            lambda: containers.delete_secret(name),
            f'{BASE_PATH}/secrets/',
        ),
        (
            'containers.delete_registry_credentials',
            lambda: containers.delete_registry_credentials(name),
            f'{BASE_PATH}/container-registry-credentials/',
        ),
        (
            'containers.delete_fileset_secret',
            lambda: containers.delete_fileset_secret(name),
            f'{BASE_PATH}/file-secrets/',
        ),
        (
            'instances.get_by_id',
            lambda: services['instances'].get_by_id(name),
            f'{BASE_PATH}/instances/',
        ),
        ('volumes.get_by_id', lambda: services['volumes'].get_by_id(name), f'{BASE_PATH}/volumes/'),
        (
            'volumes.delete_by_id',
            lambda: services['volumes'].delete_by_id(name),
            f'{BASE_PATH}/volumes/',
        ),
        (
            'ssh_keys.get_by_id',
            lambda: services['ssh_keys'].get_by_id(name),
            f'{BASE_PATH}/sshkeys/',
        ),
        (
            'ssh_keys.delete_by_id',
            lambda: services['ssh_keys'].delete_by_id(name),
            f'{BASE_PATH}/sshkeys/',
        ),
        (
            'startup_scripts.get_by_id',
            lambda: services['startup_scripts'].get_by_id(name),
            f'{BASE_PATH}/scripts/',
        ),
        (
            'startup_scripts.delete_by_id',
            lambda: services['startup_scripts'].delete_by_id(name),
            f'{BASE_PATH}/scripts/',
        ),
        (
            'clusters.get_by_id',
            lambda: services['clusters'].get_by_id(name),
            f'{BASE_PATH}/clusters/',
        ),
        (
            'containers.update_deployment',
            lambda: containers.update_deployment(name, _DEPLOYMENT),
            deployments,
        ),
        (
            'containers.update_deployment_scaling_options',
            lambda: containers.update_deployment_scaling_options(name, _SCALING),
            deployments,
        ),
        (
            'containers.add_deployment_environment_variables',
            lambda: containers.add_deployment_environment_variables(name, 'c', _ENV_VARS),
            deployments,
        ),
        (
            'containers.update_deployment_environment_variables',
            lambda: containers.update_deployment_environment_variables(name, 'c', _ENV_VARS),
            deployments,
        ),
        (
            'containers.delete_deployment_environment_variables',
            lambda: containers.delete_deployment_environment_variables(name, 'c', ['K']),
            deployments,
        ),
        (
            'instances.is_available',
            lambda: services['instances'].is_available(name),
            f'{BASE_PATH}/instance-availability/',
        ),
        (
            'clusters.is_available',
            lambda: services['clusters'].is_available(name),
            f'{BASE_PATH}/cluster-availability/',
        ),
        ('jobs.update', lambda: jobs.update(name, _JOB), job_deployments),
        ('jobs.get_by_name', lambda: jobs.get_by_name(name), job_deployments),
        ('jobs.delete', lambda: jobs.delete(name), job_deployments),
        ('jobs.get_status', lambda: jobs.get_status(name), job_deployments),
        ('jobs.get_scaling_options', lambda: jobs.get_scaling_options(name), job_deployments),
        ('jobs.pause', lambda: jobs.pause(name), job_deployments),
        ('jobs.resume', lambda: jobs.resume(name), job_deployments),
        ('jobs.purge_queue', lambda: jobs.purge_queue(name), job_deployments),
    ]


class TestPathTraversal:
    @pytest.fixture
    def services(self, http_client):
        return {
            'containers': ContainersService(http_client),
            'instances': InstancesService(http_client),
            'volumes': VolumesService(http_client),
            'ssh_keys': SSHKeysService(http_client),
            'startup_scripts': StartupScriptsService(http_client),
            'clusters': ClustersService(http_client),
            'jobs': JobDeploymentsService(http_client),
        }

    def test_no_service_builds_a_url_by_interpolation(self):
        # CLAUDE.md: "Never interpolate a caller-supplied value into the request path."
        # Without this, a new method that f-strings its url is caught by neither the
        # coverage table below nor the runtime backstop.
        interpolating = _service_methods_interpolating_a_url()

        assert not interpolating, (
            f'these methods build a url with an f-string instead of path_params, so a '
            f'caller-supplied value can escape its path segment: {sorted(interpolating)}'
        )

    def test_every_method_taking_a_path_param_is_covered(self, services):
        # The table below is hand-maintained; this is what stops it drifting. Two
        # methods (instances/clusters.is_available) were once missed exactly this way.
        # arrange
        covered = set()
        for label, _, _ in _call_sites(services, 'placeholder'):
            service_key, method_name = label.split('.', 1)
            covered.add((type(services[service_key]).__name__, method_name))

        # act
        missing = _service_methods_taking_a_path_param() - covered

        # assert
        assert not missing, (
            f'these methods take a caller-supplied path value but are not exercised '
            f'by this file; add them to _call_sites: {sorted(missing)}'
        )

    @pytest.mark.parametrize('name', REJECTED_NAMES)
    def test_unsafe_name_is_rejected_before_a_request_is_sent(self, services, name):
        for label, call, _ in _call_sites(services, name):
            with responses.RequestsMock(assert_all_requests_are_fired=False) as mock:
                for method in ('GET', 'POST', 'PUT', 'PATCH', 'DELETE'):
                    mock.add(method, ANY_URL, json={}, status=200)
                with pytest.raises(ValueError, match='path segment must'):
                    call()
                assert not mock.calls, f'{label}({name!r}) sent a request anyway'

    def test_ordinary_names_still_reach_the_documented_route(self, services):
        for label, call, expected_prefix in _call_sites(services, 'my-resource-1'):
            with responses.RequestsMock(assert_all_requests_are_fired=False) as mock:
                for method in ('GET', 'POST', 'PUT', 'PATCH', 'DELETE'):
                    mock.add(method, ANY_URL, json={}, status=200)
                try:
                    call()
                except Exception:  # response shape is irrelevant here
                    pass

                # Without this the test passes vacuously if the call raises before
                # sending -- exactly the regression it exists to catch.
                assert mock.calls, f'{label} sent no request for an ordinary name'
                for path in [c.request.path_url for c in mock.calls]:
                    assert path.startswith(f'{expected_prefix}my-resource-1'), (
                        f'{label} changed shape for an ordinary name: {path}'
                    )

    def test_query_string_injection_cannot_override_the_force_flag(self, services):
        # delete_secret passes params={'force': ...}; the name must not be able to
        # smuggle an earlier `force=true` into the query string.
        with responses.RequestsMock(assert_all_requests_are_fired=False) as mock:
            mock.add('DELETE', ANY_URL, json={}, status=200)
            with pytest.raises(ValueError, match='path segment must'):
                services['containers'].delete_secret('x?force=true&', force=False)
            assert not mock.calls, 'a name carrying a query string reached the wire'

    def test_the_force_flag_still_reaches_the_query_string(self, services):
        # Without this the test above passes even if delete_secret stopped sending it.
        with responses.RequestsMock(assert_all_requests_are_fired=False) as mock:
            mock.add('DELETE', ANY_URL, json={}, status=200)
            services['containers'].delete_secret('my-api-key', force=False)

            path = mock.calls[0].request.path_url
            assert path.count('force=') == 1, f'force flag was polluted: {path}'
            assert path.endswith('force=false'), path
