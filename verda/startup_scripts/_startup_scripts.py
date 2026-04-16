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

STARTUP_SCRIPTS_ENDPOINT = '/scripts'


class StartupScript:
    """A startup script model class."""

    def __init__(self, id: str, name: str, script: str) -> None:
        """Initialize a new startup script object.

        :param id: startup script id
        :type id: str
        :param name: startup script name
        :type name: str
        :param script: the actual script
        :type script: str
        """
        self._id = id
        self._name = name
        self._script = script

    @property
    def id(self) -> str:
        """Get the startup script id.

        :return: startup script id
        :rtype: str
        """
        return self._id

    @property
    def name(self) -> str:
        """Get the startup script name.

        :return: startup script name
        :rtype: str
        """
        return self._name

    @property
    def script(self) -> str:
        """Get the actual startup script code.

        :return: startup script text
        :rtype: str
        """
        return self._script


class StartupScriptsService:
    """A service for interacting with the startup scripts endpoint."""

    def __init__(self, http_client) -> None:
        self._http_client = http_client

    def get(self) -> list[StartupScript]:
        """Get all of the client's startup scripts.

        :return: list of startup script objects
        :rtype: list[StartupScript]
        """
        scripts = self._http_client.get(STARTUP_SCRIPTS_ENDPOINT).json()
        scripts_objects = [
            StartupScript(script['id'], script['name'], script['script']) for script in scripts
        ]
        return scripts_objects

    def get_by_id(self, id) -> StartupScript:
        """Get a specific startup script by id.

        :param id: startup script id
        :type id: str
        :return: startup script object
        :rtype: StartupScript
        """
        script = self._http_client.get(STARTUP_SCRIPTS_ENDPOINT + f'/{id}').json()[0]

        return StartupScript(script['id'], script['name'], script['script'])

    def delete(self, id_list: list[str]) -> None:
        """Delete multiple startup scripts by id.

        :param id_list: list of startup scripts ids
        :type id_list: list[str]
        """
        payload = {'scripts': id_list}
        self._http_client.delete(STARTUP_SCRIPTS_ENDPOINT, json=payload)
        return

    def delete_by_id(self, id: str) -> None:
        """Delete a single startup script by id.

        :param id: startup script id
        :type id: str
        """
        self._http_client.delete(STARTUP_SCRIPTS_ENDPOINT + f'/{id}')
        return

    def create(self, name: str, script: str) -> StartupScript:
        """Create a new startup script.

        :param name: startup script name
        :type name: str
        :param script: startup script value
        :type script: str
        :return: the new startup script's id
        :rtype: str
        """
        payload = {'name': name, 'script': script}
        id = self._http_client.post(STARTUP_SCRIPTS_ENDPOINT, json=payload).text
        return StartupScript(id, name, script)
