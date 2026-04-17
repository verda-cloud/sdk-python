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

# Create new startup script
bash_script = """echo this is a test script for serious cat business

# create a cats folder
mkdir cats && cd cats

# download a cat picture
curl https://http.cat/200 --output cat.jpg
"""
script = verda.startup_scripts.create('catty businness', bash_script)

# Print new startup script id, name, script code
print(script.id)
print(script.name)
print(script.script)

# Get all startup scripts
all_scripts = verda.startup_scripts.get()

# Get a single startup script by id
some_script = verda.startup_scripts.get_by_id(script.id)

# Delete startup script by id
verda.startup_scripts.delete_by_id(script.id)
