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

import pytest

from verda.inference_client import InferenceClient, InferenceClientError

BASE_URL = 'https://inference.example.com/v1/my-deployment'


@pytest.fixture
def inference_client():
    return InferenceClient(inference_key='key-123', endpoint_base_url=BASE_URL)


class TestBuildUrl:
    """`path` is a caller-chosen multi-segment path, but it must stay under the base."""

    @pytest.mark.parametrize(
        ('path', 'expected'),
        [
            ('', f'{BASE_URL}/'),
            ('predict', f'{BASE_URL}/predict'),
            ('/predict', f'{BASE_URL}/predict'),
            # multi-segment paths are the documented contract and must keep working
            ('v1/models/predict', f'{BASE_URL}/v1/models/predict'),
            ('/v1/models/predict', f'{BASE_URL}/v1/models/predict'),
        ],
    )
    def test_ordinary_paths_are_joined_unchanged(self, inference_client, path, expected):
        assert inference_client._build_url(path) == expected

    @pytest.mark.parametrize(
        'path',
        [
            '../other-deployment',
            '../../v1/other-deployment',
            'a/../../b',
            './x',
            '..',
        ],
    )
    def test_paths_that_escape_the_deployment_are_rejected(self, inference_client, path):
        # endpoint_base_url ends with this deployment's name, so a dot-segment walks
        # the request onto a different deployment while still carrying the caller's
        # inference key.
        with pytest.raises(InferenceClientError, match='relative path segment'):
            inference_client._build_url(path)
