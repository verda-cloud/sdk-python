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
import requests
import responses  # https://github.com/getsentry/responses
from responses import matchers

from verda.inference_client import (
    AsyncInferenceExecution,
    AsyncStatus,
    InferenceClient,
    InferenceClientError,
)

BASE_URL = 'https://inference.example.com/v1/my-deployment'

VERBS = ['get', 'post', 'put', 'delete', 'patch', 'head', 'options']


PREDICT_URL = f'{BASE_URL}/predict'
STATUS_URL = 'https://inference.example.com/v1/status/my-deployment'
RESULT_URL = 'https://inference.example.com/v1/result/my-deployment'
REDIRECT_URL = 'https://inference.example.com/v1/moved'
MOVED_URL = f'{BASE_URL}/moved'
EXECUTION_ID = 'exec-1'

REDIRECT_STATUSES = [301, 302, 303, 307, 308]


def _execution(client):
    return AsyncInferenceExecution(client, EXECUTION_ID, AsyncStatus.Initialized)


# (method, url the call sends to, call)
ENTRY_POINTS = {
    'run_sync': ('POST', PREDICT_URL, lambda c: c.run_sync({'a': 1}, path='predict')),
    'run': ('POST', PREDICT_URL, lambda c: c.run({'a': 1}, path='predict')),
    'run_no_response': (
        'POST',
        PREDICT_URL,
        lambda c: c.run({'a': 1}, path='predict', no_response=True),
    ),
    'get': ('GET', PREDICT_URL, lambda c: c.get('predict')),
    'post': ('POST', PREDICT_URL, lambda c: c.post('predict', json={'a': 1})),
    'put': ('PUT', PREDICT_URL, lambda c: c.put('predict', json={'a': 1})),
    'delete': ('DELETE', PREDICT_URL, lambda c: c.delete('predict')),
    'patch': ('PATCH', PREDICT_URL, lambda c: c.patch('predict', json={'a': 1})),
    'head': ('HEAD', PREDICT_URL, lambda c: c.head('predict')),
    'options': ('OPTIONS', PREDICT_URL, lambda c: c.options('predict')),
    'health': ('GET', f'{BASE_URL}/health', lambda c: c.health()),
    'status_json': ('GET', STATUS_URL, lambda c: _execution(c).status_json()),
    'result': ('GET', RESULT_URL, lambda c: _execution(c).result()),
}


@pytest.fixture
def inference_client():
    return InferenceClient(inference_key='key-123', endpoint_base_url=BASE_URL)


@pytest.fixture
def following_client():
    return InferenceClient(
        inference_key='key-123', endpoint_base_url=BASE_URL, follow_redirects=True
    )


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


class TestRedirectResponses:
    """A 3xx response is reported to the caller as an error."""

    @pytest.mark.parametrize('status', REDIRECT_STATUSES)
    @pytest.mark.parametrize('entry_point', list(ENTRY_POINTS))
    def test_request_redirect_failed(self, inference_client, entry_point, status):
        # arrange
        method, url, call = ENTRY_POINTS[entry_point]
        responses.add(method, url, status=status, headers={'Location': REDIRECT_URL})
        for target_method in ('GET', method):
            responses.add(target_method, REDIRECT_URL, json={'Id': EXECUTION_ID})

        # act
        with pytest.raises(InferenceClientError, match=rf'redirect \({status}\)'):
            call(inference_client)

        # assert
        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == url

    def test_request_redirect_to_another_host_failed(self, inference_client):
        # arrange
        inference_client.set_global_header('X-Request-Source', 'tests')
        target = 'https://other.example.net/moved'
        responses.add(responses.POST, PREDICT_URL, status=307, headers={'Location': target})
        responses.add(responses.POST, target, json={})

        # act
        with pytest.raises(InferenceClientError, match='redirects are not followed'):
            inference_client.run_sync({'a': 1}, path='predict')

        # assert
        assert len(responses.calls) == 1

    def test_session_redirect_returned_as_is_successful(self, inference_client):
        # arrange
        responses.add(responses.GET, PREDICT_URL, status=307, headers={'Location': REDIRECT_URL})
        responses.add(responses.GET, REDIRECT_URL, json={})

        # act
        response = inference_client._session.get(PREDICT_URL, allow_redirects=True)

        # assert
        assert response.status_code == 307
        assert len(responses.calls) == 1

    def test_request_redirect_inside_deployment_by_default_failed(self, inference_client):
        # arrange
        responses.add(responses.GET, PREDICT_URL, status=307, headers={'Location': MOVED_URL})
        responses.add(responses.GET, MOVED_URL, json={})

        # act
        with pytest.raises(InferenceClientError, match='redirects are not followed'):
            inference_client.get('predict')

        # assert
        assert inference_client.follow_redirects is False
        assert len(responses.calls) == 1

    @pytest.mark.parametrize(
        ('path', 'location', 'hint'),
        [
            ('predict', f'{PREDICT_URL}/', 'add a trailing slash to `path`'),
            ('predict', '/predict/', 'add a trailing slash to `path`'),
            ('predict/', PREDICT_URL, 'remove the trailing slash from `path`'),
            ('predict/', '/predict', 'remove the trailing slash from `path`'),
        ],
    )
    def test_request_redirect_trailing_slash_failed(self, inference_client, path, location, hint):
        # arrange
        responses.add(
            responses.GET, f'{BASE_URL}/{path}', status=307, headers={'Location': location}
        )

        # act
        with pytest.raises(InferenceClientError) as excinfo:
            inference_client.get(path)

        # assert
        assert str(excinfo.value).endswith(hint)

    def test_request_redirect_to_another_path_has_no_hint_failed(self, inference_client):
        # arrange
        responses.add(responses.GET, PREDICT_URL, status=307, headers={'Location': MOVED_URL})

        # act
        with pytest.raises(InferenceClientError) as excinfo:
            inference_client.get('predict')

        # assert
        assert str(excinfo.value).endswith('redirects are not followed')

    @pytest.mark.parametrize(
        ('status', 'headers'),
        [
            (304, {}),
            (304, {'Location': MOVED_URL}),
            (300, {}),
            (307, {}),
        ],
    )
    @pytest.mark.parametrize('follow_redirects', [False, True])
    def test_request_non_redirect_3xx_successful(self, follow_redirects, status, headers):
        # arrange
        client = InferenceClient(
            inference_key='key-123', endpoint_base_url=BASE_URL, follow_redirects=follow_redirects
        )
        responses.add(responses.GET, PREDICT_URL, status=status, headers=headers)

        # act
        response = client.get('predict')

        # assert
        assert response.status_code == status
        assert len(responses.calls) == 1

    @pytest.mark.parametrize(
        'location',
        [
            'https://[invalid',
            'https://[invalid/v1/my-deployment/moved',
            'https://inference.example.com:99999/v1/my-deployment/moved',
        ],
    )
    @pytest.mark.parametrize('follow_redirects', [False, True])
    def test_request_redirect_malformed_location_failed(self, follow_redirects, location):
        # arrange
        client = InferenceClient(
            inference_key='key-123', endpoint_base_url=BASE_URL, follow_redirects=follow_redirects
        )
        responses.add(responses.GET, PREDICT_URL, status=307, headers={'Location': location})

        # act
        with pytest.raises(InferenceClientError, match=r'redirect \(307\)'):
            client.get('predict')

        # assert
        assert len(responses.calls) == 1


class TestFollowRedirects:
    """With `follow_redirects=True`, only a redirect inside the deployment is followed."""

    @pytest.mark.parametrize(
        ('location', 'target'),
        [
            (MOVED_URL, MOVED_URL),
            ('/v1/my-deployment/moved', MOVED_URL),
            ('moved', MOVED_URL),
            ('/v1/my-deployment/a/b?q=1', f'{BASE_URL}/a/b?q=1'),
            ('/v1/my-deployment', BASE_URL),
            ('/v1/my-deployment/v1/models/m:predict', f'{BASE_URL}/v1/models/m:predict'),
        ],
    )
    @pytest.mark.parametrize('status', REDIRECT_STATUSES)
    def test_follow_redirect_inside_deployment_successful(
        self, following_client, status, location, target
    ):
        # arrange
        responses.add(responses.GET, PREDICT_URL, status=status, headers={'Location': location})
        responses.add(
            responses.GET,
            target,
            json={'out': 1},
            match=[matchers.header_matcher({'Authorization': 'Bearer key-123'})],
        )

        # act
        response = following_client.get('predict')

        # assert
        assert response.json() == {'out': 1}
        assert len(responses.calls) == 2
        assert responses.calls[1].request.url == target

    @pytest.mark.parametrize('status', [307, 308])
    def test_follow_redirect_keeps_method_and_body_successful(self, following_client, status):
        # arrange
        responses.add(responses.POST, PREDICT_URL, status=status, headers={'Location': MOVED_URL})
        responses.add(
            responses.POST,
            MOVED_URL,
            json={'out': 1},
            match=[matchers.json_params_matcher({'a': 1})],
        )

        # act
        response = following_client.run_sync({'a': 1}, path='predict')

        # assert
        assert response.output() == {'out': 1}
        assert responses.calls[1].request.method == 'POST'

    @pytest.mark.parametrize('status', [301, 302, 303])
    def test_follow_redirect_changes_post_to_get_successful(self, following_client, status):
        # arrange
        responses.add(responses.POST, PREDICT_URL, status=status, headers={'Location': MOVED_URL})
        responses.add(responses.GET, MOVED_URL, json={'out': 1})

        # act
        response = following_client.run_sync({'a': 1}, path='predict')

        # assert
        assert response.output() == {'out': 1}
        assert responses.calls[1].request.method == 'GET'
        assert responses.calls[1].request.body is None

    @pytest.mark.parametrize(
        'location',
        [
            # another deployment
            'https://inference.example.com/v1/other-deployment/moved',
            '/v1/other-deployment/moved',
            '/v1/moved',
            # a deployment whose name starts with this one
            '/v1/my-deployment-2/moved',
            'https://inference.example.com/v1/my-deployment-2',
            # relative path segments, plain and encoded
            '../other-deployment/moved',
            '/v1/my-deployment/../other-deployment/moved',
            '/v1/my-deployment/%2e%2e/other-deployment/moved',
            '/v1/my-deployment/%2E%2E/other-deployment/moved',
            '/v1/my-deployment/..%2Fother-deployment/moved',
            '/v1/my-deployment/a/..%2F..%2F..%2Fother-deployment',
            '/v1/my-deployment/./moved',
            '/v1/my-deployment/..;/other-deployment/moved',
            '/v1/my-deployment/..%252f..%252fother-deployment',
            # characters that `path` does not allow
            '/v1/my-deployment/a%20b',
            '/v1/my-deployment/a;b',
            '/v1/my-deployment/a\\b',
            # another host
            'https://other.example.net/v1/my-deployment/moved',
            '//other.example.net/v1/my-deployment/moved',
            # another scheme
            'http://inference.example.com/v1/my-deployment/moved',
            # another port
            'https://inference.example.com:8443/v1/my-deployment/moved',
            'https://inference.example.com:bad/v1/my-deployment/moved',
            # user info
            'https://user@inference.example.com/v1/my-deployment/moved',
        ],
    )
    @pytest.mark.parametrize('status', REDIRECT_STATUSES)
    def test_follow_redirect_outside_deployment_failed(self, following_client, status, location):
        # arrange
        responses.add(responses.POST, PREDICT_URL, status=status, headers={'Location': location})

        # act
        with pytest.raises(InferenceClientError, match=rf'redirect \({status}\)') as excinfo:
            following_client.run_sync({'a': 1}, path='predict')

        # assert
        assert 'failed the follow_redirects check' in str(excinfo.value)
        assert len(responses.calls) == 1

    def test_follow_redirect_stops_at_rejected_hop_failed(self, following_client):
        # arrange
        location = 'https://other.example.net/moved'
        responses.add(responses.GET, PREDICT_URL, status=307, headers={'Location': MOVED_URL})
        responses.add(responses.GET, MOVED_URL, status=307, headers={'Location': location})

        # act
        with pytest.raises(InferenceClientError, match=location):
            following_client.get('predict')

        # assert
        assert len(responses.calls) == 2

    def test_follow_redirect_hop_limit_failed(self, following_client):
        # arrange
        responses.add(
            responses.GET, PREDICT_URL, status=307, headers={'Location': f'{BASE_URL}/hop-1'}
        )
        for hop in range(1, 10):
            responses.add(
                responses.GET,
                f'{BASE_URL}/hop-{hop}',
                status=307,
                headers={'Location': f'{BASE_URL}/hop-{hop + 1}'},
            )

        # act
        with pytest.raises(InferenceClientError, match='Exceeded 5 redirects'):
            following_client.get('predict')

        # assert
        assert len(responses.calls) == 6

    @pytest.mark.parametrize('entry_point', ['status_json', 'result'])
    @pytest.mark.parametrize('status', REDIRECT_STATUSES)
    def test_async_request_redirect_failed(self, following_client, entry_point, status):
        # arrange
        _, url, call = ENTRY_POINTS[entry_point]
        responses.add(responses.GET, url, status=status, headers={'Location': MOVED_URL})
        responses.add(responses.GET, MOVED_URL, json={'Status': 'Completed'})

        # act
        with pytest.raises(InferenceClientError, match='redirects are not followed'):
            call(following_client)

        # assert
        assert len(responses.calls) == 1

    def test_session_redirect_outside_deployment_returned_as_is_successful(self, following_client):
        # arrange
        responses.add(responses.GET, PREDICT_URL, status=307, headers={'Location': REDIRECT_URL})
        responses.add(responses.GET, REDIRECT_URL, json={})

        # act
        response = following_client._session.get(PREDICT_URL, allow_redirects=True)

        # assert
        assert response.status_code == 307
        assert len(responses.calls) == 1


class TestRequests:
    """Successful inference requests."""

    def test_run_sync_successful(self, inference_client):
        # arrange
        responses.add(
            responses.POST,
            PREDICT_URL,
            json={'out': 1},
            match=[
                matchers.json_params_matcher({'a': 1}),
                matchers.header_matcher({'Authorization': 'Bearer key-123', 'X-Extra': 'x'}),
            ],
        )

        # act
        response = inference_client.run_sync({'a': 1}, path='predict', headers={'X-Extra': 'x'})

        # assert
        assert response.status_code == 200
        assert response.output() == {'out': 1}

    def test_run_sync_stream_successful(self, inference_client):
        # arrange
        responses.add(
            responses.POST,
            PREDICT_URL,
            body='line 1\nline 2\n',
            content_type='text/event-stream',
        )

        # act
        response = inference_client.run_sync({'a': 1}, path='predict', stream=True)

        # assert
        assert list(response.stream()) == [b'line 1', b'line 2']

    def test_run_then_status_and_result_successful(self, inference_client):
        # arrange
        responses.add(
            responses.POST,
            PREDICT_URL,
            json={'Id': EXECUTION_ID},
            match=[matchers.header_matcher({'Prefer': 'respond-async'})],
        )
        inference_id = matchers.header_matcher(
            {'Authorization': 'Bearer key-123', 'X-Inference-Id': EXECUTION_ID}
        )
        responses.add(responses.GET, STATUS_URL, json={'Status': 'Completed'}, match=[inference_id])
        responses.add(responses.GET, RESULT_URL, json={'out': 1}, match=[inference_id])

        # act
        execution = inference_client.run({'a': 1}, path='predict')
        status = execution.status_json()
        result = execution.result()

        # assert
        assert execution.id == EXECUTION_ID
        assert status == {'Status': 'Completed'}
        assert execution.status() == AsyncStatus.Completed
        assert result == {'out': 1}

    def test_result_text_successful(self, inference_client):
        # arrange
        responses.add(responses.GET, RESULT_URL, body='plain', content_type='text/plain')

        # act
        result = _execution(inference_client).result()

        # assert
        assert result == {'result': 'plain'}

    @pytest.mark.parametrize('entry_point', ['status_json', 'result'])
    def test_async_requests_client_timeout_successful(self, inference_client, entry_point):
        # arrange
        _, url, call = ENTRY_POINTS[entry_point]
        responses.add(responses.GET, url, json={'Status': 'Completed'})

        # act
        call(inference_client)

        # assert
        assert responses.calls[0].request.req_kwargs['timeout'] == inference_client.timeout_seconds

    @pytest.mark.parametrize('entry_point', ['status_json', 'result'])
    def test_async_requests_failed(self, inference_client, entry_point):
        # arrange
        _, url, call = ENTRY_POINTS[entry_point]
        responses.add(responses.GET, url, status=500, json={'error': 'boom'})

        # act
        with pytest.raises(InferenceClientError, match='500'):
            call(inference_client)

    @pytest.mark.parametrize('entry_point', ['status_json', 'result'])
    def test_async_requests_timeout_failed(self, inference_client, entry_point):
        # arrange
        _, url, call = ENTRY_POINTS[entry_point]
        responses.add(responses.GET, url, body=requests.exceptions.ReadTimeout())

        # act
        with pytest.raises(InferenceClientError, match='timed out'):
            call(inference_client)

    @pytest.mark.parametrize(
        'entry_point', ['get', 'post', 'put', 'delete', 'patch', 'head', 'options']
    )
    def test_http_method_helpers_successful(self, inference_client, entry_point):
        # arrange
        method, url, call = ENTRY_POINTS[entry_point]
        responses.add(method, url, status=200)

        # act
        response = call(inference_client)

        # assert
        assert response.status_code == 200
        assert len(responses.calls) == 1

    @pytest.mark.parametrize(
        'entry_point', ['get', 'post', 'put', 'delete', 'patch', 'head', 'options', 'health']
    )
    def test_http_method_helpers_client_timeout_successful(self, inference_client, entry_point):
        # arrange
        method, url, call = ENTRY_POINTS[entry_point]
        responses.add(method, url, status=200)

        # act
        call(inference_client)

        # assert
        assert responses.calls[0].request.req_kwargs['timeout'] == inference_client.timeout_seconds

    def test_http_method_helpers_explicit_timeout_successful(self, inference_client):
        # arrange
        responses.add(responses.GET, PREDICT_URL, status=200)

        # act
        inference_client.get('predict', timeout_seconds=7)

        # assert
        assert responses.calls[0].request.req_kwargs['timeout'] == 7

    def test_get_with_params_successful(self, inference_client):
        # arrange
        responses.add(
            responses.GET,
            PREDICT_URL,
            json={},
            match=[matchers.query_param_matcher({'q': 'x'})],
        )

        # act
        response = inference_client.get('predict', params={'q': 'x'})

        # assert
        assert response.status_code == 200

    def test_health_successful(self, inference_client):
        # arrange
        responses.add(responses.GET, f'{BASE_URL}/health', json={'ok': True})

        # act
        response = inference_client.health()

        # assert
        assert response.json() == {'ok': True}
