import asyncio
from reactivex import of, operators
from discord_client import DiscordClient
from plugins.embed_signer import EmbedSigner
from processors import pipeline_gate, pipeline_sender
from config import ChatPipeline, Env, load_config

env_conf = Env()
config = load_config()
client = DiscordClient(channels=config.channels)
pipelines = of(*config.pipelines)


def pipeline_subscription(pipeline: ChatPipeline):
    client.input.pipe(operators.filter(pipeline_gate(pipeline))).subscribe(
        pipeline_sender(pipeline, client.output)
    )


client.output.pipe(EmbedSigner("signer").operator).subscribe(client.send_message)
client.output.subscribe(on_next=lambda x: print(f"Sending message: {repr(x)}"))

pipelines.subscribe(pipeline_subscription)

asyncio.run(client.start(env_conf.d_token))
