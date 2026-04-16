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

"""Example script demonstrating SGLang model deployment using the Verda API.

This script provides an example of deploying a SGLang server with deepseek-ai/deepseek-llm-7b-chat model,
including creation, monitoring, testing, and cleanup.
"""

import json
import os
import signal
import sys
import time
from datetime import datetime

from verda import VerdaClient
from verda.containers import (
    ComputeResource,
    Container,
    ContainerDeploymentStatus,
    Deployment,
    EntrypointOverridesSettings,
    EnvVar,
    EnvVarType,
    HealthcheckSettings,
    QueueLoadScalingTrigger,
    ScalingOptions,
    ScalingPolicy,
    ScalingTriggers,
    UtilizationScalingTrigger,
)
from verda.exceptions import APIException

CURRENT_TIMESTAMP = datetime.now().strftime('%Y%m%d-%H%M%S').lower()  # e.g. 20250403-120000

# Configuration constants
DEPLOYMENT_NAME = f'sglang-deployment-example-{CURRENT_TIMESTAMP}'
SGLANG_IMAGE_URL = 'docker.io/lmsysorg/sglang:v0.4.1.post6-cu124'
DEEPSEEK_MODEL_PATH = 'deepseek-ai/deepseek-llm-7b-chat'
HF_SECRET_NAME = 'huggingface-token'

# Get confidential values from environment variables
CLIENT_ID = os.environ.get('VERDA_CLIENT_ID')
CLIENT_SECRET = os.environ.get('VERDA_CLIENT_SECRET')
INFERENCE_KEY = os.environ.get('VERDA_INFERENCE_KEY')
HF_TOKEN = os.environ.get('HF_TOKEN')


def wait_for_deployment_health(
    client: VerdaClient,
    deployment_name: str,
    max_attempts: int = 20,
    delay: int = 30,
) -> bool:
    """Wait for deployment to reach healthy status.

    Args:
        client: Verda API client
        deployment_name: Name of the deployment to check
        max_attempts: Maximum number of status checks
        delay: Delay between checks in seconds

    Returns:
        bool: True if deployment is healthy, False otherwise
    """
    print('Waiting for deployment to be healthy (may take several minutes to download model)...')
    for attempt in range(max_attempts):
        try:
            status = client.containers.get_deployment_status(deployment_name)
            print(f'Attempt {attempt + 1}/{max_attempts} - Deployment status: {status}')
            if status == ContainerDeploymentStatus.HEALTHY:
                return True
            time.sleep(delay)
        except APIException as e:
            print(f'Error checking deployment status: {e}')
            return False
    return False


def cleanup_resources(client: VerdaClient) -> None:
    """Clean up all created resources.

    Args:
        client: Verda API client
    """
    try:
        # Delete deployment
        client.containers.delete_deployment(DEPLOYMENT_NAME)
        print('Deployment deleted')
    except APIException as e:
        print(f'Error during cleanup: {e}')


def graceful_shutdown(signum, _frame) -> None:
    """Handle graceful shutdown on signals."""
    print(f'\nSignal {signum} received, cleaning up resources...')
    try:
        cleanup_resources(verda)
    except Exception as e:
        print(f'Error during cleanup: {e}')
    sys.exit(0)


try:
    # Get the inference API key
    inference_key = INFERENCE_KEY
    if not inference_key:
        inference_key = input('Enter your Inference API Key from the Verda dashboard: ')
    else:
        print('Using Inference API Key from environment')

    # Initialize client with inference key
    verda = VerdaClient(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        inference_key=inference_key,
    )

    # Register signal handlers for cleanup
    signal.signal(signal.SIGINT, graceful_shutdown)
    signal.signal(signal.SIGTERM, graceful_shutdown)

    # Create a secret for the Hugging Face token
    print(f'Creating secret for Hugging Face token: {HF_SECRET_NAME}')
    try:
        # Check if secret already exists
        existing_secrets = verda.containers.get_secrets()
        secret_exists = any(secret.name == HF_SECRET_NAME for secret in existing_secrets)

        if not secret_exists:
            # check is HF_TOKEN is set, if not, prompt the user
            if not HF_TOKEN:
                HF_TOKEN = input('Enter your Hugging Face token: ')
            verda.containers.create_secret(HF_SECRET_NAME, HF_TOKEN)
            print(f"Secret '{HF_SECRET_NAME}' created successfully")
        else:
            print(f"Secret '{HF_SECRET_NAME}' already exists, using existing secret")
    except APIException as e:
        print(f'Error creating secret: {e}')
        sys.exit(1)

    # Create container configuration
    APP_PORT = 30000
    container = Container(
        image=SGLANG_IMAGE_URL,
        exposed_port=APP_PORT,
        healthcheck=HealthcheckSettings(enabled=True, port=APP_PORT, path='/health'),
        entrypoint_overrides=EntrypointOverridesSettings(
            enabled=True,
            cmd=[
                'python3',
                '-m',
                'sglang.launch_server',
                '--model-path',
                DEEPSEEK_MODEL_PATH,
                '--host',
                '0.0.0.0',
                '--port',
                str(APP_PORT),
            ],
        ),
        env=[
            EnvVar(
                name='HF_TOKEN',
                value_or_reference_to_secret=HF_SECRET_NAME,
                type=EnvVarType.SECRET,
            )
        ],
    )

    # Create scaling configuration
    scaling_options = ScalingOptions(
        min_replica_count=1,
        max_replica_count=5,
        scale_down_policy=ScalingPolicy(delay_seconds=60 * 5),
        scale_up_policy=ScalingPolicy(delay_seconds=0),  # No delay for scale up
        queue_message_ttl_seconds=500,
        # Modern LLM engines are optimized for batching requests, with minimal performance impact. Taking advantage of batching can significantly improve throughput.
        concurrent_requests_per_replica=32,
        scaling_triggers=ScalingTriggers(
            # lower value means more aggressive scaling
            queue_load=QueueLoadScalingTrigger(threshold=0.1),
            cpu_utilization=UtilizationScalingTrigger(enabled=True, threshold=90),
            gpu_utilization=UtilizationScalingTrigger(enabled=True, threshold=90),
        ),
    )

    # Set compute settings. For a 7B model, General Compute (24GB VRAM) is sufficient
    compute = ComputeResource(name='General Compute', size=1)

    # Create deployment object (no need to provide container_registry_settings because it's public)
    deployment = Deployment(
        name=DEPLOYMENT_NAME,
        containers=[container],
        compute=compute,
        scaling=scaling_options,
        is_spot=False,
    )

    # Create the deployment
    created_deployment = verda.containers.create_deployment(deployment)
    print(f'Created deployment: {created_deployment.name}')
    print('This could take several minutes while the model is downloaded and the server starts...')

    # Wait for deployment to be healthy
    if not wait_for_deployment_health(verda, DEPLOYMENT_NAME):
        print('Deployment health check failed')
        cleanup_resources(verda)
        sys.exit(1)

    # Test the deployment with a simple request
    print('\nTesting the deployment...')
    try:
        # Test model info endpoint
        print(
            'Testing /get_model_info endpoint by making a sync GET request to the SGLang server...'
        )
        model_info_response = created_deployment._inference_client.get(path='/get_model_info')
        print('Model info endpoint is working!')
        print(f'Response: {model_info_response}')

        # Test completions endpoint
        print('\nTesting completions API...')
        completions_data = {
            'model': DEEPSEEK_MODEL_PATH,
            'prompt': 'Is consciousness fundamentally computational, or is there something more to subjective experience that cannot be reduced to information processing?',
            'max_tokens': 128,
            'temperature': 0.7,
            'top_p': 0.9,
        }

        # Make a sync inference request to the SGLang server
        completions_response = created_deployment.run_sync(
            completions_data,
            path='/v1/completions',
        )
        print('Completions API is working!')
        print(f'Response: {completions_response.output()}\n')

        # Make a stream sync inference request to the SGLang server
        completions_response_stream = created_deployment.run_sync(
            {**completions_data, 'stream': True}, path='/v1/completions', stream=True
        )
        print('Stream completions API is working!')
        # Print the streamed response
        for line in completions_response_stream.stream(as_text=True):
            if line:
                line = line.decode('utf-8')

                if line.startswith('data:'):
                    data = line[5:]  # Remove 'data: ' prefix
                    if data == '[DONE]':
                        break
                    try:
                        event_data = json.loads(data)
                        token_text = event_data['choices'][0]['text']

                        # Print token immediately to show progress
                        print(token_text, end='', flush=True)
                    except json.JSONDecodeError:
                        continue

    except Exception as e:
        print(f'Error testing deployment: {e}')

    # Cleanup or keep running based on user input
    keep_running = input('\nDo you want to keep the deployment running? (y/n): ')
    if keep_running.lower() != 'y':
        cleanup_resources(verda)
    else:
        print(f"Deployment {DEPLOYMENT_NAME} is running. Don't forget to delete it when finished.")
        print('You can delete it from the Verda dashboard or by running:')
        print(f"verda.containers.delete('{DEPLOYMENT_NAME}')")

except Exception as e:
    print(f'Unexpected error: {e}')
    # Attempt cleanup even if there was an error
    try:
        cleanup_resources(verda)
    except Exception as cleanup_error:
        print(f'Error during cleanup after failure: {cleanup_error}')
    sys.exit(1)
