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

from verda.exceptions import APIException

ERROR_CODE = 'test_code'
ERROR_MESSAGE = 'test message'


def test_api_exception_with_code():
    error_str = f'error code: {ERROR_CODE}\nmessage: {ERROR_MESSAGE}'

    with pytest.raises(APIException) as exc_info:
        raise APIException(ERROR_CODE, ERROR_MESSAGE)

    assert exc_info.value.code == ERROR_CODE
    assert exc_info.value.message == ERROR_MESSAGE
    assert exc_info.value.__str__() == error_str


def test_api_exception_without_code():
    error_str = f'message: {ERROR_MESSAGE}'

    with pytest.raises(APIException) as exc_info:
        raise APIException(None, ERROR_MESSAGE)

    assert exc_info.value.code is None
    assert exc_info.value.message == ERROR_MESSAGE
    assert exc_info.value.__str__() == error_str
