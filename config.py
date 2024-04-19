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
class InputMessage:
    content: str | None
    embed: Embed | None
    channel_id: int
    channel_name: str


@dataclass
class ChatPipelineGate:
    content: str | None
    embed: dict | None


@dataclass
class PipelineParserNode:
    pattern: str | list[str]
    type: str


@dataclass
class PipelineParser:
    input: PipelineParserNode
    output: PipelineParserNode


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
