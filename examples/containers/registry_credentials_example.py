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
from verda.containers import (
    AWSECRCredentials,
    CustomRegistryCredentials,
    DockerHubCredentials,
    GCRCredentials,
    GithubCredentials,
)

# Get client secret and id from environment variables
CLIENT_ID = os.environ.get('VERDA_CLIENT_ID')
CLIENT_SECRET = os.environ.get('VERDA_CLIENT_SECRET')

# Initialize Verda client
verda = VerdaClient(CLIENT_ID, CLIENT_SECRET)

# Example 1: DockerHub Credentials
dockerhub_creds = DockerHubCredentials(
    name='my-dockerhub-creds',
    username='your-dockerhub-username',
    access_token='your-dockerhub-access-token',
)
verda.containers.add_registry_credentials(dockerhub_creds)
print('Created DockerHub credentials')

# Example 2: GitHub Container Registry Credentials
github_creds = GithubCredentials(
    name='my-github-creds',
    username='your-github-username',
    access_token='your-github-token',
)
verda.containers.add_registry_credentials(github_creds)
print('Created GitHub credentials')

# Example 3: Google Container Registry (GCR) Credentials
# For GCR, you need to provide a service account key JSON string
gcr_service_account_key = """{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "private-key-id",
  "private_key": "-----BEGIN PRIVATE KEY-----\\nYOUR_PRIVATE_KEY_HERE\\n-----END PRIVATE KEY-----\\n",
  "client_email": "your-service-account@your-project.iam.gserviceaccount.com",
  "client_id": "client-id",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project.iam.gserviceaccount.com"
}"""

gcr_creds = GCRCredentials(name='my-gcr-creds', service_account_key=gcr_service_account_key)
verda.containers.add_registry_credentials(gcr_creds)
print('Created GCR credentials')

# Example 4: AWS ECR Credentials
aws_creds = AWSECRCredentials(
    name='my-aws-ecr-creds',
    access_key_id='AKIAEXAMPLE123456',
    secret_access_key='wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY',
    region='eu-north-1',
    ecr_repo='887841266746.dkr.ecr.eu-north-1.amazonaws.com',
)
verda.containers.add_registry_credentials(aws_creds)
print('Created AWS ECR credentials')

# Example 5: Custom Registry Credentials
custom_docker_config = """{
  "auths": {
    "your-custom-registry.com": {
      "auth": "base64-encoded-username-password"
    }
  }
}"""

custom_creds = CustomRegistryCredentials(
    name='my-custom-registry-creds', docker_config_json=custom_docker_config
)
verda.containers.add_registry_credentials(custom_creds)
print('Created Custom registry credentials')

# Delete all registry credentials
verda.containers.delete_registry_credentials('my-dockerhub-creds')
verda.containers.delete_registry_credentials('my-github-creds')
verda.containers.delete_registry_credentials('my-gcr-creds')
verda.containers.delete_registry_credentials('my-aws-ecr-creds')
verda.containers.delete_registry_credentials('my-custom-registry-creds')
