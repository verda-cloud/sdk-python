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

"""Example script demonstrating container deployment management using the Verda API.

This script provides a comprehensive example of container deployment lifecycle,
including creation, monitoring, scaling, and cleanup.
"""

import os
import time

from verda import VerdaClient
from verda.containers import (
    ComputeResource,
    Container,
    ContainerDeploymentStatus,
    ContainerRegistrySettings,
    Deployment,
    EnvVar,
    EnvVarType,
    GeneralStorageMount,
    HealthcheckSettings,
    QueueLoadScalingTrigger,
    ScalingOptions,
    ScalingPolicy,
    ScalingTriggers,
    SecretMount,
    SharedFileSystemMount,
    UtilizationScalingTrigger,
)
from verda.exceptions import APIException

# Configuration constants
DEPLOYMENT_NAME = 'my-deployment'
IMAGE_NAME = 'your-image-name:version'

# Get client secret and id from environment variables
CLIENT_ID = os.environ.get('VERDA_CLIENT_ID')
CLIENT_SECRET = os.environ.get('VERDA_CLIENT_SECRET')

# Verda client instance
verda = None


def wait_for_deployment_health(
    client: VerdaClient,
    deployment_name: str,
    max_attempts: int = 10,
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
    for _attempt in range(max_attempts):
        try:
            status = client.containers.get_deployment_status(deployment_name)
            print(f'Deployment status: {status}')
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


def main() -> None:
    """Main function demonstrating deployment lifecycle management."""
    try:
        # Initialize client
        global verda
        verda = VerdaClient(CLIENT_ID, CLIENT_SECRET)

        # Create container configuration
        container = Container(
            image=IMAGE_NAME,
            exposed_port=80,
            healthcheck=HealthcheckSettings(enabled=True, port=80, path='/health'),
            volume_mounts=[
                GeneralStorageMount(mount_path='/data'),
                # Optional: Fileset secret
                SecretMount(
                    mount_path='/path/to/mount',
                    secret_name='my-fileset-secret',  # This fileset secret must be created beforehand
                ),
                # Optional: Mount an existing shared filesystem volume
                SharedFileSystemMount(mount_path='/sfs', volume_id='<ID-OF-THE-SFS-VOLUME>'),
            ],
            env=[
                # Secret environment variables needed to be added beforehand
                EnvVar(
                    name='HF_TOKEN',
                    # This is a reference to a secret already created
                    value_or_reference_to_secret='hf-token',
                    type=EnvVarType.SECRET,
                ),
                # Plain environment variables can be added directly
                EnvVar(
                    name='VERSION',
                    value_or_reference_to_secret='1.5.2',
                    type=EnvVarType.PLAIN,
                ),
            ],
        )

        # Create scaling configuration
        scaling_options = ScalingOptions(
            min_replica_count=1,
            max_replica_count=5,
            scale_down_policy=ScalingPolicy(delay_seconds=300),
            scale_up_policy=ScalingPolicy(delay_seconds=300),
            queue_message_ttl_seconds=500,
            concurrent_requests_per_replica=1,
            scaling_triggers=ScalingTriggers(
                queue_load=QueueLoadScalingTrigger(threshold=1),
                cpu_utilization=UtilizationScalingTrigger(enabled=True, threshold=80),
                gpu_utilization=UtilizationScalingTrigger(enabled=True, threshold=80),
            ),
        )

        # Create registry and compute settings
        registry_settings = ContainerRegistrySettings(is_private=False)
        compute = ComputeResource(name='General Compute', size=1)

        # Create deployment object
        deployment = Deployment(
            name=DEPLOYMENT_NAME,
            container_registry_settings=registry_settings,
            containers=[container],
            compute=compute,
            scaling=scaling_options,
            is_spot=False,
        )

        # Create the deployment
        created_deployment = verda.containers.create_deployment(deployment)
        print(f'Created deployment: {created_deployment.name}')

        # Wait for deployment to be healthy
        if not wait_for_deployment_health(verda, DEPLOYMENT_NAME):
            print('Deployment health check failed')
            cleanup_resources(verda)
            return

        # Update scaling configuration
        try:
            deployment = verda.containers.get_deployment_by_name(DEPLOYMENT_NAME)
            # Create new scaling options with increased replica counts
            deployment.scaling = ScalingOptions(
                min_replica_count=2,
                max_replica_count=10,
                scale_down_policy=ScalingPolicy(delay_seconds=300),
                scale_up_policy=ScalingPolicy(delay_seconds=300),
                queue_message_ttl_seconds=500,
                concurrent_requests_per_replica=1,
                scaling_triggers=ScalingTriggers(
                    queue_load=QueueLoadScalingTrigger(threshold=1),
                    cpu_utilization=UtilizationScalingTrigger(enabled=True, threshold=80),
                    gpu_utilization=UtilizationScalingTrigger(enabled=True, threshold=80),
                ),
            )
            updated_deployment = verda.containers.update_deployment(DEPLOYMENT_NAME, deployment)
            print(f'Updated deployment scaling: {updated_deployment.name}')
        except APIException as e:
            print(f'Error updating scaling options: {e}')

        # Demonstrate deployment operations
        try:
            # Pause deployment
            verda.containers.pause_deployment(DEPLOYMENT_NAME)
            print('Deployment paused')
            time.sleep(60)

            # Resume deployment
            verda.containers.resume_deployment(DEPLOYMENT_NAME)
            print('Deployment resumed')

            # Restart deployment
            verda.containers.restart_deployment(DEPLOYMENT_NAME)
            print('Deployment restarted')

            # Purge queue
            verda.containers.purge_deployment_queue(DEPLOYMENT_NAME)
            print('Queue purged')
        except APIException as e:
            print(f'Error in deployment operations: {e}')

        # Clean up
        cleanup_resources(verda)

    except Exception as e:
        print(f'Unexpected error: {e}')
        # Attempt cleanup even if there was an error
        try:
            cleanup_resources(verda)
        except Exception as cleanup_error:
            print(f'Error during cleanup after failure: {cleanup_error}')


if __name__ == '__main__':
    main()
