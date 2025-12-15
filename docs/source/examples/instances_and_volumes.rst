Instances and Volumes
=====================

.. code-block:: python

    import os
    from verda import VerdaClient
    from verda.constants import Actions, VolumeTypes

    # Get client secret from environment variable
    CLIENT_SECRET = os.environ['VERDA_CLIENT_SECRET']
    CLIENT_ID = 'Ibk5bdxV64lKAWOqYnvSi'  # Replace with your client ID

    # Create datcrunch client
    verda = VerdaClient(CLIENT_ID, CLIENT_SECRET)

    # Get some volume type constants
    NVMe = VolumeTypes.NVMe
    HDD = VolumeTypes.HDD

    EXISTING_OS_VOLUME_ID = '81e45bf0-5da2-412b-97d7-c20a7564fca0'
    EXAMPLE_VOLUME_ID = '225dde24-ae44-4787-9224-2b9f56f44394'
    EXAMPLE_INSTANCE_ID = '1eeabba4-caf7-4b4a-9143-0107034cc7f5'

    # Get all SSH keys
    ssh_keys = verda.ssh_keys.get()
    ssh_keys_ids = list(map(lambda ssh_key: ssh_key.id, ssh_keys))

    # Create instance with extra attached volumes
    instance_with_extra_volumes = verda.instances.create(instance_type='1V100.6V',
                                                         image='ubuntu-24.04-cuda-12.8-open-docker',
                                                         ssh_key_ids=ssh_keys,
                                                         hostname='example',
                                                         description='example instance',
                                                         volumes=[
                                                             {"type": HDD, "name": "volume-1", "size": 95},
                                                             {"type": NVMe, "name": "volume-2", "size": 95},
                                                         ])

    # Create instance with custom OS volume size and name
    instance_with_custom_os_volume = verda.instances.create(instance_type='1V100.6V',
                                                           image='ubuntu-24.04-cuda-12.8-open-docker',
                                                           ssh_key_ids=ssh_keys,
                                                           hostname='example',
                                                           description='example instance',
                                                           os_volume={
                                                               "name": "OS volume",
                                                               "size": 95,
                                                           })

    # Create instance with existing OS volume as an image
    instance_with_existing_os_volume = verda.instances.create(instance_type='1V100.6V',
                                                              image=EXISTING_OS_VOLUME_ID,
                                                              ssh_key_ids=ssh_keys,
                                                              hostname='example',
                                                              description='example instance')

    # Delete instance AND OS volume (the rest of the volumes would be detached)
    verda.instances.action(instance_id=EXAMPLE_INSTANCE_ID,
                           action=Actions.DELETE)

    # Delete instance WITHOUT deleting the OS volume (will detach all volumes of the instance)
    verda.instances.action(instance_id=EXAMPLE_INSTANCE_ID,
                           action=Actions.DELETE,
                           volume_ids=[])


    # Delete instance and one of it's volumes (will delete one volume, detach the rest)
    verda.instances.action(instance_id=EXAMPLE_INSTANCE_ID,
                           action=Actions.DELETE,
                           volume_ids=[EXAMPLE_VOLUME_ID])
