import os
import time

from verda import VerdaClient
from verda.constants import Actions, InstanceStatus, Locations

# Get client secret and id from environment variables
CLIENT_ID = os.environ.get('VERDA_CLIENT_ID')
CLIENT_SECRET = os.environ.get('VERDA_CLIENT_SECRET')

# Create datcrunch client
verda = VerdaClient(CLIENT_ID, CLIENT_SECRET)

# Get all SSH keys id's
ssh_keys = verda.ssh_keys.get()
ssh_keys_ids = [ssh_key.id for ssh_key in ssh_keys]

# Create a new instance
instance = verda.instances.create(
    instance_type='1V100.6V',
    image='ubuntu-22.04-cuda-12.0-docker',
    location=Locations.FIN_03,
    ssh_key_ids=ssh_keys_ids,
    hostname='example',
    description='example instance',
)

# Wait for instance to enter running state
while instance.status != InstanceStatus.RUNNING:
    time.sleep(0.5)
    instance = verda.instances.get_by_id(instance.id)

print(instance)

# Delete instance
verda.instances.action(instance.id, Actions.DELETE)
