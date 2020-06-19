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
        signal_handler.start(unique_key)

        await getattr(obj, attr)(*args, **kwargs)

    return inside


class QueueWrapper:
    def __init__(self, obj, signal_handler, unique_key, **kwargs):
        kwargs["signal_handler"] = signal_handler
        kwargs["unique_key"] = unique_key
        self.consumer_kwargs = kwargs
        for attr, method in obj.__class__.__dict__.items():
            if callable(method):
                if inspect.iscoroutinefunction(method) or asyncio.iscoroutinefunction(method):
                    if attr == "put":
                        setattr(self, attr, queue_wrapper_put(obj, attr, **kwargs))
