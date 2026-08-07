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

import re

import pytest
import responses

from verda.clusters import ClustersService
from verda.containers import ContainersService
from verda.instances import InstancesService
from verda.job_deployments import JobDeploymentsService
from verda.ssh_keys import SSHKeysService
from verda.startup_scripts import StartupScriptsService
from verda.volumes import VolumesService

BASE_PATH = '/v1'

# Hostile name -> the single path segment it must be reduced to on the wire.
# Expectations are written out literally rather than derived from the SDK helper, so
# the test fails if the encoding rule itself regresses.
HOSTILE_NAMES = [
    ('../../v1/instances', '..%2F..%2Fv1%2Finstances'),
    ('../../../v1/instances', '..%2F..%2F..%2Fv1%2Finstances'),
    ('../ssh-keys', '..%2Fssh-keys'),
    ('../../v1/balance', '..%2F..%2Fv1%2Fbalance'),
    ('nested/../../escape', 'nested%2F..%2F..%2Fescape'),
    # query-string / fragment smuggling
    ('x?force=true&', 'x%3Fforce%3Dtrue%26'),
    ('name#frag', 'name%23frag'),
    # a literal '%' must be escaped so it cannot decode into a dot-segment later
    ('%2E%2E', '%252E%252E'),
]

# Names that cannot be made safe by encoding and must be refused outright:
# '.' and '..' are RFC 3986 dot-segments, and an empty name collapses the URL onto
# the collection endpoint (turning delete-one into delete-all).
REJECTED_NAMES = ['.', '..', '', None]

ANY_URL = re.compile(r'.*')


def _register_catch_all():
    """Answer any request so the prepared URL can be inspected afterwards."""
    for method in (responses.GET, responses.POST, responses.PUT, responses.PATCH, responses.DELETE):
        responses.add(method, ANY_URL, json={}, status=200)


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

    @pytest.mark.parametrize(('name', 'encoded'), HOSTILE_NAMES)
    def test_hostile_name_stays_within_its_endpoint(self, services, name, encoded):
        for label, call, expected_prefix in _call_sites(services, name):
            with responses.RequestsMock(assert_all_requests_are_fired=False) as mock:
                for method in ('GET', 'POST', 'PUT', 'PATCH', 'DELETE'):
                    mock.add(method, ANY_URL, json={}, status=200)
                try:
                    call()
                except Exception:  # response-shape errors are irrelevant here
                    pass

                sent = [c.request.path_url for c in mock.calls]
                assert sent, f'{label}({name!r}) sent no request'
                for path in sent:
                    assert path.startswith(expected_prefix + encoded), (
                        f'{label}({name!r}) escaped its endpoint: {path}'
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

                for path in [c.request.path_url for c in mock.calls]:
                    assert path.startswith(f'{expected_prefix}my-resource-1'), (
                        f'{label} changed shape for an ordinary name: {path}'
                    )

    def test_query_string_injection_cannot_override_the_force_flag(self, services):
        # delete_secret passes params={'force': ...}; the name must not be able to
        # smuggle an earlier `force=true` into the query string.
        with responses.RequestsMock(assert_all_requests_are_fired=False) as mock:
            mock.add('DELETE', ANY_URL, json={}, status=200)
            services['containers'].delete_secret('x?force=true&', force=False)

            path = mock.calls[0].request.path_url
            assert path.count('force=') == 1, f'force flag was polluted: {path}'
            assert path.endswith('force=false'), path
