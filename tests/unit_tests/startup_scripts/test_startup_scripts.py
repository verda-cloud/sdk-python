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

from verda.exceptions import APIException
from verda.startup_scripts import StartupScript, StartupScriptsService

INVALID_REQUEST = 'invalid_request'
INVALID_REQUEST_MESSAGE = 'Your existence is invalid'

SCRIPT_ID = 'deadc0de-a5d2-4972-ae4e-d429115d055b'
SCRIPT_NAME = 'next episode of _____'
SCRIPT_VALUE = 'this was not in the script!'

script_ID_2 = 'beefbeef-a5d2-4972-ae4e-d429115d055b'

PAYLOAD = [{'id': SCRIPT_ID, 'name': SCRIPT_NAME, 'script': SCRIPT_VALUE}]


class TestStartupScripts:
    @pytest.fixture
    def startup_script_service(self, http_client):
        return StartupScriptsService(http_client)

    @pytest.fixture
    def endpoint(self, http_client):
        return http_client._base_url + '/scripts'

    def test_get_scripts(self, startup_script_service, endpoint):
        # arrange - add response mock
        responses.add(responses.GET, endpoint, json=PAYLOAD, status=200)

        # act
        scripts = startup_script_service.get()

        # assert
        assert isinstance(scripts, list)
        assert len(scripts) == 1
        assert isinstance(scripts[0], StartupScript)
        assert scripts[0].id == SCRIPT_ID
        assert scripts[0].name == SCRIPT_NAME
        assert scripts[0].script == SCRIPT_VALUE
        assert responses.assert_call_count(endpoint, 1) is True

    def test_get_script_by_id_successful(self, startup_script_service, endpoint):
        # arrange - add response mock
        url = endpoint + '/' + SCRIPT_ID
        responses.add(responses.GET, url, json=PAYLOAD, status=200)

        # act
        script = startup_script_service.get_by_id(SCRIPT_ID)

        # assert
        assert isinstance(script, StartupScript)
        assert script.id == SCRIPT_ID
        assert script.name == SCRIPT_NAME
        assert script.script == SCRIPT_VALUE
        assert responses.assert_call_count(url, 1) is True

    def test_get_script_by_id_failed(self, startup_script_service, endpoint):
        # arrange - add response mock
        url = endpoint + '/x'
        responses.add(
            responses.GET,
            url,
            json={'code': INVALID_REQUEST, 'message': INVALID_REQUEST_MESSAGE},
            status=400,
        )

        # act
        with pytest.raises(APIException) as excinfo:
            startup_script_service.get_by_id('x')

        # assert
        assert excinfo.value.code == INVALID_REQUEST
        assert excinfo.value.message == INVALID_REQUEST_MESSAGE
        assert responses.assert_call_count(url, 1) is True

    def test_create_script_successful(self, startup_script_service, endpoint):
        # arrange - add response mock
        responses.add(responses.POST, endpoint, body=SCRIPT_ID, status=201)

        # act
        script = startup_script_service.create(SCRIPT_NAME, SCRIPT_VALUE)

        # assert
        assert isinstance(script, StartupScript)
        assert script.id == SCRIPT_ID
        assert responses.assert_call_count(endpoint, 1) is True

    def test_create_script_failed(self, startup_script_service, endpoint):
        # arrange - add response mock
        responses.add(
            responses.POST,
            endpoint,
            json={'code': INVALID_REQUEST, 'message': INVALID_REQUEST_MESSAGE},
            status=400,
        )

        # act
        with pytest.raises(APIException) as excinfo:
            startup_script_service.create(SCRIPT_NAME, SCRIPT_VALUE)

        # assert
        assert excinfo.value.code == INVALID_REQUEST
        assert excinfo.value.message == INVALID_REQUEST_MESSAGE
        assert responses.assert_call_count(endpoint, 1) is True

    def test_delete_scripts_successful(self, startup_script_service, endpoint):
        # arrange - add response mock
        responses.add(responses.DELETE, endpoint, status=200)

        # act
        result = startup_script_service.delete([SCRIPT_ID, script_ID_2])

        # assert
        assert result is None
        assert responses.assert_call_count(endpoint, 1) is True

    def test_delete_scripts_failed(self, startup_script_service, endpoint):
        # arrange - add response mock
        responses.add(
            responses.DELETE,
            endpoint,
            json={'code': INVALID_REQUEST, 'message': INVALID_REQUEST_MESSAGE},
            status=400,
        )

        # act
        with pytest.raises(APIException) as excinfo:
            startup_script_service.delete(['x'])

        # assert
        assert excinfo.value.code == INVALID_REQUEST
        assert excinfo.value.message == INVALID_REQUEST_MESSAGE
        assert responses.assert_call_count(endpoint, 1) is True

    def test_delete_script_by_id_successful(self, startup_script_service, endpoint):
        # arrange - add response mock
        url = endpoint + '/' + SCRIPT_ID
        responses.add(responses.DELETE, url, status=200)

        # act
        result = startup_script_service.delete_by_id(SCRIPT_ID)

        # assert
        assert result is None
        assert responses.assert_call_count(url, 1) is True

    def test_delete_script_by_id_failed(self, startup_script_service, endpoint):
        # arrange - add response mock
        url = endpoint + '/x'
        responses.add(
            responses.DELETE,
            url,
            json={'code': INVALID_REQUEST, 'message': INVALID_REQUEST_MESSAGE},
            status=400,
        )

        # act
        with pytest.raises(APIException) as excinfo:
            startup_script_service.delete_by_id('x')

        # assert
        assert excinfo.value.code == INVALID_REQUEST
        assert excinfo.value.message == INVALID_REQUEST_MESSAGE
        assert responses.assert_call_count(url, 1) is True
