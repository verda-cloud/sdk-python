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

import responses

from verda import VerdaClient

BASE_URL = 'https://example.com'


@responses.activate()
def main():
    responses.add(
        responses.POST,
        f'{BASE_URL}/oauth2/token',
        json={
            'access_token': 'dummy',
            'token_type': 'Bearer',
            'refresh_token': 'dummy',
            'scope': 'fullAccess',
            'expires_in': 3600,
        },
        status=200,
    )

    client = VerdaClient('id', 'secret', BASE_URL)
    assert client.constants.base_url == BASE_URL


if __name__ == '__main__':
    main()
