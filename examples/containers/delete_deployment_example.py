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

"""Example script demonstrating deleting a deployment using the Verda API."""

import os

from verda import VerdaClient

DEPLOYMENT_NAME = 'sglang-deployment-example-20250411-160652'

# Get confidential values from environment variables
CLIENT_ID = os.environ.get('VERDA_CLIENT_ID')
CLIENT_SECRET = os.environ.get('VERDA_CLIENT_SECRET')

# Initialize client with inference key
verda = VerdaClient(CLIENT_ID, CLIENT_SECRET)

# Register signal handlers for cleanup
verda.containers.delete_deployment(DEPLOYMENT_NAME)
print('Deployment deleted')
