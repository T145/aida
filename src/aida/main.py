import asyncio
import os
import random

import asyncclick as click
import httpx
from dotenv import dotenv_values
from rich.console import Console
from rich.progress import Progress, SpinnerColumn
from rich.traceback import install

from .api import signal

console = Console()

# Important for sreaming files: https://www.python-httpx.org/async/#streaming-requests


async def my_async_function(progress, task, job_id):
    delay = random.randint(1,3)
    await asyncio.sleep(delay)
    progress.update(task, description="ID: {}, Job's done! {}s".format(job_id, delay), advance=1)
    #return job_id, delay

# Main thread controls the terminal output


@click.command()
# @click.option("--count", default=1, help="Number of greetings.")
# @click.option("--name", prompt="Your name", help="The person to greet.")
async def hello():
    install(console=console)

    config = dotenv_values(".env")
    os.environ["PHONE_NUMBER"] = config["PHONE_NUMBER"]
    transport = httpx.AsyncHTTPTransport(retries=1)

    async with httpx.AsyncClient(transport=transport) as client:
        with Progress(
            SpinnerColumn(spinner_name='dots12'),
            "[progress.description]{task.description}",
            console=console,
        ) as progress:
            console.log(await signal.v1_request(client, 'groups'))
            task = progress.add_task("Waiting for messages...")
            tasks = [my_async_function(progress, task, job_id) for job_id in range(10)]

            for job in asyncio.as_completed(tasks):
                #job_id, delay = await job
                await job
                #console.log("ID: {}, Job's done! {}s".format(job_id, delay))

            progress.stop()

        console.clear()
        console.log('--- FINISHED ---')


if __name__ == '__main__':
    hello(_anyio_backend="asyncio")
