import asyncio
import os
import random
from typing import Any, Dict, List

import asyncclick as click
import httpx
from dotenv import dotenv_values
from pymongo import UpdateOne
from rich.console import Console
from rich.progress import Progress, SpinnerColumn
from rich.traceback import install

from .api import signal
from .api.mongo import AsyncMongoDBSaver
from .core import chat

console = Console()

# Important for streaming files: https://www.python-httpx.org/async/#streaming-requests


async def my_async_function(progress, task, job_id):
    delay = random.randint(1,3)
    await asyncio.sleep(delay)
    progress.update(task, description="ID: {}, Job's done! {}s".format(job_id, delay), advance=1)

# Main thread controls the terminal output

def _get_signal_group_write_ops(groups: List[Dict[str, Any]]) -> List[UpdateOne]:
    ops = list()
    for group in groups:
        group['members'] = [i for i in group['members'] if i]
        group_id = group.pop('id')
        mongo_id = group.pop('internal_id')
        ops.append(UpdateOne({"_id": mongo_id}, {"$set": {"group_id": group_id, **group}}, upsert=True))
    return ops


@click.command()
# @click.option("--count", default=1, help="Number of greetings.")
# @click.option("--name", prompt="Your name", help="The person to greet.")
async def hello():
    install(console=console)

    config = dotenv_values(".env")
    os.environ["PHONE_NUMBER"] = config["PHONE_NUMBER"]
    transport = httpx.AsyncHTTPTransport(retries=1)
    loop = asyncio.get_event_loop()

    async with httpx.AsyncClient(transport=transport) as http_client:
        async with AsyncMongoDBSaver.from_conn_info(
            host='localhost', port=27017, db_name='checkpoints'
        ) as checkpointer:
            with Progress(
                SpinnerColumn(spinner_name='dots12'),
                "[progress.description]{task.description}",
                console=console,
            ) as progress:
                signal_db = checkpointer.client['signal']

                await signal_db['groups'].bulk_write(
                    _get_signal_group_write_ops(await signal.v1_request(http_client, 'groups'))
                )

                aida = await chat.build_graph(checkpointer)
                config = {'configurable': {'thread_id': '5', 'user_id': '5'}}
                inputs = {'messages': []}

                # inputs['messages'].append(HumanMessage(content="Andy: What is the sum of the years when Kevin Costner and Mark Cuban were born?"))

                progress_task = progress.add_task("Waiting for messages...")
                #tasks = [my_async_function(progress, task, job_id) for job_id in range(10)]

                try:
                    while True:
                        await asyncio.sleep(2)
                        messages = await signal.v1_request(http_client, 'receive')

                        if len(messages) > 0:
                            console.log('Got {} message{}!'.format(len(messages), 's' if len(messages) > 1 else ''))

                        for dm in messages:
                            await signal_db['messages2'].insert_one(dm)
                            dm = dm['envelope']
                            user = dm['sourceName']
                            console.log(dm)
                            await signal_db['messages2'].insert_one(dm)

                            if "syncMessage" in dm:
                                dm = dm["syncMessage"]

                                if "sentMessage" not in dm:
                                    continue

                                dm = dm["sentMessage"]
                            elif "dataMessage" in dm:
                                dm = dm["dataMessage"]
                            else:
                                continue

                            if "message" not in dm:
                                continue

                            text = dm['message'].strip()

                            if not text:
                                continue # It's a reaction or multimedia

                            await signal_db['messages'].insert_one(dm)
                            progress.reset(progress_task)
                except (asyncio.CancelledError, KeyboardInterrupt):
                    progress.stop_task(progress_task)

                # for job in asyncio.as_completed(tasks):
                #     await job

        console.clear()
        console.log('--- FINISHED ---')


if __name__ == '__main__':
    hello(_anyio_backend="asyncio")
