# Verda Python SDK

Welcome to the documentation for the official Verda (formerly Datacrunch) Python SDK.

The Public API documentation is [available here](https://api.verda.com/v1/docs)

The Python SDK is open-sourced and can be [found here](https://github.com/verda-cloud/sdk-python)

## Basic Examples:

First, get your client credentials - [instructions available here](https://api.verda.com/v1/docs#description/quick-start-guide).

Deploy a new instance:

```python
import os
from verda import VerdaClient

# Get client secret from environment variable
CLIENT_SECRET = os.environ['VERDA_CLIENT_SECRET']
CLIENT_ID = 'Ibk5bdxV64lKAWOqYnvSi'  # Replace with your client ID

# Create client
verda = VerdaClient(CLIENT_ID, CLIENT_SECRET)

# Get all SSH keys id's
ssh_keys = verda.ssh_keys.get()
ssh_keys_ids = list(map(lambda ssh_key: ssh_key.id, ssh_keys))

# Create a new instance
instance = verda.instances.create(instance_type='1V100.6V',
                                  image='ubuntu-24.04-cuda-12.8-open-docker',
                                  ssh_key_ids=ssh_keys_ids,
                                  hostname='example',
                                  description='example instance')
```

List all existing instances, ssh keys, startup scripts:

```python
instances = verda.instances.get()
keys = verda.ssh_keys.get()
scripts = verda.startup_scripts.get()
```

List all available instance & image types (information about available
os images and instances to deploy)

```python
instance_types = verda.instance_types.get()
images_types = verda.images.get()
```
