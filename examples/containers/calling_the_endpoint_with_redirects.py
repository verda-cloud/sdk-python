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
from verda.inference_client import InferenceClient, InferenceClientError

# Configuration - replace with your deployment name
DEPLOYMENT_NAME = os.environ.get('VERDA_DEPLOYMENT_NAME')

# Client id and secret authenticate calls to the Verda API, such as the deployment lookup
CLIENT_ID = os.environ.get('VERDA_CLIENT_ID')
CLIENT_SECRET = os.environ.get('VERDA_CLIENT_SECRET')

# The inference key authenticates calls to the deployment endpoint
INFERENCE_KEY = os.environ.get('VERDA_INFERENCE_KEY')

# Verda client instance, used only to look up the deployment
verda = VerdaClient(CLIENT_ID, CLIENT_SECRET)

# Get the deployment, to read its endpoint base url
deployment = verda.containers.get_deployment_by_name(DEPLOYMENT_NAME)

# By default the inference client does not follow redirects, and a 3xx response
# raises InferenceClientError. With follow_redirects=True, the client follows a
# redirect only if the target is inside this deployment: the same scheme, host and
# port, and a path under endpoint_base_url. It follows at most 5 redirects.
with InferenceClient(
    inference_key=INFERENCE_KEY,
    endpoint_base_url=deployment.endpoint_base_url,
    follow_redirects=True,
) as inference_client:
    # Make a synchronous request to the endpoint.
    # This example demonstrates calling a SGLang deployment which serves LLMs using an OpenAI-compatible API format
    data = {
        'model': 'deepseek-ai/deepseek-llm-7b-chat',
        'prompt': 'Write a haiku about the sea.',
        'max_tokens': 64,
        'temperature': 0.7,
    }

    try:
        response = inference_client.run_sync(data=data, path='v1/completions')
        print(response.output())
    except InferenceClientError as e:
        # A redirect to a target outside the deployment is not followed. The error
        # message shows the Location value, and a hint if only a trailing slash differs.
        print(f'Request failed: {e}')
