from os import environ
import json
from dataclasses import dataclass, field
from dacite import from_dict
from discord import Embed


class Env:
    d_token: str

    def __init__(self):
        self.d_token = environ["D_TOKEN"]


@dataclass
class MessageEvent:
    content: str | None
    embed: Embed | None
    channel_id: int
    channel_name: str


@dataclass
class ChatPipelineGate:
    content: str | None
    embed: dict[str, str] | None


@dataclass
class PipelineParserNode:
    pattern: str | list[str] | dict
    type: str

    def __post_init__(self):
        if isinstance(self.pattern, dict) and self.type != "embed":
            raise ValueError(
                "Pattern of type dict is only supported with parser node of type embed"
            )


@dataclass
class EmbedOptions:
    title: str | None
    color: int | None
    description: str | None


@dataclass
class PipelineParser:
    input: PipelineParserNode
    output: PipelineParserNode
    embed_options: EmbedOptions | None


@dataclass
class ChatPipeline:
    gate: ChatPipelineGate | None
    channel_id: int
    channel_name: str
    from_channel: str | None
    parser: PipelineParser | None


@dataclass
class Config:
    pipelines: list[ChatPipeline] = field(default_factory=lambda: [])
    channels: set[int] = field(init=False)

    def __post_init__(self):
        self.channels = set(pipeline.channel_id for pipeline in self.pipelines)


def load_config(path: str = "./config.json"):
    json_data: dict = None
    with open(path, "r", encoding="utf8") as j:
        json_data = json.loads(j.read())
    config_data = from_dict(data_class=Config, data=json_data)
    return config_data


if __name__ == "__main__":
    config = load_config()
    print(config)
