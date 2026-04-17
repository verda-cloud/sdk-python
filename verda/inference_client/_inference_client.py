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

from collections.abc import Generator
from dataclasses import dataclass
from enum import Enum
from typing import Any
from urllib.parse import urlparse

import requests
from dataclasses_json import Undefined, dataclass_json  # type: ignore
from requests.structures import CaseInsensitiveDict


class InferenceClientError(Exception):
    """Base exception for InferenceClient errors."""

    pass


class AsyncStatus(str, Enum):
    """Async status."""

    Initialized = 'Initialized'
    Queue = 'Queue'
    Inference = 'Inference'
    Completed = 'Completed'


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class InferenceResponse:
    """Inference response."""

    headers: CaseInsensitiveDict[str]
    status_code: int
    status_text: str
    _original_response: requests.Response
    _stream: bool = False

    def _is_stream_response(self, headers: CaseInsensitiveDict[str]) -> bool:
        """Check if the response headers indicate a streaming response.

        Args:
            headers: The response headers to check

        Returns:
            bool: True if the response is likely a stream, False otherwise
        """
        # Standard chunked transfer encoding
        is_chunked_transfer = headers.get('Transfer-Encoding', '').lower() == 'chunked'
        # Server-Sent Events content type
        is_event_stream = headers.get('Content-Type', '').lower() == 'text/event-stream'
        # NDJSON
        is_ndjson = headers.get('Content-Type', '').lower() == 'application/x-ndjson'
        # Stream JSON
        is_stream_json = headers.get('Content-Type', '').lower() == 'application/stream+json'
        # Keep-alive
        is_keep_alive = headers.get('Connection', '').lower() == 'keep-alive'
        # No content length
        has_no_content_length = 'Content-Length' not in headers

        # No Content-Length with keep-alive often suggests streaming (though not definitive)
        is_keep_alive_and_no_content_length = is_keep_alive and has_no_content_length

        return (
            self._stream
            or is_chunked_transfer
            or is_event_stream
            or is_ndjson
            or is_stream_json
            or is_keep_alive_and_no_content_length
        )

    def output(self, is_text: bool = False) -> Any:
        """Get response output as a string or object."""
        try:
            if is_text:
                return self._original_response.text
            return self._original_response.json()
        except Exception as e:
            # if the response is a stream (check headers), raise relevant error
            if self._is_stream_response(self._original_response.headers):
                raise InferenceClientError(
                    'Response might be a stream, use the stream method instead'
                ) from e
            raise InferenceClientError(f'Failed to parse response as JSON: {e!s}') from e

    def stream(self, chunk_size: int = 512, as_text: bool = True) -> Generator[Any, None, None]:
        """Stream the response content.

        Args:
            chunk_size: Size of chunks to stream, in bytes
            as_text: If True, stream as text using iter_lines. If False, stream as binary using iter_content.

        Returns:
            Generator yielding chunks of the response
        """
        if as_text:
            for chunk in self._original_response.iter_lines(chunk_size=chunk_size):
                if chunk:
                    yield chunk
        else:
            for chunk in self._original_response.iter_content(chunk_size=chunk_size):
                if chunk:
                    yield chunk


class InferenceClient:
    """Inference client."""

    def __init__(
        self, inference_key: str, endpoint_base_url: str, timeout_seconds: int = 60 * 5
    ) -> None:
        """Initialize the InferenceClient.

        Args:
            inference_key: The authentication key for the API
            endpoint_base_url: The base URL for the API
            timeout_seconds: Request timeout in seconds

        Raises:
            InferenceClientError: If the parameters are invalid
        """
        if not inference_key:
            raise InferenceClientError('inference_key cannot be empty')

        parsed_url = urlparse(endpoint_base_url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise InferenceClientError('endpoint_base_url must be a valid URL')

        self.inference_key = inference_key
        self.endpoint_base_url = endpoint_base_url.rstrip('/')
        self.base_domain = self.endpoint_base_url[: self.endpoint_base_url.rindex('/')]
        self.deployment_name = self.endpoint_base_url[self.endpoint_base_url.rindex('/') + 1 :]
        self.timeout_seconds = timeout_seconds
        self._session = requests.Session()
        self._global_headers = {
            'Authorization': f'Bearer {inference_key}',
            'Content-Type': 'application/json',
        }

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._session.close()

    @property
    def global_headers(self) -> dict[str, str]:
        """Get the current global headers that will be used for all requests.

        Returns:
            Dictionary of current global headers
        """
        return self._global_headers.copy()

    def set_global_header(self, key: str, value: str) -> None:
        """Set or update a global header that will be used for all requests.

        Args:
            key: Header name
            value: Header value
        """
        self._global_headers[key] = value

    def set_global_headers(self, headers: dict[str, str]) -> None:
        """Set multiple global headers at once that will be used for all requests.

        Args:
            headers: Dictionary of headers to set globally
        """
        self._global_headers.update(headers)

    def remove_global_header(self, key: str) -> None:
        """Remove a global header.

        Args:
            key: Header name to remove from global headers
        """
        if key in self._global_headers:
            del self._global_headers[key]

    def _build_url(self, path: str) -> str:
        """Construct the full URL by joining the base URL with the path."""
        return f'{self.endpoint_base_url}/{path.lstrip("/")}'

    def _build_request_headers(
        self, request_headers: dict[str, str] | None = None
    ) -> dict[str, str]:
        """Build the final headers by merging global headers with request-specific headers.

        Args:
            request_headers: Optional headers specific to this request

        Returns:
            Merged headers dictionary
        """
        headers = self._global_headers.copy()
        if request_headers:
            headers.update(request_headers)
        return headers

    def _make_request(self, method: str, path: str, **kwargs) -> requests.Response:
        """Make an HTTP request with error handling.

        Args:
            method: HTTP method to use
            path: API endpoint path
            **kwargs: Additional arguments to pass to the request

        Returns:
            Response object from the request

        Raises:
            InferenceClientError: If the request fails
        """
        timeout = kwargs.pop('timeout_seconds', self.timeout_seconds)
        try:
            response = self._session.request(
                method=method,
                url=self._build_url(path),
                headers=self._build_request_headers(kwargs.pop('headers', None)),
                timeout=timeout,
                **kwargs,
            )
            response.raise_for_status()
            return response
        except requests.exceptions.Timeout as e:
            raise InferenceClientError(
                f'Request to {path} timed out after {timeout} seconds'
            ) from e
        except requests.exceptions.RequestException as e:
            raise InferenceClientError(f'Request to {path} failed: {e!s}') from e

    def run_sync(
        self,
        data: dict[str, Any],
        path: str = '',
        timeout_seconds: int = 60 * 5,
        headers: dict[str, str] | None = None,
        http_method: str = 'POST',
        stream: bool = False,
    ):
        """Make a synchronous request to the inference endpoint.

        Args:
            data: The data payload to send with the request
            path: API endpoint path. Defaults to empty string.
            timeout_seconds: Request timeout in seconds. Defaults to 5 minutes.
            headers: Optional headers to include in the request
            http_method: HTTP method to use. Defaults to "POST".
            stream: Whether to stream the response. Defaults to False.

        Returns:
            InferenceResponse: Object containing the response data.

        Raises:
            InferenceClientError: If the request fails
        """
        response = self._make_request(
            http_method,
            path,
            json=data,
            timeout_seconds=timeout_seconds,
            headers=headers,
            stream=stream,
        )

        return InferenceResponse(
            headers=response.headers,
            status_code=response.status_code,
            status_text=response.reason,
            _original_response=response,
        )

    def run(
        self,
        data: dict[str, Any],
        path: str = '',
        timeout_seconds: int = 60 * 5,
        headers: dict[str, str] | None = None,
        http_method: str = 'POST',
        no_response: bool = False,
    ):
        """Make an asynchronous request to the inference endpoint.

        Args:
            data: The data payload to send with the request
            path: API endpoint path. Defaults to empty string.
            timeout_seconds: Request timeout in seconds. Defaults to 5 minutes.
            headers: Optional headers to include in the request
            http_method: HTTP method to use. Defaults to "POST".
            no_response: If True, don't wait for response. Defaults to False.

        Returns:
            AsyncInferenceExecution: Object to track the async execution status.
            If no_response is True, returns None.

        Raises:
            InferenceClientError: If the request fails
        """
        # Add relevant headers to the request, to indicate that the request is async
        headers = headers or {}
        if no_response:
            # If no_response is True, use the "Prefer: respond-async-proxy" header to run async and don't wait for the response
            headers['Prefer'] = 'respond-async-proxy'
            self._make_request(
                http_method,
                path,
                json=data,
                timeout_seconds=timeout_seconds,
                headers=headers,
            )
            return
        # Add the "Prefer: respond-async" header to the request, to run async and wait for the response
        headers['Prefer'] = 'respond-async'

        response = self._make_request(
            http_method,
            path,
            json=data,
            timeout_seconds=timeout_seconds,
            headers=headers,
        )

        result = response.json()
        execution_id = result['Id']

        return AsyncInferenceExecution(self, execution_id, AsyncStatus.Initialized)

    def get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout_seconds: int | None = None,
    ) -> requests.Response:
        """Make GET request."""
        return self._make_request(
            'GET', path, params=params, headers=headers, timeout_seconds=timeout_seconds
        )

    def post(
        self,
        path: str,
        json: dict[str, Any] | None = None,
        data: str | dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout_seconds: int | None = None,
    ) -> requests.Response:
        """Make POST request."""
        return self._make_request(
            'POST',
            path,
            json=json,
            data=data,
            params=params,
            headers=headers,
            timeout_seconds=timeout_seconds,
        )

    def put(
        self,
        path: str,
        json: dict[str, Any] | None = None,
        data: str | dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout_seconds: int | None = None,
    ) -> requests.Response:
        """Make PUT request."""
        return self._make_request(
            'PUT',
            path,
            json=json,
            data=data,
            params=params,
            headers=headers,
            timeout_seconds=timeout_seconds,
        )

    def delete(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout_seconds: int | None = None,
    ) -> requests.Response:
        """Make DELETE request."""
        return self._make_request(
            'DELETE',
            path,
            params=params,
            headers=headers,
            timeout_seconds=timeout_seconds,
        )

    def patch(
        self,
        path: str,
        json: dict[str, Any] | None = None,
        data: str | dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout_seconds: int | None = None,
    ) -> requests.Response:
        """Make PATCH request."""
        return self._make_request(
            'PATCH',
            path,
            json=json,
            data=data,
            params=params,
            headers=headers,
            timeout_seconds=timeout_seconds,
        )

    def head(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout_seconds: int | None = None,
    ) -> requests.Response:
        """Make HEAD request."""
        return self._make_request(
            'HEAD',
            path,
            params=params,
            headers=headers,
            timeout_seconds=timeout_seconds,
        )

    def options(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout_seconds: int | None = None,
    ) -> requests.Response:
        """Make OPTIONS request."""
        return self._make_request(
            'OPTIONS',
            path,
            params=params,
            headers=headers,
            timeout_seconds=timeout_seconds,
        )

    def health(self, healthcheck_path: str = '/health') -> requests.Response:
        """Check the health status of the API.

        Returns:
            requests.Response: The response from the health check

        Raises:
            InferenceClientError: If the health check fails
        """
        try:
            return self.get(healthcheck_path)
        except InferenceClientError as e:
            raise InferenceClientError(f'Health check failed: {e!s}') from e


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class AsyncInferenceExecution:
    """Async inference execution."""

    _inference_client: 'InferenceClient'
    id: str
    _status: AsyncStatus
    INFERENCE_ID_HEADER = 'X-Inference-Id'

    def status(self) -> AsyncStatus:
        """Get the current stored status of the async inference execution. Only the status value type.

        Returns:
            AsyncStatus: The status object
        """
        return self._status

    def status_json(self) -> dict[str, Any]:
        """Get the current status of the async inference execution. Return the status json.

        Returns:
            dict[str, Any]: The status response containing the execution status and other metadata
        """
        url = (
            f'{self._inference_client.base_domain}/status/{self._inference_client.deployment_name}'
        )
        response = self._inference_client._session.get(
            url,
            headers=self._inference_client._build_request_headers(
                {self.INFERENCE_ID_HEADER: self.id}
            ),
        )

        response_json = response.json()
        self._status = AsyncStatus(response_json['Status'])

        return response_json

    def result(self) -> dict[str, Any]:
        """Get the results of the async inference execution.

        Returns:
            dict[str, Any]: The results of the inference execution
        """
        url = (
            f'{self._inference_client.base_domain}/result/{self._inference_client.deployment_name}'
        )
        response = self._inference_client._session.get(
            url,
            headers=self._inference_client._build_request_headers(
                {self.INFERENCE_ID_HEADER: self.id}
            ),
        )

        if response.headers['Content-Type'] == 'application/json':
            return response.json()
        else:
            return {'result': response.text}

    # alias for get_results
    output = result
