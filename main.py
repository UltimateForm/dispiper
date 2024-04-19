import asyncio
from reactivex import of, operators
from discord_client import DiscordClient
from processors import pipeline_gate, pipeline_sender
from config import ChatPipeline, Env, load_config

env_conf = Env()
config = load_config()
client = DiscordClient(channels=config.channels)
pipelines = of(*config.pipelines)


def pipeline_subscription(pipeline: ChatPipeline):
    client.output.pipe(operators.filter(pipeline_gate(pipeline))).subscribe(
        pipeline_sender(pipeline, client.input)
    )


client.input.subscribe(on_next=lambda x: print(f"Sending message: {repr(x)}"))

pipelines.subscribe(pipeline_subscription)

asyncio.run(client.start(env_conf.d_token))
