import asyncio
from typing import Any, Optional
import discord
from config import Env

from reactivex import Subject, operators


class DiscordClient(discord.Client, Subject[discord.Message]):
    _channel_ids: set[int] = set()
    _channels: list[discord.TextChannel] = []

    def __init__(self, channels: set[int] = set(), **options: Any):
        intents = discord.Intents.default()
        intents.message_content = True
        self._channel_ids = channels
        discord.Client.__init__(self, intents=intents, **options)
        Subject.__init__(self)

    async def on_ready(self):
        for known_channel_id in self._channel_ids:
            channel = await self.fetch_channel(known_channel_id)
            self._channels.append(channel)

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
        self.on_next(message)


if __name__ == "__main__":
    from config import Config

    env_conf = Env()
    config = Config()
    client = DiscordClient(channels=config.channels)
    client.pipe(operators.filter(lambda x: x.content == "ping")).subscribe(
        on_next=lambda x: asyncio.create_task(x.reply("pong"))
    )
    asyncio.run(client.start(env_conf.D_TOKEN))
