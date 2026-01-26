"""Client initialization from environment variables."""

import os

import typer

from verda import VerdaClient


def get_client() -> VerdaClient:
    """Initialize VerdaClient from environment variables.

    Required environment variables:
        VERDA_CLIENT_ID: API client ID
        VERDA_CLIENT_SECRET: API client secret

    Optional environment variables:
        VERDA_BASE_URL: API base URL (default: https://api.verda.ai/v1)
        VERDA_INFERENCE_KEY: Inference API key

    Returns:
        Initialized VerdaClient instance

    Raises:
        typer.Exit: If required credentials are missing
    """
    client_id = os.environ.get('VERDA_CLIENT_ID')
    client_secret = os.environ.get('VERDA_CLIENT_SECRET')
    base_url = os.environ.get('VERDA_BASE_URL')
    inference_key = os.environ.get('VERDA_INFERENCE_KEY')

    if not client_id or not client_secret:
        typer.echo(
            'Error: VERDA_CLIENT_ID and VERDA_CLIENT_SECRET environment variables are required.',
            err=True,
        )
        typer.echo('Set them with:', err=True)
        typer.echo('  export VERDA_CLIENT_ID=your_client_id', err=True)
        typer.echo('  export VERDA_CLIENT_SECRET=your_client_secret', err=True)
        raise typer.Exit(code=1)

    kwargs = {
        'client_id': client_id,
        'client_secret': client_secret,
    }
    if base_url:
        kwargs['base_url'] = base_url
    if inference_key:
        kwargs['inference_key'] = inference_key

    return VerdaClient(**kwargs)
