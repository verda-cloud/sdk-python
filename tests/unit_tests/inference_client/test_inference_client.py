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
            # requests decodes percent-encoded unreserved characters before sending,
            # so these reach the wire as real dot-segments.
            '%2e%2e/%2e%2e/v1/victim',
            '%2E%2E/other-deployment',
        ],
    )
    def test_paths_that_escape_the_deployment_are_rejected(self, inference_client, path):
        # endpoint_base_url ends with this deployment's name, so a dot-segment walks
        # the request onto a different deployment while still carrying the caller's
        # inference key.
        with pytest.raises(InferenceClientError, match='relative path segment'):
            inference_client._build_url(path)

    @pytest.mark.parametrize(
        'path',
        ['predict?filter=a/../b', 'predict#a/../b', 'predict?q=..'],
    )
    def test_dot_segments_inside_a_query_string_are_not_path_traversal(
        self, inference_client, path
    ):
        # Only the path is resolved by a URL parser; a value inside the query string
        # is not, so rejecting it would break callers passing an inline query.
        assert inference_client._build_url(path) == f'{BASE_URL}/{path}'


class TestEndpointBaseUrl:
    @pytest.mark.parametrize(
        'base_url',
        [
            'https://inf.example.com/v1/..',
            'https://inf.example.com/v1/%2E%2E',
            'https://inf.example.com/v1/../admin/dep',
        ],
    )
    def test_base_url_containing_a_dot_segment_is_rejected(self, base_url):
        # deployment_name and base_domain are sliced out of this and interpolated
        # into the async status/result urls without further checks.
        with pytest.raises(InferenceClientError, match='relative path segment'):
            InferenceClient(inference_key='k', endpoint_base_url=base_url)

    @pytest.mark.parametrize(
        'base_url',
        ['https://containers.example.com', 'https://containers.example.com/'],
    )
    def test_base_url_without_a_deployment_path_is_rejected(self, base_url):
        # rindex('/') would find the '//' of the scheme, making base_domain 'https:/'
        # and the async status url 'https://status/containers.example.com'.
        with pytest.raises(InferenceClientError, match='must include the deployment path'):
            InferenceClient(inference_key='k', endpoint_base_url=base_url)

    def test_the_deployment_name_is_sliced_out_correctly(self, inference_client):
        assert inference_client.deployment_name == 'my-deployment'
        assert inference_client.base_domain == 'https://inference.example.com/v1'
