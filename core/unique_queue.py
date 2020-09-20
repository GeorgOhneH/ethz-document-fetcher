import asyncio


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
            path_without_extension = path.split(".")[:-1]
            extension = path.split(".")[-1]
            item["path"] = ".".join(path_without_extension) + f"({self.paths[path]})." + extension
        else:
            item["path"] += f"({self.paths[path]})"

        self.paths[path] += 1
        return item

