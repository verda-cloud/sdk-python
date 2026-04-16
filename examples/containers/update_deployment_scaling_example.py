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

"""Example script demonstrating how to update scaling options for a container deployment.

This script shows how to update scaling configurations for an existing container deployment on Verda.
"""

import os

from verda import VerdaClient
from verda.containers import (
    QueueLoadScalingTrigger,
    ScalingOptions,
    ScalingPolicy,
    ScalingTriggers,
    UtilizationScalingTrigger,
)
from verda.exceptions import APIException

# Get deployment name, client secret and id from environment variables
DEPLOYMENT_NAME = os.environ.get('VERDA_DEPLOYMENT_NAME')
CLIENT_ID = os.environ.get('VERDA_CLIENT_ID')
CLIENT_SECRET = os.environ.get('VERDA_CLIENT_SECRET')

# Initialize client
verda = VerdaClient(CLIENT_ID, CLIENT_SECRET)

try:
    # Get current scaling options
    scaling_options = verda.containers.get_deployment_scaling_options(DEPLOYMENT_NAME)

    print('Current scaling configuration:\n')
    print(f'Min replicas: {scaling_options.min_replica_count}')
    print(f'Max replicas: {scaling_options.max_replica_count}')
    print(f'Scale-up delay: {scaling_options.scale_up_policy.delay_seconds} seconds')
    print(f'Scale-down delay: {scaling_options.scale_down_policy.delay_seconds} seconds')
    print(f'Queue message TTL: {scaling_options.queue_message_ttl_seconds} seconds')
    print(f'Concurrent requests per replica: {scaling_options.concurrent_requests_per_replica}')
    print('Scaling Triggers:')
    print(f'  Queue load threshold: {scaling_options.scaling_triggers.queue_load.threshold}')
    if scaling_options.scaling_triggers.cpu_utilization:
        print(
            f'  CPU utilization enabled: {scaling_options.scaling_triggers.cpu_utilization.enabled}'
        )
        print(
            f'  CPU utilization threshold: {scaling_options.scaling_triggers.cpu_utilization.threshold}%'
        )
    if scaling_options.scaling_triggers.gpu_utilization:
        print(
            f'  GPU utilization enabled: {scaling_options.scaling_triggers.gpu_utilization.enabled}'
        )
        if scaling_options.scaling_triggers.gpu_utilization.threshold:
            print(
                f'  GPU utilization threshold: {scaling_options.scaling_triggers.gpu_utilization.threshold}%'
            )

    # Create scaling options using ScalingOptions dataclass
    scaling_options = ScalingOptions(
        min_replica_count=1,
        max_replica_count=5,
        scale_down_policy=ScalingPolicy(delay_seconds=600),  # Longer cooldown period
        scale_up_policy=ScalingPolicy(delay_seconds=0),  # Quick scale-up
        queue_message_ttl_seconds=500,
        concurrent_requests_per_replica=50,  # LLMs can handle concurrent requests
        scaling_triggers=ScalingTriggers(
            queue_load=QueueLoadScalingTrigger(threshold=1.0),
            cpu_utilization=UtilizationScalingTrigger(enabled=True, threshold=75),
            gpu_utilization=UtilizationScalingTrigger(
                enabled=False  # Disable GPU utilization trigger
            ),
        ),
    )

    # Update scaling options
    updated_options = verda.containers.update_deployment_scaling_options(
        DEPLOYMENT_NAME, scaling_options
    )

    print('\nUpdated scaling configuration:\n')
    print(f'Min replicas: {updated_options.min_replica_count}')
    print(f'Max replicas: {updated_options.max_replica_count}')
    print(f'Scale-up delay: {updated_options.scale_up_policy.delay_seconds} seconds')
    print(f'Scale-down delay: {updated_options.scale_down_policy.delay_seconds} seconds')
    print(f'Queue message TTL: {updated_options.queue_message_ttl_seconds} seconds')
    print(f'Concurrent requests per replica: {updated_options.concurrent_requests_per_replica}')
    print('Scaling Triggers:')
    print(f'  Queue load threshold: {updated_options.scaling_triggers.queue_load.threshold}')
    if updated_options.scaling_triggers.cpu_utilization:
        print(
            f'  CPU utilization enabled: {updated_options.scaling_triggers.cpu_utilization.enabled}'
        )
        print(
            f'  CPU utilization threshold: {updated_options.scaling_triggers.cpu_utilization.threshold}%'
        )
    if updated_options.scaling_triggers.gpu_utilization:
        print(
            f'  GPU utilization enabled: {updated_options.scaling_triggers.gpu_utilization.enabled}'
        )
        if updated_options.scaling_triggers.gpu_utilization.threshold:
            print(
                f'  GPU utilization threshold: {updated_options.scaling_triggers.gpu_utilization.threshold}%'
            )


except APIException as e:
    print(f'Error updating scaling options: {e}')
except Exception as e:
    print(f'Unexpected error: {e}')
