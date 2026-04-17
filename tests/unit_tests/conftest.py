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

from verda.http_client import HTTPClient

BASE_URL = 'https://api.example.com/v1'
ACCESS_TOKEN = 'test-token'
CLIENT_ID = '0123456789xyz'
CLIENT_SECRET = '0123456789xyz'


@pytest.fixture
def http_client():
    auth_service = Mock()
    auth_service._access_token = ACCESS_TOKEN
    auth_service.is_expired = Mock(return_value=True)
    auth_service.refresh = Mock(return_value=None)
    auth_service._client_id = CLIENT_ID
    auth_service._client_secret = CLIENT_SECRET

    return HTTPClient(auth_service, BASE_URL)
