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

# Initialize Verda client
verda = VerdaClient(CLIENT_ID, CLIENT_SECRET)

# List all secrets
secrets = verda.containers.get_secrets()
print('Available secrets:')
for secret in secrets:
    print(f'- {secret.name} (created at: {secret.created_at})')

# Create a new secret
secret_name = 'my-api-key'
secret_value = 'super-secret-value'
verda.containers.create_secret(name=secret_name, value=secret_value)
print(f'\nCreated new secret: {secret_name}')

# Delete a secret (with force=False by default)
verda.containers.delete_secret(secret_name)
print(f'\nDeleted secret: {secret_name}')

# Delete a secret with force=True (will delete even if secret is in use)
secret_name = 'another-secret'
verda.containers.create_secret(name=secret_name, value=secret_value)
verda.containers.delete_secret(secret_name, force=True)
print(f'\nForce deleted secret: {secret_name}')
