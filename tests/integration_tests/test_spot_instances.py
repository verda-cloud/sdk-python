import logging
import os
import time

import pytest

from verda import VerdaClient
from verda.constants import Locations
from verda.instances import OSVolume

IN_GITHUB_ACTIONS = os.getenv('GITHUB_ACTIONS') == 'true'

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()


@pytest.mark.skipif(IN_GITHUB_ACTIONS, reason="Test doesn't work in Github Actions.")
@pytest.mark.withoutresponses
class TestInstances:
    def test_create_spot(self, verda_client: VerdaClient):
        # get ssh key
        ssh_key = verda_client.ssh_keys.get()[0]

        # create instance
        instance = verda_client.instances.create(
            hostname='test-instance',
            location=Locations.FIN_03,
            instance_type='CPU.4V.16G',
            description='test cpu instance',
            image='ubuntu-22.04',
            is_spot=True,
            ssh_key_ids=[ssh_key.id],
            os_volume=OSVolume(
                name='test-os-volume-spot', size=56, on_spot_discontinue='delete_permanently'
            ),
        )

        # assert instance is created
        assert instance.id is not None
        assert instance.status == verda_client.constants.instance_status.PROVISIONING

        while instance.status != verda_client.constants.instance_status.RUNNING:
            time.sleep(2)
            logger.debug('Waiting for instance to be running... %s', instance.status)
            instance = verda_client.instances.get_by_id(instance.id)

        logger.debug('Instance is running... %s', instance.status)
        logger.debug('Instance ID: %s', instance.id)
        logger.debug('Instance OS Volume ID: %s', instance.os_volume_id)
        logger.debug('Instance IP: %s', instance.ip)

        # assert os volume is created
        assert instance.os_volume_id is not None

        # get os volume
        os_volume = verda_client.volumes.get_by_id(instance.os_volume_id)
        assert os_volume.id is not None
        assert os_volume.name == 'test-os-volume-spot'
        assert os_volume.size == 56
