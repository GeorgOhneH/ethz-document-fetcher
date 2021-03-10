import asyncio

from core.utils import insert_text_before_extension


class UniqueQueue(asyncio.Queue):
    def __init__(self):
        super().__init__()
        self.paths = {}

    async def get(self):
        item = await super().get()

        path = item["path"]
        with_extension = item.get("with_extension", True)

        if path not in self.paths:
            self.paths[path] = 1
            return item

        if with_extension:
            item["path"] = insert_text_before_extension(item["path"], f"({self.paths[path]})")
        else:
            item["path"] += f"({self.paths[path]})"

        self.paths[path] += 1
        return item

