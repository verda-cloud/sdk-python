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

import pytest

from verda import VerdaClient
from verda.constants import Locations

IN_GITHUB_ACTIONS = os.getenv('GITHUB_ACTIONS') == 'true'

location_codes = [Locations.FIN_01, Locations.ICE_01]


@pytest.mark.skipif(IN_GITHUB_ACTIONS, reason="Test doesn't work in Github Actions.")
@pytest.mark.withoutresponses
class TestLocations:
    def test_specific_instance_availability_in_specific_location(self, verda_client: VerdaClient):
        # call the instance availability endpoint, for a specific location
        availability = verda_client.instances.is_available('CPU.4V', location_code=Locations.FIN_01)

        assert availability is not None
        assert isinstance(availability, bool)

    def test_all_availabilies_in_specific_location(self, verda_client: VerdaClient):
        # call the instance availability endpoint, for a specific location
        availabilities = verda_client.instances.get_availabilities(location_code=Locations.FIN_01)

        assert availabilities is not None
        assert isinstance(availabilities, list)
        assert len(availabilities) == 1
        assert availabilities[0]['location_code'] in location_codes
        assert isinstance(availabilities[0]['availabilities'], list)
        assert len(availabilities[0]['availabilities']) > 0

    def test_all_availabilites(self, verda_client: VerdaClient):
        # call the instance availability endpoint, for all locations
        all_availabilities = verda_client.instances.get_availabilities()

        assert all_availabilities is not None
        assert isinstance(all_availabilities, list)
        assert len(all_availabilities) > 1
        assert all_availabilities[0]['location_code'] in location_codes
        assert all_availabilities[1]['location_code'] in location_codes
        assert isinstance(all_availabilities[0]['availabilities'], list)
        assert len(all_availabilities[0]['availabilities']) > 0

    def test_get_all_locations(self, verda_client: VerdaClient):
        # call the locations endpoint
        locations = verda_client.locations.get()

        assert locations is not None
        assert isinstance(locations, list)

        assert locations[0]['code'] in location_codes
        assert locations[1]['code'] in location_codes
        assert locations[0]['code'] != locations[1]['code']

        assert locations[0]['name'] is not None
        assert locations[1]['name'] is not None
        assert locations[0]['name'] != locations[1]['name']

        assert locations[0]['country_code'] is not None
        assert locations[1]['country_code'] is not None
        assert locations[0]['country_code'] != locations[1]['country_code']
