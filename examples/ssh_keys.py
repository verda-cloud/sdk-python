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

# Create datcrunch client
verda = VerdaClient(CLIENT_ID, CLIENT_SECRET)

# Create new SSH key
public_key = (
    'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAI0qq2Qjt5GPi7DKdcnBHOkvk8xNsG9dA607tnWagOkHC test_key'
)
ssh_key = verda.ssh_keys.create('my test key', public_key)

# Print new key id, name, public key
print(ssh_key.id)
print(ssh_key.name)
print(ssh_key.public_key)

# Get all keys
all_ssh_keys = verda.ssh_keys.get()

# Get single key by id
some_ssh_key = verda.ssh_keys.get_by_id(ssh_key.id)

# Delete ssh key by id
verda.ssh_keys.delete_by_id(ssh_key.id)
