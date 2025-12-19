import os

import pytest

from verda import VerdaClient
from verda.constants import Locations

IN_GITHUB_ACTIONS = os.getenv('GITHUB_ACTIONS') == 'true'


@pytest.mark.skipif(IN_GITHUB_ACTIONS, reason="Test doesn't work in Github Actions.")
@pytest.mark.withoutresponses
class TestClusters:
    def test_create_cluster(self, verda_client: VerdaClient):
        # get ssh key
        ssh_key = verda_client.ssh_keys.get()[0]

        # create instance
        cluster = verda_client.clusters.create(
            hostname='test-instance',
            location=Locations.FIN_03,
            cluster_type='16H200',
            description='test instance',
            image='ubuntu-22.04-cuda-12.4-cluster',
            ssh_key_ids=[ssh_key.id],
        )

        # assert instance is created
        assert cluster.id is not None
        assert (
            cluster.status == verda_client.constants.instance_status.PROVISIONING
            or cluster.status == verda_client.constants.instance_status.RUNNING
        )

        assert cluster.worker_nodes is not None
        assert len(cluster.worker_nodes) == 2
        assert cluster.ip is not None

        print(cluster)

        # delete instance
        # verda_client.clusters.action(cluster.id, 'delete')
