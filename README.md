# Verda Python SDK

[<img src='https://github.com/verda-cloud/sdk-python/workflows/Unit%20Tests/badge.svg'>](https://github.com/verda-cloud/sdk-python/actions?query=workflow%3A%22Unit+Tests%22+branch%3Amaster)
[<img src='https://github.com/verda-cloud/sdk-python/workflows/Code%20Style/badge.svg'>](https://github.com/verda-cloud/sdk-python/actions?query=workflow%3A%22Code+Style%22+branch%3Amaster)
[<img src="https://codecov.io/gh/verda-cloud/sdk-python/branch/master/graph/badge.svg?token=5X5KTYSSPK">](https://codecov.io/gh/verda-cloud/sdk-python)
[<img src='https://readthedocs.org/projects/datacrunch-python/badge/?version=latest'>](https://datacrunch-python.readthedocs.io/en/latest/)
[<img src='https://img.shields.io/github/license/verda-cloud/sdk-python'>](https://github.com/verda-cloud/sdk-python/blob/master/LICENSE)
[<img src='https://img.shields.io/pypi/v/verda?logo=python'>](https://pypi.org/project/verda/)
[<img src='https://img.shields.io/pypi/pyversions/verda'>](https://pypi.org/project/verda/)

The official [Verda](https://verda.com) (formerly DataCrunch) Python SDK.

The SDK's documentation is available on [ReadTheDocs](https://datacrunch-python.readthedocs.io/en/latest/)

Verda Public API documentation [is available here](https://api.verda.com/v1/docs).

This package was originally published under `datacrunch` name, see [MIGRATION.md](./MIGRATION.md) for details.

## Getting Started - Using the SDK:

- Install:

  ```bash
  # via pip
  pip install verda

  # via uv
  uv add verda
  ```

- Generate your client credentials - [instructions in the public API docs](https://api.verda.com/v1/docs#description/quick-start-guide).


- Add your client id and client secret to an environment variable (don't want it to be hardcoded):

  Linux (bash):

  ```bash
  export VERDA_CLIENT_ID=YOUR_ID_HERE
  export VERDA_CLIENT_SECRET=YOUR_SECRET_HERE
  ```

- To enable sending inference requests from SDK you must generate an inference key - [Instructions on inference authorization](https://docs.verda.com/inference/authorization)

- Add your inference key to an environment variable

  Linux (bash):
 
  ```bash
  export VERDA_INFERENCE_KEY=YOUR_API_KEY_HERE
  ```
  
  Other platforms:
  https://en.wikipedia.org/wiki/Environment_variable

- Example for creating a new instance:

  ```python
  import os
  from verda import VerdaClient
  from verda.constants import Actions

  # Get credentials from environment variables
  CLIENT_ID = os.environ['VERDA_CLIENT_ID']
  CLIENT_SECRET = os.environ['VERDA_CLIENT_SECRET']

  # Create client
  verda = VerdaClient(CLIENT_ID, CLIENT_SECRET)

  # Get all SSH keys
  ssh_keys = [key.id for key in verda.ssh_keys.get()]

  # Create a new instance
  instance = verda.instances.create(instance_type='1V100.6V',
                                    image='ubuntu-24.04-cuda-12.8-open-docker',
                                    ssh_key_ids=ssh_keys,
                                    hostname='example',
                                    description='example instance')

  # Delete instance
  verda.instances.action(instance.id, Actions.DELETE)
  ```

  More examples can be found in the [/examples](./examples) folder or in the [documentation](https://datacrunch-python.readthedocs.io/en/latest/).

## Development

### Set up the local development environment

Prerequisite: install [`uv`](https://docs.astral.sh/uv/).

Clone the repository, create local environment and install dependencies:

  ```bash
  git clone git@github.com:verda-cloud/sdk-python.git
  cd sdk-python
  uv sync
  ```

### Run Tests

- Execute all tests

  ```bash
  uv run pytest
  ```

- Execute a single test file

  ```bash
  uv run pytest tests/unit_tests/test_file.py
  ```

### Local Manual Testing

Create a file in the root directory of the project:

```python
# example.py
from verda import VerdaClient

CLIENT_SECRET = 'secret'
CLIENT_ID = 'your-id'

# Create client
verda = VerdaClient(CLIENT_ID, CLIENT_SECRET)
```

Run it:

```bash
uv run python example.py
```

### Generating the documentation

If added a new service, create a documentation template under api/services for that service.

```bash
cd docs
make html
```

### Code style

```bash
# Lint
uv run ruff check

# Format code
uv run ruff format
```

## Contact

You can [contact us here](https://verda.com/contact), or open an issue in the repo.
