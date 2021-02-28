import logging
import asyncio

import aiohttp
from tenacity import retry, stop_after_attempt, retry_if_exception_type, wait_fixed

logger = logging.getLogger(__name__)


def after_log():
    def log_it(retry_state):
        e = retry_state.outcome.exception()
        logger.warning(f"Request was not successful for url. {retry_state.args[2]}. "
                       f"Error: {e.__class__.__name__} {e}. Attempt: {retry_state.attempt_number}")

    return log_it


class MonitorSession(aiohttp.ClientSession):
    def __init__(self, signals, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.signals = signals

    @retry(reraise=True,
           wait=wait_fixed(1),
           stop=stop_after_attempt(4),
           after=after_log(),
           retry=retry_if_exception_type((asyncio.TimeoutError,
                                          aiohttp.client_exceptions.ServerDisconnectedError)))
    async def _request(self, *args, **kwargs):
        response = await super()._request(*args, **kwargs)
        headers_length = sum((len(key) + len(value) for key, value in response.raw_headers))
        if self.signals is not None:
            self.signals.downloaded_content_length.emit(headers_length)
        response.content.read = async_monitor_length_bytes(response.content.read, signals=self.signals)
        return response


def async_monitor_length_bytes(func, signals):
    async def wrapper(*args, **kwargs):
        result = await func(*args, **kwargs)
        if signals is not None:
            signals.downloaded_content_length.emit(len(result))
        return result

    return wrapper
