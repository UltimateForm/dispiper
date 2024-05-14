import asyncio
from reactivex import Observable, Observer, create
from discord import Embed

from config import MessageEvent


class Plugin:
    name: str

    def __init__(self, name):
        self.name = name

    async def handle(self, observer: Observer[MessageEvent], msg: MessageEvent):
        observer.on_next(msg)

    def operator(self, source: Observable[MessageEvent]):
        def subscribe(observer: Observer[MessageEvent], scheduler=None):
            def on_next(value: str):
                asyncio.create_task(self.handle(observer, value))

            return source.subscribe(
                on_next, observer.on_error, observer.on_completed, scheduler=scheduler
            )

        return create(subscribe)
