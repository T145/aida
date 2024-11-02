import base64
import os
from typing import Any

from httpx import AsyncClient


class SignalAPIError(Exception):
    """SignalAPIError base class."""
    pass


def _base64_encode(bits: bytes) -> str:
    return str(base64.b64encode(bits), encoding="utf-8")


async def v1_request(
    http_client: AsyncClient,
    route: str,
    protocol: str = 'http',
    base_url: str = 'localhost',
    port: int = 1337
) -> Any:
    url = '{}://{}:{}/v1/{}/{}'.format(protocol, base_url, port, route, os.environ["PHONE_NUMBER"])
    #headers = { "Connection": "Upgrade", "Upgrade": "websocket" }
    r = await http_client.get(url)

    if r.status_code != 200:
        raise SignalAPIError('Error when getting {}!'.format(url))

    return r.json()
