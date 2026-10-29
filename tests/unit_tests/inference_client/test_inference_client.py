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

import pytest
import responses  # https://github.com/getsentry/responses
from responses import matchers

from verda.inference_client import InferenceClient, InferenceClientError

BASE_URL = 'https://inference.example.com/v1/my-deployment'

VERBS = ['get', 'post', 'put', 'delete', 'patch', 'head', 'options']


@pytest.fixture
def inference_client():
    return InferenceClient(inference_key='key-123', endpoint_base_url=BASE_URL)


class TestBuildUrl:
    """`path` is a caller-chosen multi-segment path, but it must stay under the base."""

    @pytest.mark.parametrize(
        ('path', 'expected'),
        [
            ('', f'{BASE_URL}/'),
            ('predict', f'{BASE_URL}/predict'),
            ('/predict', f'{BASE_URL}/predict'),
            # multi-segment paths are the documented contract and must keep working
            ('v1/models/predict', f'{BASE_URL}/v1/models/predict'),
            ('/v1/models/predict', f'{BASE_URL}/v1/models/predict'),
            ('v1/chat/completions', f'{BASE_URL}/v1/chat/completions'),
            ('v1/models/', f'{BASE_URL}/v1/models/'),
            # TensorFlow Serving names the method after a ':'
            ('v1/models/my_model:predict', f'{BASE_URL}/v1/models/my_model:predict'),
        ],
    )
    def test_ordinary_paths_are_joined_unchanged(self, inference_client, path, expected):
        assert inference_client._build_url(path) == expected

    @pytest.mark.parametrize(
        'path',
        [
            '../other-deployment',
            '../../v1/other-deployment',
            'a/../../b',
            './x',
            '..',
        ],
    )
    def test_paths_that_escape_the_deployment_are_rejected(self, inference_client, path):
        # endpoint_base_url ends with this deployment's name, so a dot-segment walks
        # the request onto a different deployment while still carrying the caller's
        # inference key.
        with pytest.raises(InferenceClientError, match='escape the API base path'):
            inference_client._build_url(path)

    @pytest.mark.parametrize(
        'path',
        ['chat?x=1', 'v1#frag', 'predict?filter=a/../b', 'predict?q=..'],
    )
    def test_a_query_string_or_fragment_in_the_path_is_rejected(self, inference_client, path):
        # Query data is passed as `params`, so a '?' or '#' here can only come from a
        # value interpolated into the path, injecting parameters into a request that
        # carries the inference key.
        with pytest.raises(InferenceClientError, match='query string or fragment'):
            inference_client._build_url(path)

    @pytest.mark.parametrize(
        'path',
        [
            # requests decodes percent-encoded unreserved characters before sending,
            # so these reach the wire as real dot-segments.
            '%2e%2e/x',
            '%2e%2e/%2e%2e/v1/victim',
            '%2E%2E/other-deployment',
            # a decoding check misses these, but a normalising proxy may not
            '..%252fx',
            '..%2Fx',
            '..;/x',
            'a\\b',
            'a;b',
            'v1/my model',
        ],
    )
    def test_an_escape_or_a_character_outside_the_allowlist_is_rejected(
        self, inference_client, path
    ):
        with pytest.raises(InferenceClientError, match='unencoded value'):
            inference_client._build_url(path)


class TestRequestPaths:
    @pytest.mark.parametrize('verb', VERBS)
    @responses.activate
    def test_params_are_sent_as_the_query_string(self, inference_client, verb):
        # arrange
        responses.add(
            verb.upper(),
            f'{BASE_URL}/v1/models',
            match=[matchers.query_param_matcher({'filter': 'a/../b'})],
        )

        # act
        response = getattr(inference_client, verb)('v1/models', params={'filter': 'a/../b'})

        # assert
        assert response.status_code == 200

    @pytest.mark.parametrize('verb', VERBS)
    @responses.activate
    def test_a_rejected_path_sends_no_request(self, inference_client, verb):
        with pytest.raises(InferenceClientError, match='query string or fragment'):
            getattr(inference_client, verb)('chat?x=1')

        assert len(responses.calls) == 0

    @responses.activate
    def test_run_sync_posts_to_the_path(self, inference_client):
        # arrange
        responses.add(responses.POST, f'{BASE_URL}/v1/chat/completions', json={'ok': True})

        # act
        response = inference_client.run_sync({'prompt': 'hi'}, path='v1/chat/completions')

        # assert
        assert response.status_code == 200

    @responses.activate
    def test_run_posts_to_the_path(self, inference_client):
        # arrange
        responses.add(responses.POST, f'{BASE_URL}/v1/chat/completions', json={'Id': 'abc'})

        # act
        execution = inference_client.run({'prompt': 'hi'}, path='v1/chat/completions')

        # assert
        assert execution.id == 'abc'

    @responses.activate
    def test_run_sync_sends_params_as_the_query_string(self, inference_client):
        # arrange
        responses.add(
            responses.POST,
            f'{BASE_URL}/v1/completions',
            json={'ok': True},
            match=[matchers.query_param_matcher({'stream': 'true'})],
        )

        # act
        response = inference_client.run_sync(
            {'prompt': 'hi'}, path='v1/completions', params={'stream': 'true'}
        )

        # assert
        assert response.status_code == 200

    @pytest.mark.parametrize('no_response', [False, True])
    @responses.activate
    def test_run_sends_params_as_the_query_string(self, inference_client, no_response):
        # arrange
        responses.add(
            responses.POST,
            f'{BASE_URL}/v1/completions',
            json={'Id': 'abc'},
            match=[matchers.query_param_matcher({'stream': 'true'})],
        )

        # act
        inference_client.run(
            {'prompt': 'hi'},
            path='v1/completions',
            no_response=no_response,
            params={'stream': 'true'},
        )

        # assert
        assert len(responses.calls) == 1

    @responses.activate
    def test_health_gets_the_health_path(self, inference_client):
        # arrange
        responses.add(responses.GET, f'{BASE_URL}/health')

        # act
        response = inference_client.health()

        # assert
        assert response.status_code == 200

    @responses.activate
    def test_run_sync_rejects_a_query_string_in_the_path(self, inference_client):
        with pytest.raises(InferenceClientError, match='query string or fragment'):
            inference_client.run_sync({'prompt': 'hi'}, path='v1/completions?stream=true')

        assert len(responses.calls) == 0


class TestEndpointBaseUrl:
    @pytest.mark.parametrize(
        'base_url',
        [
            'https://inf.example.com/v1/..',
            'https://inf.example.com/v1/%2E%2E',
            'https://inf.example.com/v1/../admin/dep',
        ],
    )
    def test_base_url_containing_a_dot_segment_is_rejected(self, base_url):
        # deployment_name and base_domain are sliced out of this and interpolated
        # into the async status/result urls without further checks.
        with pytest.raises(InferenceClientError, match='relative path segment'):
            InferenceClient(inference_key='k', endpoint_base_url=base_url)

    @pytest.mark.parametrize(
        'base_url',
        ['https://containers.example.com', 'https://containers.example.com/'],
    )
    def test_base_url_without_a_deployment_path_is_rejected(self, base_url):
        # rindex('/') would find the '//' of the scheme, making base_domain 'https:/'
        # and the async status url 'https://status/containers.example.com'.
        with pytest.raises(InferenceClientError, match='must include the deployment path'):
            InferenceClient(inference_key='k', endpoint_base_url=base_url)

    def test_the_deployment_name_is_sliced_out_correctly(self, inference_client):
        assert inference_client.deployment_name == 'my-deployment'
        assert inference_client.base_domain == 'https://inference.example.com/v1'
