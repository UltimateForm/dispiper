import asyncio
from discord_client import DiscordClient
from config import ChatPipeline, Env, Config
from reactivex import of, operators
from processors import pipeline_gate, pipeline_sender

env_conf = Env()
config = Config()
client = DiscordClient(channels=config.channels)
pipelines = of(*config.pipelines)


def pipeline_subscription(pipeline: ChatPipeline):
    client.pipe(operators.filter(pipeline_gate(pipeline))).subscribe(
        pipeline_sender(pipeline, client)
    )


pipelines.subscribe(pipeline_subscription)

asyncio.run(client.start(env_conf.D_TOKEN))
