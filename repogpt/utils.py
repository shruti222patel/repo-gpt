import asyncio


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)

        return cls._instances[cls]


async def merge_generators(*generators):
    async def collect_all(async_gen):
        async for item in async_gen:
            yield item

    tasks = [collect_all(gen) for gen in generators]
    for next_to_complete in asyncio.as_completed(tasks):
        async for item in next_to_complete:
            yield item
