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
from typing import Any

# Path segments a URL parser resolves relative to the preceding segment (RFC 3986,
# section 5.2.4). Reaching the wire with one of these means the request has been
# retargeted at a different endpoint.
_RELATIVE_SEGMENTS = frozenset({'.', '..'})

# A percent-escape of an unreserved character (RFC 3986, section 2.3). `requests`
# decodes these while preparing a request, so '%2E' becomes '.' before it is sent.
_ESCAPED_UNRESERVED = re.compile(r'%([0-9A-Fa-f]{2})')
_UNRESERVED = frozenset('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~')

# Percent-encoded path separators. `requests` leaves these encoded, but they are
# decoded by intermediaries that unescape before normalising, and a backslash is
# treated as a separator by some servers.
_ENCODED_SEPARATORS = ('%2F', '%2f', '%5C', '%5c', '\\')


def _decode_unreserved(path: str) -> str:
    """Decode the percent-escapes that ``requests`` decodes before sending a request.

    Mirrors ``requests.utils.unquote_unreserved``, which is not part of the public
    ``requests`` API, so a future release cannot break importing this package.

    Args:
        path: A url path, possibly percent-encoded.

    Returns:
        The path with escapes of unreserved characters decoded.
    """

    def replace(match: re.Match) -> str:
        char = chr(int(match.group(1), 16))
        return char if char in _UNRESERVED else match.group(0)

    return _ESCAPED_UNRESERVED.sub(replace, path)


def has_relative_path_segment(path: str) -> bool:
    """Whether a url path contains a segment a URL parser would resolve away.

    Any query string or fragment is stripped first: only the path is resolved, so a
    dot-segment inside a query value is not traversal. Percent-escapes of unreserved
    characters are then decoded, because ``requests`` decodes them before sending and
    a check against the raw string would miss ``%2E%2E``.

    Encoded separators are decoded too. They survive to the wire, but an intermediary
    that unescapes them before normalising the path (for example Envoy's
    ``UNESCAPE_AND_FORWARD``) turns ``..%2F..%2Fx`` back into a working traversal, so
    the check has to see what such a server would see. This does not reject an encoded
    separator on its own: ``docker.io%2Fmyorg`` decodes to two ordinary segments.

    Args:
        path: A url path to inspect.

    Returns:
        True if resolving the path would move it above one of its own segments.
    """
    path = path.split('?', 1)[0].split('#', 1)[0]
    decoded = _decode_unreserved(path)
    for separator in _ENCODED_SEPARATORS:
        decoded = decoded.replace(separator, '/')

    return bool(_RELATIVE_SEGMENTS.intersection(decoded.split('/')))


def stringify_class_object_properties(class_object: type) -> str:
    """Generates a json string representation of a class object's properties and values.

    :param class_object: An instance of a class
    :type class_object: Type
    :return: _description_
    :rtype: json string representation of a class object's properties and values
    """
    class_properties = {
        property: getattr(class_object, property, '')
        for property in class_object.__dir__()  # noqa: A001
        if property[:1] != '_' and type(getattr(class_object, property, '')).__name__ != 'method'
    }
    return json.dumps(class_properties, indent=2)


def strip_none_values(data: Any) -> Any:
    """Recursively remove ``None`` values from JSON-serializable data."""
    if isinstance(data, dict):
        return {key: strip_none_values(value) for key, value in data.items() if value is not None}
    if isinstance(data, list):
        return [strip_none_values(item) for item in data]
    return data
