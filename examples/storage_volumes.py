# Copyright 2026 Verda Cloud Oy
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

from verda import VerdaClient

# Get client secret and id from environment variables
CLIENT_ID = os.environ.get('VERDA_CLIENT_ID')
CLIENT_SECRET = os.environ.get('VERDA_CLIENT_SECRET')

# Create datcrunch client
verda = VerdaClient(CLIENT_ID, CLIENT_SECRET)

# Get some volume type constants
NVMe = verda.constants.volume_types.NVMe
HDD = verda.constants.volume_types.HDD
SFS = verda.constants.volume_types.SFS

# Example instance id
INSTANCE_ID = '8705bb38-2574-454f-9967-d18b130bf5ee'

# Get all volumes
all_volumes = verda.volumes.get()

# Get all attached volumes
all_attached_volumes = verda.volumes.get(status=verda.constants.volume_status.ATTACHED)

# Get volume by id
random_volume = verda.volumes.get_by_id('0c41e387-3dd8-495f-a285-e861527f2f3d')

# Create a 200 GB detached NVMe volume
nvme_volume = verda.volumes.create(type=NVMe, name='data-storage-1', size=200)

# Create a shared filesystem volume
shared_filesystem_volume = verda.volumes.create(type=SFS, name='shared-filesystem-1', size=50)

# Create a 500 GB HDD volume and attach it to an existing shutdown instance
# Note: If the instance isn't shutdown an exception would be raised
hdd_volume = verda.volumes.create(
    type=HDD, name='data-storage-2', size=500, instance_id=INSTANCE_ID
)

nvme_volume_id = nvme_volume.id
hdd_volume_id = hdd_volume.id
sfs_volume_id = shared_filesystem_volume.id

# attach the nvme volume to the instance
verda.volumes.attach(nvme_volume_id, INSTANCE_ID)

# detach both volumes from the instance
verda.volumes.detach([nvme_volume_id, hdd_volume_id])

# rename volume
verda.volumes.rename(nvme_volume_id, 'new-name')

# increase volume size
verda.volumes.increase_size(nvme_volume_id, 300)

# clone volume
verda.volumes.clone(nvme_volume_id)

# clone volume and give it a new name and storage type (from NVMe to HDD)
verda.volumes.clone(nvme_volume_id, name='my-cloned-volume', type=HDD)

# clone multiple volumes at once
verda.volumes.clone([nvme_volume_id, hdd_volume_id])

# delete volumes (move to trash for 96h, not permanent)
verda.volumes.delete([nvme_volume_id, hdd_volume_id, sfs_volume_id])

# get all volumes in trash
volumes_in_trash = verda.volumes.get_in_trash()

# delete volumes permanently
verda.volumes.delete([nvme_volume_id, hdd_volume_id, sfs_volume_id], is_permanent=True)
