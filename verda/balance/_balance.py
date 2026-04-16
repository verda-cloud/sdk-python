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

BALANCE_ENDPOINT = '/balance'


class Balance:
    """A balance model class."""

    def __init__(self, amount: float, currency: str) -> None:
        """Initialize a new Balance object.

        :param amount: Balance amount
        :type amount: float
        :param currency: currency code
        :type currency: str
        """
        self._amount = amount
        self._currency = currency

    @property
    def amount(self) -> float:
        """Get the balance amount.

        :return: amount
        :rtype: float
        """
        return self._amount

    @property
    def currency(self) -> str:
        """Get the currency code.

        :return: currency code
        :rtype: str
        """
        return self._currency


class BalanceService:
    """A service for interacting with the balance endpoint."""

    def __init__(self, http_client) -> None:
        self._http_client = http_client

    def get(self) -> Balance:
        """Get the client's current balance.

        :return: Balance object containing the amount and currency.
        :rtype: Balance
        """
        balance = self._http_client.get(BALANCE_ENDPOINT).json()
        return Balance(balance['amount'], balance['currency'])
