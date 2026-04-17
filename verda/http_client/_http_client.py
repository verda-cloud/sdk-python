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

import json

import requests

from verda._version import __version__
from verda.exceptions import APIException


def handle_error(response: requests.Response) -> None:
    """Checks for the response status code and raises an exception if it's 400 or higher.

    :param response: the API call response
    :raises APIException: an api exception with message and error type code
    """
    if not response.ok:
        data = json.loads(response.text)
        code = data['code'] if 'code' in data else None
        message = data['message'] if 'message' in data else None
        raise APIException(code, message)


class HTTPClient:
    """An http client, a wrapper for the requests library.

    For each request, it adds the authentication header with an access token.
    If the access token is expired it refreshes it before calling the specified API endpoint.
    Also checks the response status code and raises an exception if needed.
    """

    def __init__(self, auth_service, base_url: str) -> None:
        self._version = __version__
        self._base_url = base_url
        self._auth_service = auth_service
        self._auth_service.authenticate()

    def post(
        self, url: str, json: dict | None = None, params: dict | None = None, **kwargs
    ) -> requests.Response:
        """Sends a POST request.

        A wrapper for the requests.post method.

        Builds the url, uses custom headers, refresh tokens if needed.

        :param url: relative url of the API endpoint
        :type url: str
        :param json: A JSON serializable Python object to send in the body of the Request, defaults to None
        :type json: dict, optional
        :param params: Dictionary of querystring data to attach to the Request, defaults to None
        :type params: dict, optional

        :raises APIException: an api exception with message and error type code

        :return: Response object
        :rtype: requests.Response
        """
        self._refresh_token_if_expired()

        url = self._add_base_url(url)
        headers = self._generate_headers()

        response = requests.post(url, json=json, headers=headers, params=params, **kwargs)
        handle_error(response)

        return response

    def put(
        self, url: str, json: dict | None = None, params: dict | None = None, **kwargs
    ) -> requests.Response:
        """Sends a PUT request.

        A wrapper for the requests.put method.

        Builds the url, uses custom headers, refresh tokens if needed.

        :param url: relative url of the API endpoint
        :type url: str
        :param json: A JSON serializable Python object to send in the body of the Request, defaults to None
        :type json: dict, optional
        :param params: Dictionary of querystring data to attach to the Request, defaults to None
        :type params: dict, optional

        :raises APIException: an api exception with message and error type code

        :return: Response object
        :rtype: requests.Response
        """
        self._refresh_token_if_expired()

        url = self._add_base_url(url)
        headers = self._generate_headers()

        response = requests.put(url, json=json, headers=headers, params=params, **kwargs)
        handle_error(response)

        return response

    def get(self, url: str, params: dict | None = None, **kwargs) -> requests.Response:
        """Sends a GET request.

        A wrapper for the requests.get method.

        Builds the url, uses custom headers, refresh tokens if needed.

        :param url: relative url of the API endpoint
        :type url: str
        :param params: Dictionary of querystring data to attach to the Request, defaults to None
        :type params: dict, optional

        :raises APIException: an api exception with message and error type code

        :return: Response object
        :rtype: requests.Response
        """
        self._refresh_token_if_expired()

        url = self._add_base_url(url)
        headers = self._generate_headers()

        response = requests.get(url, params=params, headers=headers, **kwargs)
        handle_error(response)

        return response

    def patch(
        self, url: str, json: dict | None = None, params: dict | None = None, **kwargs
    ) -> requests.Response:
        """Sends a PATCH request.

        A wrapper for the requests.patch method.

        Builds the url, uses custom headers, refresh tokens if needed.

        :param url: relative url of the API endpoint
        :type url: str
        :param json: A JSON serializable Python object to send in the body of the Request, defaults to None
        :type json: dict, optional
        :param params: Dictionary of querystring data to attach to the Request, defaults to None
        :type params: dict, optional

        :raises APIException: an api exception with message and error type code

        :return: Response object
        :rtype: requests.Response
        """
        self._refresh_token_if_expired()

        url = self._add_base_url(url)
        headers = self._generate_headers()

        response = requests.patch(url, json=json, headers=headers, params=params, **kwargs)
        handle_error(response)

        return response

    def delete(
        self, url: str, json: dict | None = None, params: dict | None = None, **kwargs
    ) -> requests.Response:
        """Sends a DELETE request.

        A wrapper for the requests.delete method.

        Builds the url, uses custom headers, refresh tokens if needed.

        :param url: relative url of the API endpoint
        :type url: str
        :param json: A JSON serializable Python object to send in the body of the Request, defaults to None
        :type json: dict, optional
        :param params: Dictionary of querystring data to attach to the Request, defaults to None
        :type params: dict, optional

        :raises APIException: an api exception with message and error type code

        :return: Response object
        :rtype: requests.Response
        """
        self._refresh_token_if_expired()

        url = self._add_base_url(url)
        headers = self._generate_headers()

        response = requests.delete(url, headers=headers, json=json, params=params, **kwargs)
        handle_error(response)

        return response

    def _refresh_token_if_expired(self) -> None:
        """Refreshes the access token if it expired.

        Uses the refresh token to refresh, and if the refresh token is also expired, uses the client credentials.

        :raises APIException: an api exception with message and error type code
        """
        if self._auth_service.is_expired():
            # try to refresh. if refresh token has expired, reauthenticate
            try:
                self._auth_service.refresh()
            except Exception:
                self._auth_service.authenticate()

    def _generate_headers(self) -> dict:
        """Generate the default headers for every request.

        :return: dict with request headers
        :rtype: dict
        """
        headers = {
            'Authorization': self._generate_bearer_header(),
            'User-Agent': self._generate_user_agent(),
            'Content-Type': 'application/json',
        }
        return headers

    def _generate_bearer_header(self) -> str:
        """Generate the authorization header Bearer string.

        :return: Authorization header Bearer string
        :rtype: str
        """
        return f'Bearer {self._auth_service._access_token}'

    def _generate_user_agent(self) -> str:
        """Generate the user agent string.

        :return: user agent string
        :rtype: str
        """
        # get the first 10 chars of the client id
        client_id_truncated = self._auth_service._client_id[:10]

        return f'datacrunch-python-v{self._version}-{client_id_truncated}'

    def _add_base_url(self, url: str) -> str:
        """Adds the base url to the relative url.

        Example:
        if the relative url is '/balance'
        and the base url is 'https://api.verda.com/v1'
        then this method will return 'https://api.verda.com/v1/balance'

        :param url: a relative url path
        :type url: str
        :return: the full url path
        :rtype: str
        """
        return self._base_url + url
