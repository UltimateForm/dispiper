from os import environ
import json
from discord import Embed, Message


class Env:
    D_TOKEN: str

    def __init__(self):
        self.D_TOKEN = environ["D_TOKEN"]


class ChatPipelineGate:
    content: str | None
    embed: Embed | None

    def __init__(self, raw: dict):
        self.content = raw.get("content")
        if "embed" in raw.keys():
            embed_raw = raw["embed"]
            self.embed = Embed()
            self.embed.add_field(name="Message", value=embed_raw.get("Message"))


class PipelineParser:
    source: str
    pattern: str
    output_type: str
    additional_embed_props: list[str]
    content_format: str | None

    def __init__(self, raw: dict):
        self.source = raw["source"]
        self.pattern = raw["pattern"]
        self.output_type = raw["output_type"]
        self.additional_embed_props = raw.get("additional_embed_props") or []
        self.content_format = raw.get("content_format")


class ChatPipeline:
    gate: ChatPipelineGate | None
    channel_id: str
    channel_name: str
    from_channel: str | None
    parser: PipelineParser | None

    def __init__(self, raw: dict):
        self.channel_name = raw["channel_name"]
        self.from_channel = raw.get("from_channel")
        self.channel_id = raw["channel_id"]
        raw_keys = raw.keys()
        if "gate" in raw_keys:
            self.gate = ChatPipelineGate(raw["gate"])
        if "parser" in raw_keys:
            self.parser = PipelineParser(raw["parser"])


class Config:
    pipelines: list[ChatPipeline] = []
    channels: set[int] = set()
    _raw_dict: dict

    def __init__(self):
        with open("./config.json", "r") as j:
            self._raw_dict = json.loads(j.read())
        for raw_pipeline in self._raw_dict["pipelines"]:
            pipeline = ChatPipeline(raw_pipeline)
            self.pipelines.append(pipeline)
            self.channels.add(pipeline.channel_id)


if __name__ == "__main__":
    con = Config()
    print(con.channels)
    firstEmbed = con.pipelines[0].gate.embed
