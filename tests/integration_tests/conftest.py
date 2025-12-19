import os

import pytest
from dotenv import load_dotenv

from verda import VerdaClient

"""
Make sure to run the server and the account has enough balance before running the tests
"""

BASE_URL = os.getenv('VERDA_BASE_URL', 'https://api.verda.com/v1')

# Load env variables, make sure there's an env file with valid client credentials
load_dotenv()
CLIENT_SECRET = os.getenv('VERDA_CLIENT_SECRET')
CLIENT_ID = os.getenv('VERDA_CLIENT_ID')


@pytest.fixture
def verda_client():
    return VerdaClient(CLIENT_ID, CLIENT_SECRET, BASE_URL)
