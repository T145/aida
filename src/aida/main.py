import anyio
import asyncclick as click


@click.command()
@click.option("--count", default=1, help="Number of greetings.")
@click.option("--name", prompt="Your name", help="The person to greet.")
async def hello(count, name):
    """Simple program that greets NAME for a total of COUNT times."""
    for x in range(count):
        if x:
            await anyio.sleep(0.1)
        click.echo(f"Hello, {name}!")

if __name__ == '__main__':
    hello(_anyio_backend="trio")
