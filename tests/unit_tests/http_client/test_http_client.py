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

from unittest.mock import Mock

import pytest
import responses  # https://github.com/getsentry/responses

from verda.exceptions import APIException

INVALID_REQUEST = 'invalid_request'
INVALID_REQUEST_MESSAGE = 'Your existence is invalid'

UNAUTHORIZED_REQUEST = 'unauthorized_request'
UNAUTHORIZED_REQUEST_MESSAGE = 'Access token is missing or invalid'


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
