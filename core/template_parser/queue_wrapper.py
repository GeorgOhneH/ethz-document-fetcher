import asyncio
import inspect


def queue_wrapper_put(obj, attr, **consumer_kwargs):
    signal_handler = consumer_kwargs["signal_handler"]
    unique_key = consumer_kwargs["unique_key"]

    async def inside(*args, **kwargs):
        if kwargs.get("item"):
            kwargs["item"].update(consumer_kwargs)
        else:
            args[0].update(consumer_kwargs)
        signal_handler.start(unique_key)  # finish signal in downloader

        await getattr(obj, attr)(*args, **kwargs)

    return inside


class QueueWrapper:
    def __init__(self, queue, signal_handler, unique_key, site_settings, **kwargs):
        kwargs["signal_handler"] = signal_handler
        kwargs["unique_key"] = unique_key
        kwargs["site_settings"] = site_settings
        self.consumer_kwargs = kwargs
        setattr(self, "put", queue_wrapper_put(queue, "put", **kwargs))
