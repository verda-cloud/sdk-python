import pytest
import responses

from verda.exceptions import APIException
from verda.long_term import LongTermPeriod, LongTermService

INVALID_REQUEST = 'invalid_request'
INVALID_REQUEST_MESSAGE = 'Bad request'

PERIOD_1 = {
    'code': '3_MONTHS',
    'name': '3 months',
    'is_enabled': True,
    'unit_name': 'month',
    'unit_value': 3.0,
    'discount_percentage': 14.0,
}

PERIOD_2 = {
    'code': '6_MONTHS',
    'name': '6 months',
    'is_enabled': True,
    'unit_name': 'month',
    'unit_value': 6.0,
    'discount_percentage': 20.0,
}

PAYLOAD = [PERIOD_1, PERIOD_2]


class TestLongTermService:
    @pytest.fixture
    def long_term_service(self, http_client):
        return LongTermService(http_client)

    @pytest.fixture
    def endpoint(self, http_client):
        return http_client._base_url + '/long-term/periods'

    def test_get_cluster_periods(self, long_term_service, endpoint):
        # arrange
        responses.add(responses.GET, endpoint + '/clusters', json=PAYLOAD, status=200)

        # act
        periods = long_term_service.get_cluster_periods()

        # assert
        assert isinstance(periods, list)
        assert len(periods) == 2
        assert isinstance(periods[0], LongTermPeriod)
        assert periods[0].code == '3_MONTHS'
        assert periods[0].name == '3 months'
        assert periods[0].is_enabled is True
        assert periods[0].unit_name == 'month'
        assert periods[0].unit_value == 3.0
        assert periods[0].discount_percentage == 14.0
        assert periods[1].code == '6_MONTHS'
        assert responses.assert_call_count(endpoint + '/clusters', 1) is True

    def test_get_cluster_periods_failed(self, long_term_service, endpoint):
        # arrange
        url = endpoint + '/clusters'
        responses.add(
            responses.GET,
            url,
            json={'code': INVALID_REQUEST, 'message': INVALID_REQUEST_MESSAGE},
            status=400,
        )

        # act + assert
        with pytest.raises(APIException) as excinfo:
            long_term_service.get_cluster_periods()

        assert excinfo.value.code == INVALID_REQUEST
        assert excinfo.value.message == INVALID_REQUEST_MESSAGE
        assert responses.assert_call_count(url, 1) is True

    def test_get_instance_periods(self, long_term_service, endpoint):
        # arrange
        responses.add(responses.GET, endpoint + '/instances', json=PAYLOAD, status=200)

        # act
        periods = long_term_service.get_instance_periods()

        # assert
        assert isinstance(periods, list)
        assert len(periods) == 2
        assert isinstance(periods[0], LongTermPeriod)
        assert periods[0].code == '3_MONTHS'
        assert periods[0].discount_percentage == 14.0
        assert periods[1].unit_value == 6.0
        assert responses.assert_call_count(endpoint + '/instances', 1) is True

    def test_get_instance_periods_failed(self, long_term_service, endpoint):
        # arrange
        url = endpoint + '/instances'
        responses.add(
            responses.GET,
            url,
            json={'code': INVALID_REQUEST, 'message': INVALID_REQUEST_MESSAGE},
            status=400,
        )

        # act + assert
        with pytest.raises(APIException) as excinfo:
            long_term_service.get_instance_periods()

        assert excinfo.value.code == INVALID_REQUEST
        assert excinfo.value.message == INVALID_REQUEST_MESSAGE
        assert responses.assert_call_count(url, 1) is True

    def test_get_cluster_periods_empty_list(self, long_term_service, endpoint):
        # arrange
        responses.add(responses.GET, endpoint + '/clusters', json=[], status=200)

        # act
        periods = long_term_service.get_cluster_periods()

        # assert
        assert isinstance(periods, list)
        assert len(periods) == 0
