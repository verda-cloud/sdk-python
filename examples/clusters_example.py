"""
Example demonstrating how to use the Clusters API.

This example shows how to:
- Create a new compute cluster
- List all clusters
- Get a specific cluster by ID
- Get cluster nodes
- Scale a cluster
- Delete a cluster
"""

import os

from verda import VerdaClient
from verda.constants import Actions, Locations

# Get credentials from environment variables
CLIENT_ID = os.environ.get('VERDA_CLIENT_ID')
CLIENT_SECRET = os.environ.get('VERDA_CLIENT_SECRET')

# Create client
verda = VerdaClient(CLIENT_ID, CLIENT_SECRET)


def create_cluster_example():
    """Create a new compute cluster."""
    # Get SSH keys
    ssh_keys = [key.id for key in verda.ssh_keys.get()]

    # Create a cluster with 3 nodes
    cluster = verda.clusters.create(
        hostname='my-compute-cluster',
        cluster_type='16H200',
        image='ubuntu-22.04-cuda-12.4-cluster',
        description='Example compute cluster for distributed training',
        ssh_key_ids=ssh_keys,
        location=Locations.FIN_03,
        shared_volume_name='my-shared-volume',
        shared_volume_size=30000,
    )

    print(f'Created cluster: {cluster.id}')
    print(f'Cluster hostname: {cluster.hostname}')
    print(f'Cluster status: {cluster.status}')
    print(f'Cluster cluster_type: {cluster.cluster_type}')
    print(f'Cluster worker_nodes: {cluster.worker_nodes}')
    print(f'Location: {cluster.location}')

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
    running_clusters = verda.clusters.get(status=verda.constants.cluster_status.RUNNING)
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

    return cluster


def delete_cluster_example(cluster_id: str):
    """Delete a cluster."""
    print(f'\nDeleting cluster {cluster_id}...')

    verda.clusters.action(cluster_id, Actions.DELETE)

    print('Cluster deleted successfully')


def main():
    """Run all cluster examples."""
    print('=== Clusters API Example ===\n')

    # Create a new cluster
    print('1. Creating a new cluster...')
    cluster = create_cluster_example()
    cluster_id = cluster.id

    # List all clusters
    print('\n2. Listing all clusters...')
    list_clusters_example()

    # Get cluster by ID
    print('\n3. Getting cluster details...')
    get_cluster_by_id_example(cluster_id)

    # Delete the cluster
    print('\n6. Deleting the cluster...')
    delete_cluster_example(cluster_id)

    print('\n=== Example completed successfully ===')


if __name__ == '__main__':
    main()
