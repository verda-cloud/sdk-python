from dataclasses import dataclass

from dataclasses_json import Undefined, dataclass_json

LONG_TERM_PERIODS_ENDPOINT = '/long-term/periods'


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class LongTermPeriod:
    """A long-term commitment period."""

    code: str
    name: str
    is_enabled: bool
    unit_name: str
    unit_value: float
    discount_percentage: float


class LongTermService:
    """A service for interacting with the long-term periods endpoints."""

    def __init__(self, http_client) -> None:
        self._http_client = http_client

    def get_cluster_periods(self) -> list[LongTermPeriod]:
        """Get available long-term commitment periods for clusters.

        :return: list of long-term period objects
        :rtype: list[LongTermPeriod]
        """
        periods = self._http_client.get(LONG_TERM_PERIODS_ENDPOINT + '/clusters').json()
        return [LongTermPeriod.from_dict(p, infer_missing=True) for p in periods]

    def get_instance_periods(self) -> list[LongTermPeriod]:
        """Get available long-term commitment periods for instances.

        :return: list of long-term period objects
        :rtype: list[LongTermPeriod]
        """
        periods = self._http_client.get(LONG_TERM_PERIODS_ENDPOINT + '/instances').json()
        return [LongTermPeriod.from_dict(p, infer_missing=True) for p in periods]
