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

import re
import uuid
from unittest.mock import Mock

import pytest
import requests
import responses  # https://github.com/getsentry/responses

from verda.exceptions import APIException
from verda.http_client._http_client import _encode_path_segment, handle_error

INVALID_REQUEST = 'invalid_request'
INVALID_REQUEST_MESSAGE = 'Your existence is invalid'

UNAUTHORIZED_REQUEST = 'unauthorized_request'
UNAUTHORIZED_REQUEST_MESSAGE = 'Access token is missing or invalid'


@pytest.mark.parametrize(
    'value',
    ['my-deployment', 'a1b2c3', 'name_with.dots-and~tilde', 'UPPER123'],
)
def test_encode_path_segment_leaves_ordinary_names_unchanged(value):
    assert _encode_path_segment(value) == value


@pytest.mark.parametrize(
    'value',
    [
        'a/b',
        'docker.io/myorg',
        '../../v1/balance',
        '../ssh-keys',
        'nested/../../escape',
        'a/./b',
        'a/..',
        # some servers normalise '\' to a separator
        '..\\..\\v1\\balance',
        'a\\b',
    ],
)
def test_encode_path_segment_rejects_path_separators(value):
    # '%2F' survives to the wire, but any intermediary that unescapes before
    # normalising (Envoy's UNESCAPE_AND_FORWARD) turns '..%2F..%2Fv1%2Finstances'
    # back into a working traversal.
    with pytest.raises(ValueError, match='only letters, digits'):
        _encode_path_segment(value)


@pytest.mark.parametrize(
    'value',
    ['x?force=true&', 'name#fragment', 'a b', 'a;b', 'ünicode', 'name@host', 'a+b'],
)
def test_encode_path_segment_rejects_characters_outside_the_unreserved_set(value):
    # These were previously percent-encoded and sent.
    with pytest.raises(ValueError, match='only letters, digits'):
        _encode_path_segment(value)


@pytest.mark.parametrize('value', ['%2E', '%2e%2E', '..%2F..', 'my%20deployment', '100%'])
def test_encode_path_segment_rejects_a_percent_sign(value):
    # A pre-encoded name is caller error: pass the raw name.
    with pytest.raises(ValueError, match='only letters, digits'):
        _encode_path_segment(value)


@pytest.mark.parametrize('value', ['.', '..'])
def test_encode_path_segment_rejects_relative_segments(value):
    # RFC 3986 dot-segments cannot be neutralised by encoding: `quote` leaves '.'
    # alone (it is unreserved) and encoding it as '%2E' does not help either, because
    # `requests.utils.requote_uri` decodes percent-encoded unreserved characters back
    # before the request goes on the wire.
    with pytest.raises(ValueError, match='relative path segment'):
        _encode_path_segment(value)


def test_encode_path_segment_rejects_an_empty_value():
    # An empty segment collapses the URL onto the collection endpoint, which turns
    # a delete-one call into a delete-all call.
    with pytest.raises(ValueError, match='must be a non-empty string'):
        _encode_path_segment('')


@pytest.mark.parametrize('value', [None, 3.5, b'abc', True])
def test_encode_path_segment_reports_a_wrong_type_as_a_type_problem(value):
    # The message has to name the real cause: 3.5 and None are not empty strings.
    with pytest.raises(ValueError, match='must be a str, int or UUID'):
        _encode_path_segment(value)


def test_encode_path_segment_allows_dots_inside_a_name():
    assert _encode_path_segment('v1.2.3') == 'v1.2.3'
    assert _encode_path_segment('..leading') == '..leading'


class TestBuildPath:
    """`path_params` values are encoded by the client, so call sites cannot forget."""

    def test_template_without_path_params_is_returned_unchanged(self, http_client):
        assert http_client._build_path('/instances', None) == '/instances'
        assert http_client._build_path('/long-term/periods/clusters', {}) == (
            '/long-term/periods/clusters'
        )

    def test_ordinary_values_are_substituted(self, http_client):
        path = http_client._build_path(
            '/container-deployments/{name}/status', {'name': 'my-deployment'}
        )
        assert path == '/container-deployments/my-deployment/status'

    def test_multiple_params_are_substituted(self, http_client):
        path = http_client._build_path(
            '/container-deployments/{name}/replicas/{replica}',
            {'name': 'dep', 'replica': 'r-1'},
        )
        assert path == '/container-deployments/dep/replicas/r-1'

    @pytest.mark.parametrize(
        'value',
        ['a/b', 'x?force=true&', 'name#frag', 'a b', '..\\..\\x', '%2E%2E'],
    )
    def test_hostile_values_are_rejected(self, http_client, value):
        with pytest.raises(ValueError, match='only letters, digits'):
            http_client._build_path('/secrets/{name}', {'name': value})

    @pytest.mark.parametrize('value', ['../../v1/instances', 'nested/../escape'])
    def test_values_containing_dot_segments_are_rejected(self, http_client, value):
        with pytest.raises(ValueError, match='path segment must'):
            http_client._build_path('/secrets/{name}', {'name': value})

    @pytest.mark.parametrize('value', ['.', '..', '', None])
    def test_values_that_cannot_be_encoded_are_rejected(self, http_client, value):
        with pytest.raises(ValueError, match='path segment must'):
            http_client._build_path('/secrets/{name}', {'name': value})

    def test_placeholder_without_a_value_is_rejected(self, http_client):
        # Otherwise the literal '{id}' would be sent as the resource id.
        with pytest.raises(ValueError, match='unsubstituted placeholder'):
            http_client._build_path('/instances/{id}', None)

    def test_placeholder_missing_from_path_params_raises(self, http_client):
        # 'a' is supplied and used, 'b' has no value at all. Every template/params
        # mismatch reports as ValueError, matching what the request methods document.
        with pytest.raises(ValueError, match='no value given for placeholder'):
            http_client._build_path('/x/{a}/{b}', {'a': '1'})

    def test_misspelled_key_reports_the_unused_parameter(self, http_client):
        # Both wrong at once; the unused-key message names the actual mistake.
        with pytest.raises(ValueError, match='unused path parameter'):
            http_client._build_path('/instances/{id}', {'wrong_name': 'x'})

    def test_path_param_the_template_does_not_use_is_rejected(self, http_client):
        # A stale key left behind after a template was renamed: the caller believes
        # the value is being sent, but it silently is not.
        with pytest.raises(ValueError, match='unused path parameter'):
            http_client._build_path('/instances/{id}', {'id': 'x', 'stale': 'y'})

    @pytest.mark.parametrize(
        ('value', 'expected'),
        [
            (123, '123'),
            (
                uuid.UUID('0c41e387-8b12-4b4b-9c1e-000000000001'),
                '0c41e387-8b12-4b4b-9c1e-000000000001',
            ),
        ],
    )
    def test_non_string_values_are_coerced_not_rejected(self, http_client, value, expected):
        # Before path_params these were interpolated by an f-string, so rejecting them
        # would be an undocumented breaking change for callers passing ints or UUIDs.
        assert http_client._build_path('/instances/{id}', {'id': value}) == f'/instances/{expected}'

    @pytest.mark.parametrize('value', [b'abc', ['a'], {'k': 'v'}, 3.5])
    def test_types_that_are_not_identifiers_are_rejected(self, http_client, value):
        # str() on these yields a nonsense segment (b'abc' -> "b'abc'"), producing a
        # confusing 404 instead of an error at the call site.
        with pytest.raises(ValueError, match='path segment must be'):
            http_client._build_path('/instances/{id}', {'id': value})


class TestHttpClient:
    def test_add_base_url(self, http_client):
        # arrange
        path = '/test'
        base = http_client._base_url

        # act
        url = http_client._add_base_url(path)

        # assert
        assert base == http_client._base_url
        assert url == base + path

    @pytest.mark.parametrize(
        'path',
        [
            '/container-deployments/../../v1/instances',
            '/container-deployments/..',
            '/instances/../ssh-keys',
            '/volumes/.',
            '/scripts/./x',
        ],
    )
    def test_add_base_url_rejects_relative_path_segments(self, http_client, path):
        # A call site that skips path_params must not be able to retarget the request.
        with pytest.raises(ValueError, match='escape the API base path'):
            http_client._add_base_url(path)

    @pytest.mark.parametrize(
        'path',
        [
            '/container-deployments/%2E%2E',
            '/volumes/%2e',
            '/x/%2E%2E/%zz',
            '/container-deployments/..%2F..%2Fv1%2Finstances',
            '/container-deployments/..%2f..%2fv1%2Finstances',
            '/instances/%2E%2E%2Fssh-keys',
            '/volumes/..%5C..%5Cadmin',
            '/volumes/..\\..\\admin',
        ],
    )
    def test_add_base_url_rejects_an_escape_or_backslash_outright(self, http_client, path):
        # Neither can appear in a path the client built: `_encode_path_segment` refuses
        # both and endpoint constants are plain literals.
        with pytest.raises(ValueError, match='unencoded value'):
            http_client._add_base_url(path)

    @pytest.mark.parametrize('path', ['/container-deployments/', '/volumes//x'])
    def test_add_base_url_rejects_an_empty_path_segment(self, http_client, path):
        # An empty segment collapses the request onto the collection endpoint, turning
        # a delete-one into a delete-all.
        with pytest.raises(ValueError, match='empty path segment'):
            http_client._add_base_url(path)

    @pytest.mark.parametrize(
        'path',
        ['/secrets/x?force=true&', '/secrets/x#frag'],
    )
    def test_add_base_url_rejects_a_query_string_in_the_path(self, http_client, path):
        # Query data is passed separately as `params`, so a '?' reaching here means an
        # unencoded value was interpolated into the path -- the injection half of the
        # traversal bug, which the dot-segment check alone does not catch.
        with pytest.raises(ValueError, match='query string or fragment'):
            http_client._add_base_url(path)

    @pytest.mark.parametrize(
        'path',
        [
            '/container-deployments/my-deployment',
            '/container-registry-credentials/my-dockerhub-creds',
            '/instance-availability/1H100.80S.22V',
            '/volumes/name.with.dots',
            '/volumes/..leading',
            '/long-term/periods/clusters',
        ],
    )
    def test_add_base_url_allows_encoded_and_ordinary_paths(self, http_client, path):
        assert http_client._add_base_url(path) == http_client._base_url + path

    def test_generate_bearer_header(self, http_client):
        bearer_string = http_client._generate_bearer_header()
        access_token = http_client._auth_service._access_token

        assert isinstance(bearer_string, str)
        assert bearer_string == f'Bearer {access_token}'

    def test_generate_user_agent(self, http_client):
        # arrange
        version = http_client._version
        client_id_truncated = http_client._auth_service._client_id[0:10]

        # act
        user_agent_string = http_client._generate_user_agent()

        # assert
        assert isinstance(user_agent_string, str)
        assert user_agent_string == f'datacrunch-python-v{version}-{client_id_truncated}'

    def test_generate_headers(self, http_client):
        # arrange / act
        headers = http_client._generate_headers()
        authorization_string = http_client._generate_bearer_header()
        user_agent_string = http_client._generate_user_agent()

        # assert
        assert isinstance(headers, dict)
        assert isinstance(headers['Content-Type'], str)
        assert isinstance(headers['Authorization'], str)
        assert isinstance(headers['User-Agent'], str)
        assert headers['Content-Type'] == 'application/json'
        assert headers['Authorization'] == authorization_string
        assert headers['User-Agent'] == user_agent_string

    @pytest.mark.parametrize('method', ['get', 'post', 'put', 'patch', 'delete'])
    @responses.activate
    def test_request_methods_substitute_path_params(self, http_client, method):
        # arrange
        responses.add(getattr(responses, method.upper()), re.compile(r'.*'), json={}, status=200)

        # act
        getattr(http_client, method)(
            '/container-deployments/{name}/status', path_params={'name': 'my-deployment'}
        )

        # assert
        assert responses.calls[0].request.path_url == (
            '/v1/container-deployments/my-deployment/status'
        )

    @pytest.mark.parametrize('method', ['get', 'post', 'put', 'patch', 'delete'])
    @responses.activate
    def test_request_methods_reject_a_hostile_path_param_before_sending(self, http_client, method):
        # arrange
        responses.add(getattr(responses, method.upper()), re.compile(r'.*'), json={}, status=200)

        # act / assert
        with pytest.raises(ValueError, match='path segment must'):
            getattr(http_client, method)(
                '/container-deployments/{name}/status', path_params={'name': 'x?force=true&'}
            )
        assert not responses.calls

    @pytest.mark.parametrize('method', ['get', 'post', 'put', 'patch', 'delete'])
    @responses.activate
    def test_request_methods_reject_unsafe_path_params_before_sending(self, http_client, method):
        # arrange
        responses.add(getattr(responses, method.upper()), re.compile(r'.*'), json={}, status=200)

        # act / assert
        with pytest.raises(ValueError, match='path segment must'):
            getattr(http_client, method)('/secrets/{name}', path_params={'name': '..'})
        assert not responses.calls

    @pytest.mark.parametrize('method', ['get', 'post', 'put', 'patch', 'delete'])
    def test_rejected_path_params_do_not_trigger_a_token_refresh(self, http_client, method):
        # arrange - the fixture reports an expired token, so a refresh would fire
        http_client._auth_service.refresh.reset_mock()
        http_client._auth_service.authenticate.reset_mock()

        # act
        with pytest.raises(ValueError, match='path segment must'):
            getattr(http_client, method)('/secrets/{name}', path_params={'name': '..'})

        # assert - an invalid name must not cost an auth round-trip
        http_client._auth_service.refresh.assert_not_called()
        http_client._auth_service.authenticate.assert_not_called()

    def test_refresh_token_if_expired_refresh_successful(self, http_client):
        # act
        http_client._refresh_token_if_expired()

        # assert
        http_client._auth_service.refresh.assert_called_once()
        http_client._auth_service.is_expired.assert_called()
        http_client._auth_service.authenticate.assert_called_once()

    def test_refresh_token_if_expired_refresh_failed(self, http_client):
        # arrange - make refresh raise an exception
        http_client._auth_service.refresh = Mock(side_effect=Exception())

        # act
        http_client._refresh_token_if_expired()

        # assert
        http_client._auth_service.refresh.assert_called_once()
        http_client._auth_service.is_expired.assert_called()
        assert http_client._auth_service.authenticate.call_count == 2

    def test_get_successful(self, http_client):
        # arrange - add response mock
        responses.add(
            method=responses.GET,
            url=(http_client._base_url + '/test'),
            status=200,
            body='{}',
            content_type='application/json',
        )

        # act
        response = http_client.get('/test')

        # assert
        assert response.ok is True
        assert response.status_code == 200
        assert response.text == '{}'
        assert response.headers['Content-Type'] == 'application/json'
        assert response.json() == {}
        assert responses.assert_call_count(http_client._base_url + '/test', 1) is True

    def test_post_successful(self, http_client):
        # arrange - add response mock
        responses.add(
            method=responses.POST,
            url=(http_client._base_url + '/test'),
            status=200,
            body='{}',
            content_type='application/json',
        )

        # act
        response = http_client.post('/test', params={})

        # assert
        assert response.ok is True
        assert response.status_code == 200
        assert response.text == '{}'
        assert response.headers['Content-Type'] == 'application/json'
        assert response.json() == {}
        assert responses.assert_call_count(http_client._base_url + '/test', 1) is True

    def test_delete_successful(self, http_client):
        # arrange - add response mock
        responses.add(
            method=responses.DELETE,
            url=(http_client._base_url + '/test'),
            status=200,
            content_type='application/json',
        )

        # act
        response = http_client.delete('/test')

        # assert
        assert response.ok is True
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'application/json'
        assert responses.assert_call_count(http_client._base_url + '/test', 1) is True

    def test_get_failed(self, http_client):
        # arrange - add response mock
        responses.add(
            method=responses.GET,
            url=(http_client._base_url + '/test'),
            status=401,
            json={
                'code': UNAUTHORIZED_REQUEST,
                'message': UNAUTHORIZED_REQUEST_MESSAGE,
            },
            content_type='application/json',
        )
        error_str = f'error code: {UNAUTHORIZED_REQUEST}\nmessage: {UNAUTHORIZED_REQUEST_MESSAGE}'

        # act
        with pytest.raises(APIException) as excinfo:
            http_client.get('/test')

        # assert
        assert excinfo.value.code == UNAUTHORIZED_REQUEST
        assert excinfo.value.message == UNAUTHORIZED_REQUEST_MESSAGE
        assert excinfo.value.__str__() == error_str

    def test_post_failed(self, http_client):
        # arrange - add response mock
        responses.add(
            method=responses.POST,
            url=(http_client._base_url + '/test'),
            status=400,
            json={'code': INVALID_REQUEST, 'message': INVALID_REQUEST_MESSAGE},
            content_type='application/json',
        )

        # act
        with pytest.raises(APIException) as excinfo:
            http_client.post('/test', json={'data': '42'})

        # assert
        assert excinfo.value.code == INVALID_REQUEST
        assert excinfo.value.message == INVALID_REQUEST_MESSAGE

    def test_delete_failed(self, http_client):
        # arrange - add response mock
        responses.add(
            method=responses.DELETE,
            url=(http_client._base_url + '/test'),
            status=400,
            json={'code': INVALID_REQUEST, 'message': INVALID_REQUEST_MESSAGE},
            content_type='application/json',
        )

        # act
        with pytest.raises(APIException) as excinfo:
            http_client.delete('/test', json={'data': '42'})

        # assert
        assert excinfo.value.code == INVALID_REQUEST
        assert excinfo.value.message == INVALID_REQUEST_MESSAGE

    @pytest.mark.parametrize('status', [301, 302, 303, 307, 308])
    @pytest.mark.parametrize('method', ['get', 'post', 'put', 'patch', 'delete'])
    def test_request_methods_redirect_failed(self, http_client, method, status):
        # arrange
        url = http_client._base_url + '/test'
        target = http_client._base_url + '/moved'
        responses.add(method.upper(), url, status=status, headers={'Location': target})
        responses.add(method.upper(), target, json={})
        responses.add(responses.GET, target, json={})

        # act
        with pytest.raises(APIException) as excinfo:
            getattr(http_client, method)('/test')

        # assert
        assert excinfo.value.code is None
        assert f'unexpected redirect ({status})' in excinfo.value.message
        assert len(responses.calls) == 1

    @pytest.mark.parametrize('method', ['get', 'post', 'put', 'patch', 'delete'])
    def test_request_methods_accept_allow_redirects_false(self, http_client, method):
        # arrange
        url = http_client._base_url + '/test'
        responses.add(method.upper(), url, json={})

        # act
        response = getattr(http_client, method)('/test', allow_redirects=False)

        # assert
        assert response.status_code == 200
        assert len(responses.calls) == 1

    @pytest.mark.parametrize('method', ['get', 'post', 'put', 'patch', 'delete'])
    def test_request_methods_allow_redirects_true_redirect_failed(self, http_client, method):
        # arrange
        url = http_client._base_url + '/test'
        target = http_client._base_url + '/moved'
        responses.add(method.upper(), url, status=307, headers={'Location': target})
        responses.add(method.upper(), target, json={})

        # act
        with pytest.raises(APIException) as excinfo:
            getattr(http_client, method)('/test', allow_redirects=True)

        # assert
        assert 'unexpected redirect (307)' in excinfo.value.message
        assert len(responses.calls) == 1


def test_handle_error_redirect_failed():
    # arrange
    response = requests.Response()
    response.status_code = 302
    response.headers['Location'] = 'https://api.example.com/v1/moved'

    # act
    with pytest.raises(APIException) as excinfo:
        handle_error(response)

    # assert
    assert excinfo.value.message == (
        "unexpected redirect (302) to 'https://api.example.com/v1/moved'; redirects are not followed"
    )
