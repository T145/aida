import asyncio

import httpx


async def main():
    async with httpx.AsyncClient() as http_client:
        headers = { "Connection": "Upgrade", "Upgrade": "websocket" }
        url = 'http://localhost:1337/v1/groups/+15405204470'

        print(await http_client.get(url, headers=headers))

if __name__ == '__main__':
    asyncio.run(main())
