import asyncio
import logging

import yaml

from core.exceptions import ParseTemplateError, LoginError
from core.template_parser.constants import POSSIBLE_CONSUMER_KWARGS
from core.template_parser.nodes import Root, Folder, Site
from core.template_parser.signal_handler import SignalHandler

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
            for child_node in node.children:
                yield from gen(child_node)

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
            return yaml.load(f, Loader=yaml.Loader)

    def save_template(self):
        data = self.root.convert_to_dict()
        try:
            with open(self.path, "w+") as f:
                yaml.dump(data=data, stream=f, Dumper=yaml.Dumper, default_flow_style=False, sort_keys=False)
        except PermissionError:
            logger.warning(f"Could not save file: {self.path}. Permission Error")

    def convert_to_dict(self):
        return self.root.convert_to_dict()

    def parse_template(self):
        if "children" in self.data:
            self.parse_children(data=self.data["children"], parent=self.root)

    def parse_children(self, data, parent):
        for node_dict in data:
            if "module" in node_dict and "folder" in node_dict:
                raise ParseTemplateError("Got module and folder node")

            children = node_dict.pop("children", None)

            if "module" in node_dict:
                child_node = self.parse_site(p_kwargs=node_dict, parent=parent)

            elif "folder" in node_dict:
                child_node = self.parse_folder(data=node_dict, parent=parent)
            else:
                raise ParseTemplateError("'module' or 'folder' field required")

            if children is not None:
                self.parse_children(children, child_node)

    def parse_folder(self, data, parent):
        name = data["folder"]

        meta_data = data.pop("meta_data", None)

        folder = Folder(name=name,
                        meta_data=meta_data,
                        parent=parent)

        return folder

    def parse_site(self, p_kwargs, parent):
        raw_module_name = p_kwargs.pop("module")

        raw_folder_name = p_kwargs.pop("folder_name", None)
        use_folder = p_kwargs.pop("use_folder", True)
        consumer_kwargs = {name: p_kwargs.pop(name, None) for name in POSSIBLE_CONSUMER_KWARGS}

        raw_function = p_kwargs.pop("function", None)
        raw_folder_function = p_kwargs.pop("folder_function", None)
        raw_login_function = p_kwargs.pop("login_function", None)

        meta_data = p_kwargs.pop("meta_data", None)

        site = Site(
            raw_module_name=raw_module_name,
            use_folder=use_folder,
            raw_folder_name=raw_folder_name,
            raw_function=raw_function,
            raw_folder_function=raw_folder_function,
            raw_login_function=raw_login_function,
            function_kwargs=p_kwargs,
            consumer_kwargs=consumer_kwargs,
            meta_data=meta_data,
            parent=parent
        )

        return site

    async def run_root(self, producers, session, queue, site_settings, cancellable_pool):
        await self.run(self.root,
                       producers=producers,
                       session=session,
                       queue=queue,
                       site_settings=site_settings,
                       cancellable_pool=cancellable_pool)

    async def run_from_unique_keys(self, unique_keys, producers, session, queue,
                                   site_settings, cancellable_pool, recursive):
        tasks = []
        for unique_key in unique_keys:
            coroutine = self.run(node=self.nodes[unique_key],
                                 producers=producers,
                                 session=session,
                                 queue=queue,
                                 site_settings=site_settings,
                                 cancellable_pool=cancellable_pool,
                                 recursive=recursive)
            tasks.append(coroutine)

        await asyncio.gather(*tasks)

    async def run(self, node, producers, session, queue, site_settings, cancellable_pool, recursive=True):
        if node.unique_key != "root":
            self.signal_handler.start(node.unique_key)  # finished signal in add_producer_exception_handler

        if node.parent is not None and node.parent.base_path is None:
            self.signal_handler.got_error(node.unique_key, "Parent needs to run first")
            return

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
            for child in node.children:
                tasks.append(self.run(child, producers, session, queue, site_settings, cancellable_pool))
        await asyncio.gather(*tasks)

    def add_producer_exception_handler(self, coroutine, node):
        async def wrapper(*args, **kwargs):
            try:
                await coroutine(*args, **kwargs)

            except asyncio.CancelledError as e:
                raise e

            except LoginError as e:
                error_msg = f"{node} login was not successful. {e.__class__.__name__}: {e}."
                logger.error(error_msg, exc_info=True)
                self.signal_handler.got_error(node.unique_key, error_msg)
            except Exception as e:
                error_msg = f"Got error while trying to fetch the folder name. {e.__class__.__name__}: {e}."
                logger.error(error_msg, exc_info=True)
                self.signal_handler.got_error(node.unique_key, error_msg)
            finally:
                if node.unique_key != "root":
                    self.signal_handler.finished(node.unique_key)

        return wrapper
