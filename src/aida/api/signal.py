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
    client: AsyncClient,
    route: str,
    base_url: str = 'http://localhost',
    port: int = 1337
) -> Any:
    url = '{}:{}/v1/{}/{}'.format(base_url, port, route, os.environ["PHONE_NUMBER"])
    r = await client.get(url)

    if r.status_code != 200:
        raise SignalAPIError('Error when getting {}!'.format(route))

    return r.json()
