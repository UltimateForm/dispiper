import asyncio
from discord import Embed, Message
from config import ChatPipeline, PipelineParser
from discord_client import DiscordClient
import re
from pygrok import Grok
from typing import Callable


def regex_match(expr: str, value: str):
    return bool(re.search(expr, value))


def pipeline_gate(pipeline: ChatPipeline):
    def processor(message: Message):
        if message.channel.name != pipeline.from_channel:
            return False
        gate = pipeline.gate
        if gate.content:
            return regex_match(gate.content, message.content)
        return False

    return processor


TRANSPORT_PROPS: dict[str, Callable[[Message], str]] = {
    "author": lambda m: m.author.name,
    "utctime": lambda m: m.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    "channel": lambda m: m.channel.name,
}


def parse_message(parser: PipelineParser, message: Message) -> Embed | str:
    pattern = parser.pattern
    additional_props = (
        parser.additional_embed_props
        if parser.output_type == "embed"
        else TRANSPORT_PROPS.keys()
    )
    if parser.source != "content":
        raise NotImplementedError("Currently only parser.source=content is supported")
    content = message.content
    match = Grok(pattern).match(content)
    props = dict(**match)
    additional_props = dict(
        (prop, TRANSPORT_PROPS[prop.lower()](message)) for prop in additional_props
    )
    combined_props = dict(**props, **additional_props)
    if parser.output_type == "embed":
        embed = Embed()
        [
            embed.add_field(name=key, value=combined_props[key], inline=False)
            for key in combined_props.keys()
        ]
        return embed
    else:
        return parser.content_format.format(**combined_props)


def pipeline_sender(pipeline: ChatPipeline, client: DiscordClient):
    def send_to_channel(message: Message):
        if message.content:
            if pipeline.parser:
                msg = parse_message(pipeline.parser, message)
                if isinstance(msg, str):
                    asyncio.create_task(
                        client.send_to_channel(pipeline.channel_name, content=msg)
                    )
                else:
                    asyncio.create_task(
                        client.send_to_channel(pipeline.channel_name, embed=msg)
                    )
            else:
                asyncio.create_task(
                    client.send_to_channel(
                        pipeline.channel_name, content=message.content
                    )
                )
        elif message.embeds:
            first_embed = next(message.embeds, None)
            if first_embed:
                asyncio.create_task(
                    client.send_to_channel(pipeline.channel_name, embed=first_embed)
                )

    return send_to_channel
