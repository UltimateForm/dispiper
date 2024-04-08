import asyncio
from discord_client import DiscordClient
from config import Env, Config
from reactivex import operators
from processors import pipeline_gate, pipeline_sender

env_conf = Env()
config = Config()
client = DiscordClient(channels=config.channels)
for pipeline in config.pipelines:
    client.pipe(operators.filter(pipeline_gate(pipeline))).subscribe(
        pipeline_sender(pipeline, client)
    )
asyncio.run(client.start(env_conf.D_TOKEN))
