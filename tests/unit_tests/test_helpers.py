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

from verda.helpers import strip_none_values


def test_strip_none_values_removes_none_recursively():
    data = {
        'name': 'job',
        'optional': None,
        'nested': {
            'keep': 'value',
            'drop': None,
        },
        'items': [
            {'keep': 1, 'drop': None},
            None,
            ['value', None],
        ],
    }

    assert strip_none_values(data) == {
        'name': 'job',
        'nested': {'keep': 'value'},
        'items': [
            {'keep': 1},
            None,
            ['value', None],
        ],
    }
