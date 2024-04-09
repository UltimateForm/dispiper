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
            is_match = regex_match(gate.content, message.content)
            return is_match
        return False

    return processor


TRANSPORT_PROPS: dict[str, Callable[[Message], str]] = {
    "Author": lambda m: m.author.name,
    "UtcTime": lambda m: m.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    "Channel": lambda m: m.channel.name,
}


def parse_message(parser: PipelineParser, message: Message) -> Embed | str:
    input_pattern = parser.input.pattern
    output_pattern = parser.output.pattern

    if not isinstance(input_pattern, str):
        raise TypeError("Non string input patterns are not supported")

    if parser.input.type != "content":
        raise NotImplementedError("Currently only parser.source=content is supported")

    if parser.output.type == "embed" and not isinstance(output_pattern, list):
        raise NotImplementedError(
            "Type list is the only supported pattern type for embed output"
        )

    if parser.output.type == "content" and not isinstance(output_pattern, str):
        raise NotImplementedError(
            "Type str is the only supported pattern type for content output"
        )

    input_content = message.content
    match = Grok(input_pattern).match(input_content)
    resolved_transport_props = dict(
        (key, TRANSPORT_PROPS[key](message)) for key in TRANSPORT_PROPS.keys()
    )
    available_props = dict(**match, **resolved_transport_props)
    output_pattern_keys = (
        output_pattern
        if isinstance(output_pattern, list)
        else available_props
        # `else available_props` because should only happen (due to above type checks) when output type is content
        # and in that case we want to use everything for formatting output string
        # since selection will be done by str.format
    )
    selected_props = dict((key, available_props[key]) for key in output_pattern_keys)
    if parser.output.type == "embed":
        embed = Embed()
        [
            embed.add_field(name=key, value=selected_props[key], inline=False)
            for key in selected_props.keys()
        ]
        return embed
    elif parser.output.type == "content":
        return parser.output.pattern.format(**selected_props)
    else:
        raise NotImplementedError(
            f"Only supported output types are embed and content, received {parser.output.type}"
        )


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
