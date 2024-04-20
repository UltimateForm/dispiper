import asyncio
from typing import Any, Optional
import discord
from reactivex import Subject, operators
from config import Env, InputMessage


class DiscordClient(discord.Client):
    _channel_ids: set[int] = set()
    _channels: list[discord.TextChannel] = []
    input: Subject[discord.Message]
    output: Subject[InputMessage]

    def __init__(self, channels: set[int], **options: Any):
        intents = discord.Intents.default()
        intents.message_content = True
        self._channel_ids = channels
        discord.Client.__init__(self, intents=intents, **options)
        self.input = Subject()
        self.output = Subject()
        self.output.subscribe(on_next=self._output_on_next)

    async def on_ready(self):
        for known_channel_id in self._channel_ids:
            channel = await self.fetch_channel(known_channel_id)
            self._channels.append(channel)

    def _output_on_next(self, msg: InputMessage):
        if msg.content:
            asyncio.create_task(
                self.send_to_channel(msg.channel_name, content=msg.content)
            )
        elif msg.embed:
            asyncio.create_task(self.send_to_channel(msg.channel_name, embed=msg.embed))
        else:
            raise ValueError(f"Encounterd unexpected input message type: {repr(msg)}")

    async def send_to_channel(
        self,
        channel_name,
        content: Optional[str] = None,
        embed: Optional[discord.Embed] = None,
    ):
        target_channel = next(
            (channel for channel in self._channels if channel.name == channel_name),
            None,
        )
        if not target_channel:
            print(
                f"Failed to send to {channel_name}, channel unregonized. Possible missing config."
            )
            return
        await target_channel.send(content=content, embed=embed)

    async def on_message(self, message: discord.message.Message):
        self.input.on_next(message)


if __name__ == "__main__":
    from config import Config

    env_conf = Env()
    config = Config()
    client = DiscordClient(channels=config.channels)
    client.pipe(operators.filter(lambda x: x.content == "ping")).subscribe(
        on_next=lambda x: asyncio.create_task(x.reply("pong"))
    )
    asyncio.run(client.start(env_conf.d_token))
