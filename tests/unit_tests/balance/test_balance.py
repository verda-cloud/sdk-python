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

import responses  # https://github.com/getsentry/responses

from verda.balance import Balance, BalanceService


def test_balance(http_client):
    # arrange - add response mock
    responses.add(
        responses.GET,
        http_client._base_url + '/balance',
        json={'amount': 50.5, 'currency': 'usd'},
        status=200,
    )

    balance_service = BalanceService(http_client)

    # act
    balance = balance_service.get()

    # assert
    assert isinstance(balance, Balance)
    assert isinstance(balance.amount, float)
    assert isinstance(balance.currency, str)
    assert balance.amount == 50.5
    assert balance.currency == 'usd'
