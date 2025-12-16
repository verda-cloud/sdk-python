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
from verda.constants import Locations

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
        name='my-compute-cluster',
        instance_type='8V100.48V',
        node_count=3,
        image='ubuntu-24.04-cuda-12.8-open-docker',
        description='Example compute cluster for distributed training',
        ssh_key_ids=ssh_keys,
        location=Locations.FIN_03,
    )

    print(f'Created cluster: {cluster.id}')
    print(f'Cluster name: {cluster.name}')
    print(f'Cluster status: {cluster.status}')
    print(f'Number of nodes: {cluster.node_count}')
    print(f'Instance type: {cluster.instance_type}')
    print(f'Location: {cluster.location}')

    return cluster


def list_clusters_example():
    """List all clusters."""
    # Get all clusters
    clusters = verda.clusters.get()

    print(f'\nFound {len(clusters)} cluster(s):')
    for cluster in clusters:
        print(f'  - {cluster.name} ({cluster.id}): {cluster.status} - {cluster.node_count} nodes')

    # Get clusters with specific status
    running_clusters = verda.clusters.get(status=verda.constants.cluster_status.RUNNING)
    print(f'\nFound {len(running_clusters)} running cluster(s)')

    return clusters


def get_cluster_by_id_example(cluster_id: str):
    """Get a specific cluster by ID."""
    cluster = verda.clusters.get_by_id(cluster_id)

    print('\nCluster details:')
    print(f'  ID: {cluster.id}')
    print(f'  Name: {cluster.name}')
    print(f'  Description: {cluster.description}')
    print(f'  Status: {cluster.status}')
    print(f'  Instance type: {cluster.instance_type}')
    print(f'  Node count: {cluster.node_count}')
    print(f'  Created at: {cluster.created_at}')
    if cluster.master_ip:
        print(f'  Master IP: {cluster.master_ip}')
    if cluster.endpoint:
        print(f'  Endpoint: {cluster.endpoint}')

    return cluster


def get_cluster_nodes_example(cluster_id: str):
    """Get all nodes in a cluster."""
    nodes = verda.clusters.get_nodes(cluster_id)

    print(f'\nCluster has {len(nodes)} node(s):')
    for i, node in enumerate(nodes, 1):
        print(f'\n  Node {i}:')
        print(f'    ID: {node.id}')
        print(f'    Hostname: {node.hostname}')
        print(f'    Status: {node.status}')
        print(f'    IP: {node.ip}')
        print(f'    Instance type: {node.instance_type}')

    return nodes


def scale_cluster_example(cluster_id: str, new_node_count: int):
    """Scale a cluster to a new number of nodes."""
    print(f'\nScaling cluster {cluster_id} to {new_node_count} nodes...')

    cluster = verda.clusters.scale(cluster_id, new_node_count)

    print('Cluster scaled successfully')
    print(f'Current node count: {cluster.node_count}')
    print(f'Cluster status: {cluster.status}')

    return cluster


def delete_cluster_example(cluster_id: str):
    """Delete a cluster."""
    print(f'\nDeleting cluster {cluster_id}...')

    verda.clusters.delete(cluster_id)

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

    # Get cluster nodes
    print('\n4. Getting cluster nodes...')
    get_cluster_nodes_example(cluster_id)

    # Scale the cluster
    print('\n5. Scaling the cluster...')
    scale_cluster_example(cluster_id, 5)

    # Delete the cluster
    print('\n6. Deleting the cluster...')
    delete_cluster_example(cluster_id)

    print('\n=== Example completed successfully ===')


if __name__ == '__main__':
    main()
