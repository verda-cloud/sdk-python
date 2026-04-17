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

# Fileset secrets are a way to mount sensitive files like API keys, certs, and credentials securely inside a container, without hardcoding them in the image or env vars.
# This example demonstrates how to create a fileset secret containing two files from your local filesystem

# Get client secret and id from environment variables
CLIENT_ID = os.environ.get('VERDA_CLIENT_ID')
CLIENT_SECRET = os.environ.get('VERDA_CLIENT_SECRET')

# Initialize the client with your credentials
verda = VerdaClient(CLIENT_ID, CLIENT_SECRET)

# Define the secret name and the file paths from your local filesystem where this script is running
SECRET_NAME = 'my-fileset-secret'
RELATIVE_FILE_PATH = './relative-path/file1.txt'
ABSOLUTE_FILE_PATH = '/home/username/absolute-path/file2.json'

# Create the fileset secret that has 2 files
fileset_secret = verda.containers.create_fileset_secret_from_file_paths(
    secret_name=SECRET_NAME, file_paths=[RELATIVE_FILE_PATH, ABSOLUTE_FILE_PATH]
)

# Get the secret
secrets = verda.containers.get_fileset_secrets()
print(secrets)

# Delete the secret
verda.containers.delete_fileset_secret(secret_name=SECRET_NAME)
