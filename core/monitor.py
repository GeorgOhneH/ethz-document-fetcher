import aiohttp


class MonitorSession(aiohttp.ClientSession):
    def __init__(self, signals, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.signals = signals

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
