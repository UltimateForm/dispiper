from typing import Callable
from reactivex import Observer
from pygrok import Grok
from discord import Embed, Message
from config import ChatPipeline, InputMessage, PipelineParser
from text_processing import regex_match, embed_to_dict


def pipeline_gate(pipeline: ChatPipeline):
    def processor(message: Message):
        if message.channel.name != pipeline.from_channel:
            return False
        gate = pipeline.gate
        if gate.content and message.content:
            is_match = regex_match(gate.content, message.content)
            return is_match
        if gate.embed and message.embeds:
            first_embed = message.embeds[0]
            gate_keys = gate.embed.keys()
            embed_dict = embed_to_dict(first_embed.description)
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
        (key, func(message)) for (key, func) in TRANSPORT_PROPS.items()
    )
    available_props = dict(**match, **resolved_transport_props)
    output_pattern_keys = (
        output_pattern
        if isinstance(output_pattern, list)
        else available_props
        # `else available_props` because should only happen
        # (due to above type checks) when output type is content
        # and in that case we want to use everything for formatting output string
        # since selection will be done by str.format
    )
    selected_props = dict((key, available_props[key]) for key in output_pattern_keys)
    if parser.output.type == "embed":
        embed = Embed()
        [
            embed.add_field(name=key, value=value, inline=False)
            for (key, value) in selected_props.items()
        ]
        return embed
    elif parser.output.type == "content":
        return parser.output.pattern.format(**selected_props)
    else:
        raise NotImplementedError(
            f"Only supported output types are embed and content,\nreceived {parser.output.type}"
        )


def pipeline_sender(pipeline: ChatPipeline, input_observer: Observer[InputMessage]):
    def send_to_channel(message: Message):
        input_message = InputMessage(
            None, None, pipeline.channel_id, pipeline.channel_name
        )
        if message.content:
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
        elif message.embeds:
            first_embed = next(iter(message.embeds), None)
            if first_embed:
                input_message.embed = first_embed
        input_observer.on_next(input_message)

    return send_to_channel
