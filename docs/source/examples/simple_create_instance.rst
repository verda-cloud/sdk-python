Simple Create Instance
======================

.. code-block:: python

    import os
    from verda import VerdaClient

    # Get client secret from environment variable
    CLIENT_SECRET = os.environ.get('VERDA_CLIENT_SECRET')
    CLIENT_ID = os.environ.get('VERDA_CLIENT_ID')

    # Create datcrunch client
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

    # Delete instance
    verda.instances.action(instance.id, verda.actions.DELETE)
        