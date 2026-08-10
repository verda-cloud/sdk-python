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
import re
from urllib.parse import quote
from uuid import UUID

import requests

from verda._version import __version__
from verda.exceptions import APIException
from verda.helpers import _RELATIVE_SEGMENTS

# A `{name}` placeholder in a relative url template.
_PLACEHOLDER = re.compile(r'\{(\w+)\}')

# Anything outside the RFC 3986 unreserved set. Every value the API takes in a path
# position is a slug, an id or a machine type: 'my-deployment', '1A100.22V', a UUID.
_UNSAFE_IN_SEGMENT = re.compile(r'[^A-Za-z0-9._~-]')

# The unreserved set plus the '/' between the segments of an endpoint constant.
_ALLOWED_IN_PATH = re.compile(r'^[A-Za-z0-9._~/-]*$')


def _encode_path_segment(value: object) -> str:
    """Check a caller-supplied value is safe as a single URL path segment.

    Only the unreserved set is allowed. Encoding a separator is not sufficient:
    ``requests`` decodes ``%2E`` back to ``.`` before sending, and an intermediary
    that unescapes ``%2F`` before normalising the path restores a traversal.

    ``int`` and ``UUID`` are coerced with ``str()``. Other types are refused, since
    ``str()`` on them yields a nonsense segment (``b'abc'`` becomes ``"b'abc'"``).

    Args:
        value: A resource name or id supplied by the caller.

    Returns:
        The value as exactly one path segment.

    Raises:
        ValueError: If the value is empty, is not a str, int or UUID, contains a
            character outside the unreserved set, or is a relative path segment.
    """
    if not isinstance(value, str | int | UUID) or isinstance(value, bool):
        raise ValueError(f'path segment must be a str, int or UUID, got {type(value).__name__}')
    if not isinstance(value, str):
        value = str(value)
    if not value:
        raise ValueError(f'path segment must be a non-empty string, got {value!r}')
    if _UNSAFE_IN_SEGMENT.search(value):
        raise ValueError(
            f'path segment must contain only letters, digits and "-._~", got {value!r}'
        )
    # Only reachable as the whole value: a separator cannot pass the check above.
    if value in _RELATIVE_SEGMENTS:
        raise ValueError(f'path segment must not be a relative path segment, got {value!r}')

    # A no-op for an allowlisted value, kept in case the allowlist widens.
    return quote(value, safe='')


def handle_error(response: requests.Response) -> None:
    """Checks for the response status code and raises an exception if it's 400 or higher.

    Args:
        response: The API call response.

    Raises:
        APIException: An api exception with message and error type code.
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
        *,
        path_params: dict | None = None,
        **kwargs,
    ) -> requests.Response:
        """Sends a POST request.

        A wrapper for the requests.post method.

        Builds the url, uses custom headers, refresh tokens if needed.

        Args:
            url: Relative url of the API endpoint.
            json: A JSON serializable Python object to send in the body of the request.
            params: Dictionary of querystring data to attach to the request.
            path_params: Values substituted into ``{name}`` placeholders in the url,
                each encoded as a single path segment.
            **kwargs: Additional keyword arguments passed through to ``requests``.

        Returns:
            The response object.

        Raises:
            ValueError: If a path parameter cannot be safely encoded as a single path
                segment, or the url and ``path_params`` do not match.
            APIException: An api exception with message and error type code.
        """
        return self._request(
            'POST', url, json=json, params=params, path_params=path_params, **kwargs
        )

    def put(
        self,
        url: str,
        json: dict | None = None,
        params: dict | None = None,
        *,
        path_params: dict | None = None,
        **kwargs,
    ) -> requests.Response:
        """Sends a PUT request.

        A wrapper for the requests.put method.

        Builds the url, uses custom headers, refresh tokens if needed.

        Args:
            url: Relative url of the API endpoint.
            json: A JSON serializable Python object to send in the body of the request.
            params: Dictionary of querystring data to attach to the request.
            path_params: Values substituted into ``{name}`` placeholders in the url,
                each encoded as a single path segment.
            **kwargs: Additional keyword arguments passed through to ``requests``.

        Returns:
            The response object.

        Raises:
            ValueError: If a path parameter cannot be safely encoded as a single path
                segment, or the url and ``path_params`` do not match.
            APIException: An api exception with message and error type code.
        """
        return self._request(
            'PUT', url, json=json, params=params, path_params=path_params, **kwargs
        )

    def get(
        self,
        url: str,
        params: dict | None = None,
        *,
        path_params: dict | None = None,
        **kwargs,
    ) -> requests.Response:
        """Sends a GET request.

        A wrapper for the requests.get method.

        Builds the url, uses custom headers, refresh tokens if needed.

        Args:
            url: Relative url of the API endpoint.
            params: Dictionary of querystring data to attach to the request.
            path_params: Values substituted into ``{name}`` placeholders in the url,
                each encoded as a single path segment.
            **kwargs: Additional keyword arguments passed through to ``requests``.

        Returns:
            The response object.

        Raises:
            ValueError: If a path parameter cannot be safely encoded as a single path
                segment, or the url and ``path_params`` do not match.
            APIException: An api exception with message and error type code.
        """
        return self._request('GET', url, params=params, path_params=path_params, **kwargs)

    def patch(
        self,
        url: str,
        json: dict | None = None,
        params: dict | None = None,
        *,
        path_params: dict | None = None,
        **kwargs,
    ) -> requests.Response:
        """Sends a PATCH request.

        A wrapper for the requests.patch method.

        Builds the url, uses custom headers, refresh tokens if needed.

        Args:
            url: Relative url of the API endpoint.
            json: A JSON serializable Python object to send in the body of the request.
            params: Dictionary of querystring data to attach to the request.
            path_params: Values substituted into ``{name}`` placeholders in the url,
                each encoded as a single path segment.
            **kwargs: Additional keyword arguments passed through to ``requests``.

        Returns:
            The response object.

        Raises:
            ValueError: If a path parameter cannot be safely encoded as a single path
                segment, or the url and ``path_params`` do not match.
            APIException: An api exception with message and error type code.
        """
        return self._request(
            'PATCH', url, json=json, params=params, path_params=path_params, **kwargs
        )

    def delete(
        self,
        url: str,
        json: dict | None = None,
        params: dict | None = None,
        *,
        path_params: dict | None = None,
        **kwargs,
    ) -> requests.Response:
        """Sends a DELETE request.

        A wrapper for the requests.delete method.

        Builds the url, uses custom headers, refresh tokens if needed.

        Args:
            url: Relative url of the API endpoint.
            json: A JSON serializable Python object to send in the body of the request.
            params: Dictionary of querystring data to attach to the request.
            path_params: Values substituted into ``{name}`` placeholders in the url,
                each encoded as a single path segment.
            **kwargs: Additional keyword arguments passed through to ``requests``.

        Returns:
            The response object.

        Raises:
            ValueError: If a path parameter cannot be safely encoded as a single path
                segment, or the url and ``path_params`` do not match.
            APIException: An api exception with message and error type code.
        """
        return self._request(
            'DELETE', url, json=json, params=params, path_params=path_params, **kwargs
        )

    def _request(
        self,
        method: str,
        url: str,
        json: dict | None = None,
        params: dict | None = None,
        path_params: dict | None = None,
        **kwargs,
    ) -> requests.Response:
        """Sends a request, building and validating the url first.

        Every verb goes through here, so the path-parameter encoding cannot be
        skipped by adding a new one.

        Args:
            method: HTTP method name.
            url: Relative url of the API endpoint.
            json: A JSON serializable Python object to send in the body of the request.
            params: Dictionary of querystring data to attach to the request.
            path_params: Values substituted into ``{name}`` placeholders in the url.
            **kwargs: Additional keyword arguments passed through to ``requests``.

        Returns:
            The response object.

        Raises:
            ValueError: If the url and ``path_params`` do not produce a safe path.
            APIException: An api exception with message and error type code.
        """
        # Validate before the refresh so a rejected name costs no auth round-trip.
        url = self._add_base_url(self._build_path(url, path_params))

        self._refresh_token_if_expired()

        response = requests.request(
            method, url, json=json, headers=self._generate_headers(), params=params, **kwargs
        )
        handle_error(response)

        return response

    def _refresh_token_if_expired(self) -> None:
        """Refreshes the access token if it expired.

        Uses the refresh token to refresh, and if the refresh token is also expired,
        uses the client credentials.

        Raises:
            APIException: An api exception with message and error type code.
        """
        if self._auth_service.is_expired():
            # try to refresh. if refresh token has expired, reauthenticate
            try:
                self._auth_service.refresh()
            except Exception:
                self._auth_service.authenticate()

    def _generate_headers(self) -> dict:
        """Generate the default headers for every request.

        Returns:
            Dict with request headers.
        """
        headers = {
            'Authorization': self._generate_bearer_header(),
            'User-Agent': self._generate_user_agent(),
            'Content-Type': 'application/json',
        }
        return headers

    def _generate_bearer_header(self) -> str:
        """Generate the authorization header Bearer string.

        Returns:
            Authorization header Bearer string.
        """
        return f'Bearer {self._auth_service._access_token}'

    def _generate_user_agent(self) -> str:
        """Generate the user agent string.

        Returns:
            User agent string.
        """
        # get the first 10 chars of the client id
        client_id_truncated = self._auth_service._client_id[:10]

        return f'datacrunch-python-v{self._version}-{client_id_truncated}'

    def _build_path(self, url: str, path_params: dict | None) -> str:
        """Substitutes caller-supplied values into a relative url template.

        Each value is checked as exactly one path segment, so a resource name or id
        cannot introduce a path separator, walk out of its segment, or start a query
        string.

        Example:
        ``_build_path('/instances/{id}', {'id': 'abc'})`` returns ``'/instances/abc'``

        Args:
            url: A relative url, optionally containing ``{name}`` placeholders.
            path_params: Values to substitute into the placeholders.

        Returns:
            The relative url with every value encoded and substituted.

        Raises:
            ValueError: If a value cannot be safely encoded as a path segment, if the
                url still contains a placeholder that was never given a value, or if
                ``path_params`` carries a key the url does not use.
        """
        if not path_params:
            if '{' in url:
                raise ValueError(f'url has an unsubstituted placeholder, got {url!r}')
            return url

        unused = set(path_params) - set(_PLACEHOLDER.findall(url))
        if unused:
            raise ValueError(f'unused path parameter {sorted(unused)} for url {url!r}')

        encoded = {key: _encode_path_segment(value) for key, value in path_params.items()}
        try:
            path = url.format(**encoded)
        except KeyError as error:
            raise ValueError(f'no value given for placeholder {error} in url {url!r}') from error

        return path

    def _add_base_url(self, url: str) -> str:
        """Adds the base url to the relative url.

        Example:
        if the relative url is '/balance'
        and the base url is 'https://api.verda.com/v1'
        then this method will return 'https://api.verda.com/v1/balance'

        Backstop for a call site that built a path without ``path_params``. Re-asserts
        the same allowlist on the finished path.

        Args:
            url: A relative url path.

        Returns:
            The full url path.

        Raises:
            ValueError: If the path could escape the API base path.
        """
        # Query data is passed separately as `params`.
        if '?' in url or '#' in url:
            raise ValueError(f'request path must not contain a query string or fragment: {url!r}')

        # Catches '%', which requests may decode into a separator or a dot, and '\',
        # which some servers normalise to '/'.
        if not _ALLOWED_IN_PATH.match(url):
            raise ValueError(f'request path must not contain an unencoded value: {url!r}')

        # An empty segment collapses a delete-one call onto the collection endpoint.
        if any(segment == '' for segment in url.split('/')[1:]):
            raise ValueError(f'request path must not contain an empty path segment: {url!r}')

        if _RELATIVE_SEGMENTS.intersection(url.split('/')):
            raise ValueError(
                f'refusing to send a request whose path would escape the API base path: {url!r}'
            )

        return self._base_url + url
