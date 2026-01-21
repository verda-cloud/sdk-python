"""
Example demonstrating how to use the Clusters API.

This example shows how to:
- Create a new compute cluster
- List all clusters
- Get a specific cluster by ID
- Get cluster nodes
- Delete a cluster
"""

import os
import time

from verda import VerdaClient
from verda.constants import Actions, ClusterStatus, Locations

# Get credentials from environment variables
CLIENT_ID = os.environ.get('VERDA_CLIENT_ID')
CLIENT_SECRET = os.environ.get('VERDA_CLIENT_SECRET')
BASE_URL = os.environ.get('VERDA_BASE_URL', 'https://api.verda.com/v1')

# Create client
verda = VerdaClient(CLIENT_ID, CLIENT_SECRET, base_url=BASE_URL)


def create_cluster_example():
    """Create a new compute cluster."""
    # Get SSH keys
    ssh_keys = [key.id for key in verda.ssh_keys.get()]

    cluster_type = '16B200'
    cluster_image = 'ubuntu-24.04-cuda-13.0-cluster'
    location_code = Locations.FIN_03

    # Check if cluster type is available
    if not verda.clusters.is_available(cluster_type, location_code):
        raise ValueError(f'Cluster type {cluster_type} is not available in {location_code}')

    # Get available images for cluster type
    images = verda.clusters.get_cluster_images(cluster_type)
    if cluster_image not in images:
        raise ValueError(f'Cluster image {cluster_image} is not supported for {cluster_type}')

    # Create a cluster
    cluster = verda.clusters.create(
        hostname='my-compute-cluster',
        cluster_type=cluster_type,
        image=cluster_image,
        description='Example compute cluster for distributed training',
        ssh_key_ids=ssh_keys,
        location=location_code,
        shared_volume_name='my-shared-volume',
        shared_volume_size=30000,
        wait_for_status=None,
    )

    print(f'Creating cluster: {cluster.id}')
    print(f'Cluster hostname: {cluster.hostname}')
    print(f'Cluster status: {cluster.status}')
    print(f'Cluster cluster_type: {cluster.cluster_type}')
    print(f'Location: {cluster.location}')

    # Wait for cluster to enter RUNNING status
    while cluster.status != ClusterStatus.RUNNING:
        print(f'Waiting for cluster to enter RUNNING status... (status: {cluster.status})')
        time.sleep(3)
        cluster = verda.clusters.get_by_id(cluster.id)

    print(f'Public IP: {cluster.ip}')
    print('Cluster is now running and ready to use!')

    return cluster


def list_clusters_example():
    """List all clusters."""
    # Get all clusters
    clusters = verda.clusters.get()

    print(f'\nFound {len(clusters)} cluster(s):')
    for cluster in clusters:
        print(
            f'  - {cluster.hostname} ({cluster.id}): {cluster.status} - {len(cluster.worker_nodes)} nodes'
        )

    # Get clusters with specific status
    running_clusters = verda.clusters.get(status=ClusterStatus.RUNNING)
    print(f'\nFound {len(running_clusters)} running cluster(s)')

    return clusters


def get_cluster_by_id_example(cluster_id: str):
    """Get a specific cluster by ID."""
    cluster = verda.clusters.get_by_id(cluster_id)

    print('\nCluster details:')
    print(f'  ID: {cluster.id}')
    print(f'  Name: {cluster.hostname}')
    print(f'  Description: {cluster.description}')
    print(f'  Status: {cluster.status}')
    print(f'  Cluster type: {cluster.cluster_type}')
    print(f'  Created at: {cluster.created_at}')
    print(f'  Public IP: {cluster.ip}')
    print(f'  Worker nodes: {len(cluster.worker_nodes)}')
    for node in cluster.worker_nodes:
        print(f'    - {node.hostname} ({node.id}): {node.status}, private IP: {node.private_ip}')
    print(f'  Shared volumes: {len(cluster.shared_volumes)}')
    for volume in cluster.shared_volumes:
        print(
            f'    - {volume.name} ({volume.id}): {volume.size_in_gigabytes} GB, mounted at {volume.mount_point}'
        )
    return cluster


def delete_cluster_example(cluster_id: str):
    """Delete a cluster."""
    print(f'\nDeleting cluster {cluster_id}...')

    verda.clusters.action(cluster_id, Actions.DELETE)

    print('Cluster deleted successfully')


def main():
    """Run all cluster examples."""
    print('=== Clusters API Example ===\n')

    print('Creating a new cluster...')
    cluster = create_cluster_example()
    cluster_id = cluster.id

    print('\nListing all clusters...')
    list_clusters_example()

    print('\nGetting cluster details...')
    get_cluster_by_id_example(cluster_id)

    print('\nDeleting the cluster...')
    delete_cluster_example(cluster_id)

    print('\n=== Example completed successfully ===')


if __name__ == '__main__':
    main()
