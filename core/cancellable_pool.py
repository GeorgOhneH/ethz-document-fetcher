import asyncio
import multiprocessing
from functools import partial


class CancellablePool(object):
    def __init__(self, max_workers=None):
        if max_workers is None:
            max_workers = multiprocessing.cpu_count()
        self.max_workers = max_workers
        self._free = set()
        self._working = set()
        self._change = asyncio.Event()

    def _new_pool(self):
        return multiprocessing.Pool(1)

    async def apply(self, fn, *args):
        """
        Like multiprocessing.Pool.apply_async, but:
         * is an asyncio coroutine
         * terminates the process if cancelled
        """
        if len(self._free) + len(self._working) < self.max_workers:
            self._free.add(self._new_pool())

        while not self._free:
            await self._change.wait()
            self._change.clear()
        pool = usable_pool = self._free.pop()
        self._working.add(pool)

        loop = asyncio.get_event_loop()
        fut = loop.create_future()

        def save_fut_set_result(future, obj):
            if future.cancelled():
                return
            future.set_result(obj)

        def save_fut_set_exception(future, err):
            if future.cancelled():
                return
            future.set_exception(err)

        def _on_done(obj):
            loop.call_soon_threadsafe(partial(save_fut_set_result, future=fut, obj=obj))

        def _on_err(err):
            loop.call_soon_threadsafe(partial(save_fut_set_exception, future=fut, err=err))

        pool.apply_async(fn, args, callback=_on_done, error_callback=_on_err)

        cancel = False
        try:
            return await fut
        except asyncio.CancelledError as e:
            cancel = True
            raise e
        finally:
            if cancel:
                pool.terminate()
                self._working.remove(pool)
                self._change.set()
            else:
                self._working.remove(pool)
                self._free.add(usable_pool)
                self._change.set()

    def shutdown(self):
        for p in self._working | self._free:
            p.terminate()
        self._free.clear()
