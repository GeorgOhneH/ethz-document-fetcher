import asyncio
import logging
import traceback

import yaml

from core.exceptions import ParseTemplateError, LoginError
from core.template_parser.nodes import Root, Folder, Site
from core.template_parser.signal_handler import SignalHandler
from settings import global_settings

logger = logging.getLogger(__name__)


class Template(object):
    def __init__(self, path, signals=None):
        self.path = path
        self.signal_handler = SignalHandler(signals=signals)
        self.root = Root()
        self.data = None
        self.nodes = {}

    def __iter__(self):
        def gen(node):
            yield node
            if node.folder is not None:
                yield from gen(node.folder)
            for site in node.sites:
                yield from gen(site)

        return gen(self.root)

    def load(self):
        if self.path is None:
            self.data = {}
        else:
            self.data = self.load_data(self.path)

        if self.data is None:
            self.data = {}

        self.parse_template()

        self.nodes = {node.unique_key: node for node in iter(self)}

    def load_data(self, path):
        with open(path) as f:
            data = yaml.load(f, Loader=yaml.Loader)

        return data

    def parse_template(self):
        if "folder" in self.data:
            self.parse_folder(data=self.data["folder"], parent=self.root)
        if "sites" in self.data:
            self.parse_sites(data=self.data["sites"], parent=self.root)

    def parse_folder(self, data, parent):
        if "name" not in data:
            raise ParseTemplateError("Expected a 'name' field in folder")

        folder = Folder(name=data["name"],
                        parent=parent)

        if "sites" in data:
            self.parse_sites(data=data["sites"], parent=folder)

        if "folder" in data:
            self.parse_folder(data=data["folder"], parent=folder)

    def parse_sites(self, data, parent):
        for producer_dict in data:
            if "module" in producer_dict and "folder" in producer_dict:
                raise ParseTemplateError("only module or folder allowed, not both")

            if "module" in producer_dict:
                self.parse_producer(p_kwargs=producer_dict, parent=parent)

            elif "folder" in producer_dict:
                self.parse_folder(data=producer_dict["folder"], parent=parent)
            else:
                raise ParseTemplateError("'module' or 'folder' field required")

    def parse_producer(self, p_kwargs, parent):
        raw_module_name = p_kwargs.pop("module")

        sub_sites = p_kwargs.pop("sites", None)
        folder = p_kwargs.pop("folder", None)

        raw_folder_name = p_kwargs.pop("folder_name", None)
        use_folder = p_kwargs.pop("use_folder", True)
        possible_consumer_kwargs = ["allowed_extensions", "forbidden_extensions"]
        consumer_kwargs = {name: p_kwargs.pop(name, None) for name in possible_consumer_kwargs}

        raw_function = p_kwargs.pop("function", None)
        raw_folder_function = p_kwargs.pop("folder_function", None)

        site = Site(
            raw_module_name=raw_module_name,
            use_folder=use_folder,
            raw_folder_name=raw_folder_name,
            raw_function=raw_function,
            raw_folder_function=raw_folder_function,
            function_kwargs=p_kwargs,
            consumer_kwargs=consumer_kwargs,
            parent=parent
        )

        if sub_sites is not None:
            self.parse_sites(data=sub_sites, parent=site)
        if folder is not None:
            self.parse_folder(data=folder, parent=site)

    async def run_root(self, producers, session, queue, site_settings, cancellable_pool):
        await self.run(self.root,
                       producers=producers,
                       session=session,
                       queue=queue,
                       site_settings=site_settings,
                       cancellable_pool=cancellable_pool)

    async def run_from_unique_key(self, unique_key, producers, session, queue,
                                  site_settings, cancellable_pool, recursive):
        await self.run(node=self.nodes[unique_key],
                       producers=producers,
                       session=session,
                       queue=queue,
                       site_settings=site_settings,
                       cancellable_pool=cancellable_pool,
                       recursive=recursive)

    async def run(self, node, producers, session, queue, site_settings, cancellable_pool, recursive=True):
        tasks = []

        coroutine = self.add_producer_exception_handler(node.add_producers, node)(producers,
                                                                                  session,
                                                                                  queue,
                                                                                  site_settings,
                                                                                  cancellable_pool,
                                                                                  self.signal_handler)
        if node.base_path is None:
            await coroutine
        else:
            tasks.append(asyncio.ensure_future(coroutine))

        if recursive and node.base_path is not None:
            if node.folder is not None:
                tasks.append(self.run(node.folder, producers, session, queue, site_settings, cancellable_pool))
            for site in node.sites:
                tasks.append(self.run(site, producers, session, queue, site_settings, cancellable_pool))
        await asyncio.gather(*tasks)

    def add_producer_exception_handler(self, coroutine, node):
        async def wrapper(*args, **kwargs):
            try:
                await coroutine(*args, **kwargs)

            except asyncio.CancelledError as e:
                raise e

            except LoginError as e:
                if global_settings.loglevel == "DEBUG":
                    traceback.print_exc()
                error_msg = f"{node} login was not successful. Error: {e}."
                logger.error(error_msg)
                self.signal_handler.quit_with_error(node.unique_key, error_msg)
            except Exception as e:
                if global_settings.loglevel == "DEBUG":
                    traceback.print_exc()
                error_msg = f"Got error while trying to fetch the folder name. Error: {e}."
                logger.error(error_msg)
                self.signal_handler.quit_with_error(node.unique_key, error_msg)

        return wrapper
