from discord import Color
from reactivex import Observer
from config import MessageEvent
from plugins.plugin_base import Plugin


class EmbedSigner(Plugin):
    async def handle(self, observer: Observer[MessageEvent], msg: MessageEvent):
        if msg.embed:
            msg.embed.set_footer(text="Created by Dispiper")
        return await super().handle(observer, msg)
