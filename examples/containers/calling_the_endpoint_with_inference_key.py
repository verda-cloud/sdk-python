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

from verda.inference_client import InferenceClient

# Get inference key and endpoint base url from environment variables
INFERENCE_KEY = os.environ.get('VERDA_INFERENCE_KEY')
BASE_URL = os.environ.get('VERDA_BASE_URL')

# Create an inference client that uses only the inference key, without client credentials
inference_client = InferenceClient(
    inference_key=INFERENCE_KEY,
    endpoint_base_url=BASE_URL,
)

# Make a synchronous request to the endpoint.
# This example demonstrates calling a SGLang deployment which serves LLMs using an OpenAI-compatible API format
data = {
    'model': 'deepseek-ai/deepseek-llm-7b-chat',
    'prompt': 'Is consciousness fundamentally computational, or is there something more to subjective experience that cannot be reduced to information processing?',
    'max_tokens': 128,
    'temperature': 0.7,
    'top_p': 0.9,
}

response = inference_client.run_sync(data=data, path='v1/completions')

# Print the response
print(response.output())
