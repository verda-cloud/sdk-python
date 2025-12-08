import os
import time

from verda import VerdaClient
from verda.constants import Actions, InstanceStatus
from verda.exceptions import APIException

# Get client secret and id from environment variables
CLIENT_ID = os.environ.get('VERDA_CLIENT_ID')
CLIENT_SECRET = os.environ.get('VERDA_CLIENT_SECRET')

# Create datcrunch client
verda = VerdaClient(CLIENT_ID, CLIENT_SECRET)

# Get all SSH keys
ssh_keys = verda.ssh_keys.get()
ssh_keys_ids = [ssh_key.id for ssh_key in ssh_keys]

# Create a new 1V100.6V instance
instance = verda.instances.create(
    instance_type='1V100.6V',
    image='ubuntu-22.04-cuda-12.0-docker',
    ssh_key_ids=ssh_keys_ids,
    hostname='example',
    description='example instance',
)

print(instance.id)

# Try to shutdown instance right away,
# encounter an error (because it's still provisioning)
try:
    verda.instances.action(instance.id, Actions.SHUTDOWN)
except APIException as exception:
    print(exception)  # we were too eager...

# Wait until instance is running (check every 30sec), only then shut it down
while instance.status != InstanceStatus.RUNNING:
    time.sleep(30)
    instance = verda.instances.get_by_id(instance.id)

# Shutdown!
try:
    verda.instances.action(instance.id, Actions.SHUTDOWN)
except APIException as exception:
    print(exception)  # no exception this time

# Wait until instance is offline (check every 30sec), only then hibernate
while instance.status != InstanceStatus.OFFLINE:
    time.sleep(30)
    instance = verda.instances.get_by_id(instance.id)

# Hibernate the instance
try:
    verda.instances.action(instance.id, Actions.HIBERNATE)
except APIException as exception:
    print(exception)
