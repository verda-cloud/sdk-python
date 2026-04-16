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

import os

import pytest
from dotenv import load_dotenv

from verda import VerdaClient

"""
Make sure to run the server and the account has enough balance before running the tests
"""

# Load env variables, make sure there's an env file with valid client credentials
load_dotenv()
CLIENT_SECRET = os.getenv('VERDA_CLIENT_SECRET')
CLIENT_ID = os.getenv('VERDA_CLIENT_ID')
BASE_URL = os.getenv('VERDA_BASE_URL', 'http://localhost:3010/v1')


@pytest.fixture
def verda_client():
    return VerdaClient(CLIENT_ID, CLIENT_SECRET, BASE_URL)
