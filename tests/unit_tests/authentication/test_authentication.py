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

import time

import pytest
import responses  # https://github.com/getsentry/responses
from responses import matchers

from verda.authentication import AuthenticationService
from verda.exceptions import APIException

INVALID_REQUEST = 'invalid_request'
INVALID_REQUEST_MESSAGE = 'Your existence is invalid'

BASE_URL = 'https://api.example.com/v1'
CLIENT_ID = '0123456789xyz'
CLIENT_SECRET = 'zyx987654321'

ACCESS_TOKEN = 'access'
REFRESH_TOKEN = 'refresh'
SCOPE = 'fullAccess'
TOKEN_TYPE = 'Bearer'
EXPIRES_IN = 3600

ACCESS_TOKEN2 = 'access2'
REFRESH_TOKEN2 = 'refresh2'


class TestAuthenticationService:
    @pytest.fixture
    def authentication_service(self):
        return AuthenticationService(CLIENT_ID, CLIENT_SECRET, BASE_URL)

    @pytest.fixture
    def endpoint(self, http_client):
        return http_client._base_url + '/oauth2/token'

    def test_authenticate_successful(self, authentication_service, endpoint):
        # arrange - add response mock
        responses.add(
            responses.POST,
            endpoint,
            json={
                'access_token': ACCESS_TOKEN,
                'refresh_token': REFRESH_TOKEN,
                'scope': SCOPE,
                'token_type': TOKEN_TYPE,
                'expires_in': EXPIRES_IN,
            },
            status=200,
        )

        # act
        auth_data = authentication_service.authenticate()

        # assert
        assert isinstance(auth_data, dict)
        assert authentication_service._access_token == ACCESS_TOKEN
        assert authentication_service._refresh_token == REFRESH_TOKEN
        assert authentication_service._scope == SCOPE
        assert authentication_service._token_type == TOKEN_TYPE
        assert authentication_service._expires_at is not None
        assert responses.assert_call_count(endpoint, 1) is True

    def test_authenticate_failed(self, authentication_service, endpoint):
        # arrange - add response mock
        responses.add(
            responses.POST,
            endpoint,
            json={'code': INVALID_REQUEST, 'message': INVALID_REQUEST_MESSAGE},
            status=400,
        )

        # act
        with pytest.raises(APIException) as excinfo:
            authentication_service.authenticate()

        # assert
        assert excinfo.value.code == INVALID_REQUEST
        assert excinfo.value.message == INVALID_REQUEST_MESSAGE
        assert responses.assert_call_count(endpoint, 1) is True
        assert (
            responses.calls[0].request.body
            == f'{{"grant_type": "client_credentials", "client_id": "{CLIENT_ID}", "client_secret": "{CLIENT_SECRET}"}}'.encode()
        )

    def test_refresh_successful(self, authentication_service, endpoint):
        # add a response for the client credentials grant
        responses.add(
            responses.POST,
            endpoint,
            json={
                'access_token': ACCESS_TOKEN,
                'refresh_token': REFRESH_TOKEN,
                'scope': SCOPE,
                'token_type': TOKEN_TYPE,
                'expires_in': EXPIRES_IN,
            },
            match=[
                matchers.json_params_matcher(
                    {
                        'grant_type': 'client_credentials',
                        'client_id': CLIENT_ID,
                        'client_secret': CLIENT_SECRET,
                    }
                )
            ],
            status=200,
        )

        # add another response for the refresh token grant
        responses.add(
            responses.POST,
            endpoint,
            json={
                'access_token': ACCESS_TOKEN2,
                'refresh_token': REFRESH_TOKEN2,
                'scope': SCOPE,
                'token_type': TOKEN_TYPE,
                'expires_in': EXPIRES_IN,
            },
            match=[
                matchers.json_params_matcher(
                    {'grant_type': 'refresh_token', 'refresh_token': REFRESH_TOKEN}
                )
            ],
            status=200,
        )

        # act
        auth_data = authentication_service.authenticate()  # authenticate first

        # assert
        assert isinstance(auth_data, dict)
        assert authentication_service._access_token == ACCESS_TOKEN
        assert authentication_service._refresh_token == REFRESH_TOKEN
        assert authentication_service._scope == SCOPE
        assert authentication_service._token_type == TOKEN_TYPE
        assert authentication_service._expires_at is not None
        assert (
            responses.calls[0].request.body
            == f'{{"grant_type": "client_credentials", "client_id": "{CLIENT_ID}", "client_secret": "{CLIENT_SECRET}"}}'.encode()
        )

        auth_data2 = authentication_service.refresh()  # refresh

        assert isinstance(auth_data2, dict)
        assert authentication_service._access_token == ACCESS_TOKEN2
        assert authentication_service._refresh_token == REFRESH_TOKEN2
        assert authentication_service._scope == SCOPE
        assert authentication_service._token_type == TOKEN_TYPE
        assert authentication_service._expires_at is not None
        assert (
            responses.calls[1].request.body
            == f'{{"grant_type": "refresh_token", "refresh_token": "{REFRESH_TOKEN}"}}'.encode()
        )
        assert responses.assert_call_count(endpoint, 2) is True

    def test_refresh_failed(self, authentication_service, endpoint):
        # arrange - add responses mock
        # first response for authentication - ok
        responses.add(
            responses.POST,
            endpoint,
            json={
                'access_token': ACCESS_TOKEN,
                'refresh_token': REFRESH_TOKEN,
                'scope': SCOPE,
                'token_type': TOKEN_TYPE,
                'expires_in': EXPIRES_IN,
            },
            match=[
                matchers.json_params_matcher(
                    {
                        'grant_type': 'client_credentials',
                        'client_id': CLIENT_ID,
                        'client_secret': CLIENT_SECRET,
                    }
                )
            ],
            status=200,
        )

        # second response for the refresh - failed
        responses.add(
            responses.POST,
            endpoint,
            json={'code': INVALID_REQUEST, 'message': INVALID_REQUEST_MESSAGE},
            match=[
                matchers.json_params_matcher(
                    {'grant_type': 'refresh_token', 'refresh_token': REFRESH_TOKEN}
                )
            ],
            status=500,
        )

        # act
        authentication_service.authenticate()  # authenticate first

        with pytest.raises(APIException) as excinfo:
            authentication_service.refresh()

        # assert
        assert excinfo.value.code == INVALID_REQUEST
        assert excinfo.value.message == INVALID_REQUEST_MESSAGE
        assert responses.assert_call_count(endpoint, 2) is True
        assert (
            responses.calls[0].request.body
            == f'{{"grant_type": "client_credentials", "client_id": "{CLIENT_ID}", "client_secret": "{CLIENT_SECRET}"}}'.encode()
        )
        assert (
            responses.calls[1].request.body
            == f'{{"grant_type": "refresh_token", "refresh_token": "{REFRESH_TOKEN}"}}'.encode()
        )

    def test_is_expired(self, authentication_service):
        # arrange
        current_time = time.time()
        future_time = current_time + 3600

        # act
        # set the expired_at as current time
        authentication_service._expires_at = current_time
        is_expired_current = authentication_service.is_expired()

        # set the expired_at as future time
        authentication_service._expires_at = future_time
        is_expired_future = authentication_service.is_expired()

        # assert
        assert is_expired_current
        assert not is_expired_future
