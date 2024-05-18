from collections import ChainMap
from typing import Callable
from reactivex import Observer
from pygrok import Grok
from discord import Embed, Message
from config import (
    ChatPipeline,
    EmbedOptions,
    MessageEvent,
    PipelineParser,
    PipelineParserNode,
)
from text_processing import regex_match, embed_to_dict


def pipeline_gate(pipeline: ChatPipeline):
    def processor(message: Message):
        if not pipeline.gate:
            return False
        if message.channel.name != pipeline.from_channel:
            return False
        gate = pipeline.gate
        if gate.content and message.content:
            is_match = regex_match(gate.content, message.content)
            return is_match
        if gate.embed and message.embeds:
            first_embed = message.embeds[0]
            gate_keys = gate.embed.keys()
            embed_dict = embed_to_dict(first_embed)
            message_embed_as_dict = dict(
                (key, value)
                for (key, value) in embed_dict.items()
                if key and value and key in gate_keys
            )
            if not bool(message_embed_as_dict):
                # message embed has no elligible fields
                return False
            all_match = all(
                regex_match(gate.embed[key], value)
                for (key, value) in message_embed_as_dict.items()
            )
            return all_match
        return False

    return processor


TRANSPORT_PROPS: dict[str, Callable[[Message], str]] = {
    "Author": lambda m: m.author.name,
    "UtcTime": lambda m: m.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    "Channel": lambda m: m.channel.name,
}


def apply_embed_options(embed: Embed, options: EmbedOptions):
    if options.title:
        embed.title = options.title
    if options.color:
        embed.color = options.color
    if options.description:
        embed.description = options.description


def parse_from_input(node: PipelineParserNode, message: Message) -> dict[str, str]:
    input_pattern = node.pattern
    matches: list[dict[str, str]]
    input_content: str | dict[str, str]
    if node.msg_type == "embed":
        if message.embeds is None or len(message.embeds) == 0:
            raise ValueError(f"Message {message.id} has no embeds to be parsed")
        input_embed: Embed = message.embeds[0]
        input_embed_dict = embed_to_dict(input_embed)
        input_content = input_embed_dict
        if isinstance(input_pattern, str):
            parse_sources = input_embed_dict.values()
            matches = [Grok(input_pattern).match(text) for text in parse_sources]
        elif isinstance(input_content, dict):
            input_keys = node.pattern.keys()
            matches = [
                Grok(input_pattern[key]).match(input_embed_dict.get(key, ""))
                for key in input_keys
            ]
    elif node.msg_type == "content":
        input_content = message.content
        match = Grok(input_pattern).match(input_content)
        matches = [match]
    else:
        raise ValueError(f"Parser of type {node.msg_type} is not supported")
    if not matches or not any(matches):
        raise ValueError(
            f"No match found for '{input_pattern}' on '{input_content}'. Make sure your pipeline gate is correct."
        )
    matches_merged = dict(ChainMap(*matches))
    return matches_merged


def parse_to_output(tokens: dict[str, str], node: PipelineParserNode) -> Embed | str:
    output_pattern = node.pattern
    output_pattern_keys = (
        output_pattern
        if isinstance(output_pattern, list)
        else tokens
        # `else tokens` because should only happen
        # (due to above type checks) when output type is content
        # and in that case we want to use everything for formatting output string
        # since selection will be done by str.format
    )
    selected_props = dict((key, tokens[key]) for key in output_pattern_keys)
    if node.msg_type == "embed":
        embed = Embed()
        for key, value in selected_props.items():
            embed.add_field(name=key, value=value, inline=False)
        return embed
    if node.msg_type == "content":
        return output_pattern.format(**selected_props)
    else:
        raise NotImplementedError(
            f"Only supported output types are embed and content,\nreceived {node.msg_type}"
        )


def parse_message(parser: PipelineParser, message: Message) -> Embed | str:
    print(f"Parsing {message}")
    matches = parse_from_input(parser.input, message) if parser.input else {}
    resolved_transport_props = dict(
        (key, func(message)) for (key, func) in TRANSPORT_PROPS.items()
    )
    available_props = {**matches, **resolved_transport_props}
    output_msg: str | Embed
    if parser.output:
        output_msg = parse_to_output(available_props, parser.output)
    else:
        output_msg = message.content or message.embeds[0]
    if isinstance(output_msg, Embed) and parser.embed_options:
        apply_embed_options(output_msg, parser.embed_options)
    return output_msg


def pipeline_sender(pipeline: ChatPipeline, input_observer: Observer[MessageEvent]):
    def send_to_channel(message: Message):
        input_message = MessageEvent(
            None, None, pipeline.channel_id, pipeline.channel_name
        )
        if pipeline.parser:
            msg = parse_message(pipeline.parser, message)
            if isinstance(msg, str):
                input_message.content = msg
            elif isinstance(msg, Embed):
                input_message.embed = msg
            else:
                raise ValueError(f"Ecountered unexpected message type: {msg}")
        else:
            input_message.content = message.content
            input_message.embed = (
                message.embeds[0] if message.embeds and len(message.embeds) else None
            )
        input_observer.on_next(input_message)

    return send_to_channel
