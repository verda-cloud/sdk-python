import logging
import os

import pytest

from verda import VerdaClient
from verda.constants import Locations

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()


IN_GITHUB_ACTIONS = os.getenv('GITHUB_ACTIONS') == 'true'


@pytest.mark.skipif(IN_GITHUB_ACTIONS, reason="Test doesn't work in Github Actions.")
@pytest.mark.withoutresponses
class TestClusters:
    def test_create_cluster(self, verda_client: VerdaClient):
        # get ssh key
        ssh_key = verda_client.ssh_keys.get()[0]

        if not verda_client.clusters.is_available('16B200', Locations.FIN_03):
            raise ValueError('Cluster type 16B200 is not available in FIN_03')
        logger.debug('[x] Cluster type 16B200 is available in FIN_03')

        availabilities = verda_client.clusters.get_availabilities(Locations.FIN_03)
        assert len(availabilities) > 0
        assert '16B200' in availabilities
        logger.debug(
            '[x] Cluster type 16B200 is one of the available cluster types in FIN_03: %s',
            availabilities,
        )

        images = verda_client.clusters.get_cluster_images('16B200')
        assert len(images) > 0
        assert 'ubuntu-22.04-cuda-12.9-cluster' in images
        logger.debug('[x] Ubuntu 22.04 CUDA 12.9 cluster image is supported for 16B200')

        # create instance
        cluster = verda_client.clusters.create(
            hostname='test-instance',
            location=Locations.FIN_03,
            cluster_type='16B200',
            description='test instance',
            image='ubuntu-22.04-cuda-12.9-cluster',
            ssh_key_ids=[ssh_key.id],
            # Set to None to not wait for provisioning but return immediately
            wait_for_status=verda_client.constants.cluster_status.PROVISIONING,
        )

        # assert instance is created
        assert cluster.id is not None
        assert (
            cluster.status == verda_client.constants.cluster_status.PROVISIONING
            or cluster.status == verda_client.constants.cluster_status.RUNNING
        )

        # If still provisioning, we don't have worker nodes yet and ip is not available
        if cluster.status != verda_client.constants.instance_status.PROVISIONING:
            assert cluster.worker_nodes is not None
            assert len(cluster.worker_nodes) == 2
            assert cluster.ip is not None

        print(f'Creating cluster: {cluster.id}')
        print(f'Cluster hostname: {cluster.hostname}')
        print(f'Cluster status: {cluster.status}')
        print(f'Cluster cluster_type: {cluster.cluster_type}')
        print(f'Location: {cluster.location}')

        # delete instance
        # verda_client.clusters.action(cluster.id, 'delete')
