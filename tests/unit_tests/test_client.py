import pytest
import responses  # https://github.com/getsentry/responses

from verda import VerdaClient
from verda.exceptions import APIException

BASE_URL = 'https://api.example.com/v1'

response_json = {
    'access_token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJoZXkiOiJ5b3UgYWN1YWxseSBjaGVja2VkIHRoaXM_In0.0RjcdKQ1NJP9gbRyXITE6LFFLwKGzeeshuubnkkfkb8',
    'token_type': 'Bearer',
    'expires_in': 3600,
    'refresh_token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ3b3ciOiJhbmQgdGhpcyB0b28_In0.AC5gk-o-MOptUgrouEErlhr8WT3Hg_RR6px6A0I7ZEk',
    'scope': 'fullAccess',
}


class TestVerdaClient:
    @responses.activate
    def test_client(self):
        # arrange - add response mock
        responses.add(responses.POST, BASE_URL + '/oauth2/token', json=response_json, status=200)

        # act
        client = VerdaClient('XXXXXXXXXXXXXX', 'XXXXXXXXXXXXXX', BASE_URL)

        # assert
        assert client.constants.base_url == BASE_URL
        assert hasattr(client, 'container_types')
        assert hasattr(client, 'cluster_types')
        assert hasattr(client, 'job_deployments')

    @responses.activate
    def test_client_with_default_base_url(self):
        # arrange - add response mock
        DEFAULT_BASE_URL = 'https://api.verda.com/v1'
        responses.add(
            responses.POST,
            DEFAULT_BASE_URL + '/oauth2/token',
            json=response_json,
            status=200,
        )

        # act
        client = VerdaClient('XXXXXXXXXXXXXX', 'XXXXXXXXXXXXXX')

        # assert
        assert client.constants.base_url == DEFAULT_BASE_URL

    @responses.activate
    def test_invalid_client_credentials(self):
        # arrange - add response mock
        responses.add(
            responses.POST,
            BASE_URL + '/oauth2/token',
            json={
                'code': 'unauthorized_request',
                'message': 'Invalid client id or client secret',
            },
            status=401,
        )

        # act
        with pytest.raises(APIException) as excinfo:
            VerdaClient('x', 'y', BASE_URL)

        # assert
        assert excinfo.value.code == 'unauthorized_request'
        assert excinfo.value.message == 'Invalid client id or client secret'
