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
from urllib.parse import quote

import requests
from requests.exceptions import InvalidURL
from requests.utils import unquote_unreserved

from verda._version import __version__
from verda.exceptions import APIException

# Path segments a URL parser resolves relative to the preceding segment (RFC 3986,
# section 5.2.4). Reaching the wire with one of these means the request has been
# retargeted at a different endpoint.
_RELATIVE_SEGMENTS = frozenset({'.', '..'})


def _encode_path_segment(value: str) -> str:
    """Encode a caller-supplied value for safe use as a single URL path segment.

    Resource names and ids are interpolated into request paths. An unencoded value
    containing ``/`` is resolved by ``requests`` while the request is prepared, which
    silently retargets the call at a different API endpoint under the caller's own
    credentials. Encoding with ``safe=''`` also neutralises ``?`` and ``#``, so a
    name cannot inject query parameters either.

    :param value: a resource name or id supplied by the caller
    :type value: str
    :raises ValueError: if the value is not a non-empty string, or is a relative
        path segment that no amount of encoding can make safe
    :return: the value encoded as exactly one path segment
    :rtype: str
    """
    if not isinstance(value, str) or not value:
        raise ValueError(f'path segment must be a non-empty string, got {value!r}')
    if value in _RELATIVE_SEGMENTS:
        # Encoding these as '%2E'/'%2E%2E' does not help: requests decodes
        # percent-encoded unreserved characters again before sending the request.
        raise ValueError(f'path segment must not be a relative path segment, got {value!r}')

    return quote(value, safe='')


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
        self,
        url: str,
        json: dict | None = None,
        params: dict | None = None,
        path_params: dict | None = None,
        **kwargs,
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
        :param path_params: Values substituted into ``{name}`` placeholders in the url,
            each encoded as a single path segment, defaults to None
        :type path_params: dict, optional

        :raises APIException: an api exception with message and error type code

        :return: Response object
        :rtype: requests.Response
        """
        self._refresh_token_if_expired()

        url = self._add_base_url(self._build_path(url, path_params))
        headers = self._generate_headers()

        response = requests.post(url, json=json, headers=headers, params=params, **kwargs)
        handle_error(response)

        return response

    def put(
        self,
        url: str,
        json: dict | None = None,
        params: dict | None = None,
        path_params: dict | None = None,
        **kwargs,
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
        :param path_params: Values substituted into ``{name}`` placeholders in the url,
            each encoded as a single path segment, defaults to None
        :type path_params: dict, optional

        :raises APIException: an api exception with message and error type code

        :return: Response object
        :rtype: requests.Response
        """
        self._refresh_token_if_expired()

        url = self._add_base_url(self._build_path(url, path_params))
        headers = self._generate_headers()

        response = requests.put(url, json=json, headers=headers, params=params, **kwargs)
        handle_error(response)

        return response

    def get(
        self,
        url: str,
        params: dict | None = None,
        path_params: dict | None = None,
        **kwargs,
    ) -> requests.Response:
        """Sends a GET request.

        A wrapper for the requests.get method.

        Builds the url, uses custom headers, refresh tokens if needed.

        :param url: relative url of the API endpoint
        :type url: str
        :param params: Dictionary of querystring data to attach to the Request, defaults to None
        :type params: dict, optional
        :param path_params: Values substituted into ``{name}`` placeholders in the url,
            each encoded as a single path segment, defaults to None
        :type path_params: dict, optional

        :raises APIException: an api exception with message and error type code

        :return: Response object
        :rtype: requests.Response
        """
        self._refresh_token_if_expired()

        url = self._add_base_url(self._build_path(url, path_params))
        headers = self._generate_headers()

        response = requests.get(url, params=params, headers=headers, **kwargs)
        handle_error(response)

        return response

    def patch(
        self,
        url: str,
        json: dict | None = None,
        params: dict | None = None,
        path_params: dict | None = None,
        **kwargs,
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
        :param path_params: Values substituted into ``{name}`` placeholders in the url,
            each encoded as a single path segment, defaults to None
        :type path_params: dict, optional

        :raises APIException: an api exception with message and error type code

        :return: Response object
        :rtype: requests.Response
        """
        self._refresh_token_if_expired()

        url = self._add_base_url(self._build_path(url, path_params))
        headers = self._generate_headers()

        response = requests.patch(url, json=json, headers=headers, params=params, **kwargs)
        handle_error(response)

        return response

    def delete(
        self,
        url: str,
        json: dict | None = None,
        params: dict | None = None,
        path_params: dict | None = None,
        **kwargs,
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
        :param path_params: Values substituted into ``{name}`` placeholders in the url,
            each encoded as a single path segment, defaults to None
        :type path_params: dict, optional

        :raises APIException: an api exception with message and error type code

        :return: Response object
        :rtype: requests.Response
        """
        self._refresh_token_if_expired()

        url = self._add_base_url(self._build_path(url, path_params))
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

    def _build_path(self, url: str, path_params: dict | None) -> str:
        """Substitutes caller-supplied values into a relative url template.

        Each value is encoded as exactly one path segment, so a resource name or id
        cannot introduce a path separator, walk out of its segment, or start a query
        string. Call sites pass values as data rather than interpolating them, which
        means the encoding cannot be forgotten.

        Example:
        ``_build_path('/instances/{id}', {'id': 'a/b'})`` returns ``'/instances/a%2Fb'``

        :param url: a relative url, optionally containing ``{name}`` placeholders
        :type url: str
        :param path_params: values to substitute into the placeholders
        :type path_params: dict, optional
        :raises ValueError: if a value cannot be safely encoded as a path segment, or
            if the url still contains a placeholder that was never given a value
        :raises KeyError: if the url has a placeholder missing from ``path_params``
        :return: the relative url with every value encoded and substituted
        :rtype: str
        """
        if not path_params:
            if '{' in url:
                raise ValueError(f'url has an unsubstituted placeholder, got {url!r}')
            return url

        encoded = {key: _encode_path_segment(value) for key, value in path_params.items()}
        path = url.format(**encoded)

        # An encoded value can never contain a separator, so substitution must not
        # change the shape of the route. Belt and braces against a future change to
        # the encoding rules.
        if path.count('/') != url.count('/'):
            raise ValueError(f'path parameter added a path segment to {url!r}')

        return path

    def _add_base_url(self, url: str) -> str:
        """Adds the base url to the relative url.

        Example:
        if the relative url is '/balance'
        and the base url is 'https://api.verda.com/v1'
        then this method will return 'https://api.verda.com/v1/balance'

        Acts as a backstop for the per-segment encoding done by the service modules:
        a relative path segment that reached this point would be resolved away by
        ``requests`` (or by the server), pointing the request at a different endpoint.

        :param url: a relative url path
        :type url: str
        :raises ValueError: if the path could escape the API base path
        :return: the full url path
        :rtype: str
        """
        path = url.split('?', 1)[0].split('#', 1)[0]

        # requests decodes percent-encoded unreserved characters before sending, which
        # turns '%2E' back into '.'. Inspect the path the way the server will see it.
        try:
            path = unquote_unreserved(path)
        except InvalidURL:
            pass

        if _RELATIVE_SEGMENTS.intersection(path.split('/')):
            raise ValueError(
                f'refusing to send a request whose path would escape the API base path: {url!r}'
            )

        return self._base_url + url
