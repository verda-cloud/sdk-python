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

from verda import VerdaClient

# Get client secret and id from environment variables
CLIENT_ID = os.environ.get('VERDA_CLIENT_ID')
CLIENT_SECRET = os.environ.get('VERDA_CLIENT_SECRET')

# Initialize the client with your credentials
verda = VerdaClient(CLIENT_ID, CLIENT_SECRET)

# Example 1: List all compute resources
print('All compute resources:')
all_resources = verda.containers.get_compute_resources()
for resource in all_resources:
    print(f'Name: {resource.name}, Size: {resource.size}, Available: {resource.is_available}')

# Example 2: List available compute resources
print('\nAvailable compute resources:')
available_resources = verda.containers.get_compute_resources(is_available=True)
for resource in available_resources:
    print(f'Name: {resource.name}, Size: {resource.size}')

# Example 3: List compute resources of size 8
print('\nCompute resources with size 8:')
size_8_resources = verda.containers.get_compute_resources(size=8)
for resource in size_8_resources:
    print(f'Name: {resource.name}, Available: {resource.is_available}')
