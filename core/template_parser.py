import asyncio
import hashlib
import importlib
import inspect
import logging
import os
import re
import time
import traceback

import yaml

from ordered_set import OrderedSet
from core.exceptions import ParseTemplateError, LoginError, ParseTemplateRuntimeError
from core.storage import cache
from core.utils import safe_path_join
from settings import settings

logger = logging.getLogger(__name__)

locks = {}


async def login_module(session, module):
    if not hasattr(module, "login"):
        return

    func = module.login
    if not callable(func):
        return

    lock_name = module.__name__ + str(id(session))

    if lock_name in locks:
        lock = locks[lock_name]
    else:
        lock = asyncio.Lock()
        locks[lock_name] = lock

    async with lock:
        if not hasattr(func, "errors"):
            func.errors = {}
        if id(session) not in func.errors:
            logger.debug(f"Logging into {module.__name__}")
            start_time = time.time()
            try:
                await func(session=session)
                logger.debug(f"Logged into {module.__name__}, time: {(time.time() - start_time):.2f}")
                func.errors[id(session)] = False
            except LoginError as e:
                func.errors[id(session)] = True
                raise e
        if func.errors[id(session)]:
            raise LoginError("Previous login was not successful")


def get_module_function(name):
    mf_name = ("custom." + name).split(".")
    module_name = ".".join(mf_name[:-1])
    function_name = mf_name[-1]
    return module_name, function_name


def check_if_null(p_kwargs):
    for key, value in p_kwargs.items():
        if value is None:
            return True
    return False


def dict_to_string(d):
    result = ""
    for key, value in d.items():
        result += str(key) + "=" + str(value) + " "
    if d:
        result = result[:-1]
    return result


def ignore_if_signal_is_none(function):
    def wrapper(self, *args, **kwargs):
        if self.signals is None:
            return
        result = function(self, *args, **kwargs)
        return result

    return wrapper


class SignalHandler(object):
    def __init__(self, signals=None):
        self.signals = signals

    @ignore_if_signal_is_none
    def start(self, unique_key, msg=None):
        if msg is None:
            self.signals.site_started[str].emit(unique_key)
        else:
            self.signals.site_started[str, str].emit(unique_key, msg)

    @ignore_if_signal_is_none
    def finished_successful(self, unique_key, msg=None):
        if msg is None:
            self.signals.site_finished_successful[str].emit(unique_key)
        else:
            self.signals.site_finished_successful[str, str].emit(unique_key, msg)

    @ignore_if_signal_is_none
    def quit_with_warning(self, unique_key, msg=None):
        if msg is None:
            self.signals.site_quit_with_warning[str].emit(unique_key)
        else:
            self.signals.site_quit_with_warning[str, str].emit(unique_key, msg)

    @ignore_if_signal_is_none
    def quit_with_error(self, unique_key, msg=None):
        if msg is None:
            self.signals.site_quit_with_error[str].emit(unique_key)
        else:
            self.signals.site_quit_with_error[str, str].emit(unique_key, msg)

    @ignore_if_signal_is_none
    def update_folder_name(self, unique_key, new_folder_name):
        self.signals.update_folder_name[str, str].emit(unique_key, new_folder_name)

    @ignore_if_signal_is_none
    def update_base_path(self, unique_key, new_base_path):
        self.signals.update_base_path[str, str].emit(unique_key, new_base_path)


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


class TemplateNode(object):
    def __init__(self, unique_key, parent=None, base_path=None):
        self.unique_key = unique_key
        self.parent = parent
        self.base_path = base_path
        self.folder = None
        self.sites = OrderedSet([])
        if self.parent is not None:
            if isinstance(self, Folder):
                self.parent.add_folder(self)
            elif isinstance(self, Site):
                self.parent.add_site(self)

    def __str__(self):
        return self.unique_key

    def add_site(self, child):
        if child.parent is None:
            raise ValueError("Child already has a parent")
        self.sites.add(child)
        child.parent = self

    def add_folder(self, folder):
        if folder.parent is None:
            raise ValueError("Child already has a parent")
        self.folder = folder
        folder.parent = self

    def gui_name(self):
        return str(self)

    async def add_producers(self, producers, session, queue, signal_handler):
        pass


class Folder(TemplateNode):
    def __init__(self, name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name

    def __str__(self):
        return self.name


class Site(TemplateNode):
    def __init__(self,
                 site_name,
                 module_name,
                 function_name,
                 folder_module_name,
                 folder_function_name,
                 folder_name,
                 use_folder,
                 function_kwargs,
                 consumer_kwargs,
                 *args,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.function_kwargs = function_kwargs
        self.folder_function_name = folder_function_name
        self.folder_module_name = folder_module_name
        self.function_name = function_name
        self.module_name = module_name
        self.consumer_kwargs = consumer_kwargs
        self.use_folder = use_folder
        self.folder_name = folder_name
        self.site_name = site_name

    def __str__(self):
        return self.module_name

    def gui_name(self):
        if self.folder_name is not None:
            return self.folder_name
        return self.site_name

    async def add_producers(self, producers, session, queue, signal_handler):
        signal_handler.start(self.unique_key)

        if check_if_null(self.function_kwargs):
            raise ParseTemplateRuntimeError("Found null field")

        producer_module = importlib.import_module(self.module_name)
        producer_function = getattr(producer_module, self.function_name)

        await login_module(session, producer_module)

        if self.base_path is None:
            folder_name = await self.get_folder_name(session, signal_handler)
            folder_name_cache = cache.get_json("folder_name")
            folder_name_cache[self.unique_key] = folder_name

            self.base_path = safe_path_join(self.parent.base_path, folder_name)
            signal_handler.update_base_path(self.unique_key, self.base_path)

        queue_wrapper = QueueWrapper(queue,
                                     signal_handler=signal_handler,
                                     unique_key=self.unique_key,
                                     **self.consumer_kwargs)

        coroutine = self.exception_handler(producer_function, signal_handler)(session=session,
                                                                              queue=queue_wrapper,
                                                                              base_path=self.base_path,
                                                                              **self.function_kwargs)
        producers.append(asyncio.ensure_future(coroutine))

    async def get_folder_name(self, session, signal_handler):
        if self.folder_name is not None or self.folder_module_name is None:
            return self.folder_name

        folder_module = importlib.import_module(self.folder_module_name)
        function = getattr(folder_module, self.folder_function_name)
        logger.debug(f"Calling folder function: {function.__module__}."
                     f"{function.__name__}<{dict_to_string(self.function_kwargs)}>")
        folder_name = await function(session=session, **self.function_kwargs)
        signal_handler.update_folder_name(self.unique_key, folder_name)
        return folder_name

    def exception_handler(self, function, signal_handler):
        async def wrapper(session, queue, base_path, *args, **kwargs):
            function_name = f"{function.__module__}.{function.__name__}"
            function_name_kwargs = f"{function_name}<{dict_to_string(kwargs)}>"
            try:
                logger.debug(f"Starting: {function_name_kwargs}")
                t = time.time()
                result = await function(session=session, queue=queue, base_path=base_path, *args, **kwargs)
                signal_handler.finished_successful(self.unique_key, f"Finished in {(time.time() - t):.2f} seconds")
                logger.debug(f"Finished: {function_name_kwargs}, time: {(time.time() - t):.2f}")
                return result
            except asyncio.CancelledError as e:
                raise e
            except TypeError as e:
                if settings.loglevel == "DEBUG":
                    traceback.print_exc()
                keyword = re.findall("'(.+)'", e.args[0])
                logger.error(f"The producer {function_name_kwargs} got an unexpected keyword: {keyword}."
                             f" Stopping the producer..")
                signal_handler.quit_with_error(self.unique_key, f"Unexpected keyword: {keyword}.")
                return
            except Exception as e:
                if settings.loglevel == "DEBUG":
                    traceback.print_exc()
                logger.error(
                    f"Got an unexpected error from producer: {function_name_kwargs}, Error: {type(e).__name__}: {e}")
                signal_handler.quit_with_error(self.unique_key, f"Error: {type(e).__name__}: {e}")
                return

        return wrapper


class Template(object):
    def __init__(self, path, signals=None):
        self.path = path
        self.signal_handler = SignalHandler(signals=signals)
        self.root = TemplateNode(unique_key="root", base_path="")
        self.data = None
        self.nodes = {node.unique_key: node for node in iter(self)}

    def __iter__(self):
        def gen(node):
            yield node
            if node.folder is not None:
                yield from gen(node.folder)
            for site in node.sites:
                yield from gen(site)

        return gen(self.root)

    def load(self):
        self.data = self.load_data(self.path)
        self.parse_template()

        self.nodes = {node.unique_key: node for node in iter(self)}

    def load_data(self, path):
        with open(path) as f:
            data = yaml.load(f, Loader=yaml.Loader)

        md5 = hashlib.md5(str(data).encode('utf-8')).hexdigest()
        folder_name_cache = self.get_folder_name_cache(md5)

        self.prepare_data(data, folder_name_cache)
        return data

    @staticmethod
    def get_folder_name_cache(md5):
        folder_name_cache = cache.get_json("folder_name")

        if "md5" not in folder_name_cache or folder_name_cache["md5"] != md5:
            new_folder_name = {"md5": md5}
            cache.set_json("folder_name", new_folder_name)
            return new_folder_name

        return folder_name_cache

    def prepare_data(self, data, folder_name_cache, unique_key="-"):
        if isinstance(data, dict):
            for key, item in data.items():
                self.prepare_data(item, folder_name_cache, unique_key + key)
            data["unique_key"] = unique_key
            if unique_key in folder_name_cache:
                data["cached_folder_name"] = folder_name_cache[unique_key]

        elif isinstance(data, list):
            for i, item in enumerate(data):
                self.prepare_data(item, folder_name_cache, unique_key + str(i))

    def parse_template(self):
        if "folder" in self.data:
            self.parse_folder(data=self.data["folder"], parent=self.root)
        if "sites" in self.data:
            self.parse_sites(data=self.data["sites"], parent=self.root)

    def parse_folder(self, data, parent):
        if "name" not in data:
            raise ParseTemplateError("Expected a 'name' field in folder")

        if "sites" not in data:
            raise ParseTemplateError("Expected a 'sites' field in folder")

        base_path = None
        if parent.base_path is not None:
            base_path = safe_path_join(parent.base_path, data["name"])

        folder = Folder(name=data["name"],
                        unique_key=data["unique_key"],
                        parent=parent,
                        base_path=base_path)

        self.parse_sites(data=data["sites"], parent=folder)

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
        site_name = p_kwargs.pop("module")

        sub_sites = p_kwargs.pop("sites", None)
        folder = p_kwargs.pop("folder", None)

        unique_key = p_kwargs.pop("unique_key", None)
        cached_folder_name = p_kwargs.pop("cached_folder_name", None)
        folder_name = p_kwargs.pop("folder_name", None)
        use_folder = p_kwargs.pop("use_folder", True)
        possible_consumer_kwargs = ["allowed_extensions", "forbidden_extensions"]
        consumer_kwargs = {name: p_kwargs.pop(name, None) for name in possible_consumer_kwargs}
        consumer_kwargs = {name: value for name, value in consumer_kwargs.items() if value is not None}

        if folder_name is None and cached_folder_name is not None:
            folder_name = cached_folder_name

        if site_name != "custom":
            module_name = site_name
            folder_module_name = site_name
            function_name = "producer"
            folder_function_name = "get_folder_name"
        else:
            if "function" not in p_kwargs:
                raise ParseTemplateError(f"Expected a 'function' field with custom")
            module_name, function_name = get_module_function(p_kwargs.pop("function"))
            if folder_name is None and use_folder:
                if "function" not in p_kwargs:
                    raise ParseTemplateError(f"Expected a 'folder_function' or 'folder_name' field with custom")
                folder_module_name, folder_function_name = get_module_function(p_kwargs.pop("folder_function"))
            else:
                folder_module_name, folder_function_name = None, None

        module_name = "sites." + module_name
        if folder_module_name is not None:
            folder_module_name = "sites." + folder_module_name

        try:
            site_module = importlib.import_module(module_name)
        except ModuleNotFoundError:
            raise ParseTemplateError(f"Site module with name: {module_name} does not exist")
        if not hasattr(site_module, function_name):
            raise ParseTemplateError(f"Function: {function_name} in module: {module_name} does not exist")

        if folder_module_name is not None:
            try:
                folder_module = importlib.import_module(folder_module_name)
            except ModuleNotFoundError:
                raise ParseTemplateError(f"Folder module with name: {folder_module_name} does not exist")
            if not hasattr(folder_module, folder_function_name):
                raise ParseTemplateError(f"Function: {folder_function_name} in module: {folder_module} does not exist")

        base_path = None
        if parent.base_path is not None:
            if not use_folder:
                base_path = parent.base_path
            elif folder_name is not None:
                base_path = safe_path_join(parent.base_path, folder_name)

        site = Site(
            site_name=site_name,
            module_name=module_name,
            function_name=function_name,
            folder_module_name=folder_module_name,
            folder_function_name=folder_function_name,
            unique_key=unique_key,
            folder_name=folder_name,
            use_folder=use_folder,
            function_kwargs=p_kwargs,
            base_path=base_path,
            consumer_kwargs=consumer_kwargs,
            parent=parent,
        )

        if sub_sites is not None:
            self.parse_sites(data=sub_sites, parent=site)
        if folder is not None:
            self.parse_folder(data=folder, parent=site)

    async def run_root(self, producers, session, queue):
        await self.run(self.root, producers=producers, session=session, queue=queue)

    async def run_from_unique_key(self, unique_key, producers, session, queue, recursive):
        await self.run(self.nodes[unique_key], producers=producers, session=session, queue=queue, recursive=recursive)

    async def run(self, node, producers, session, queue, recursive=True):
        tasks = []

        coroutine = self.add_producer_exception_handler(node.add_producers, node)(producers,
                                                                                  session,
                                                                                  queue,
                                                                                  self.signal_handler)
        if node.base_path is None:
            await coroutine
        else:
            tasks.append(asyncio.ensure_future(coroutine))

        if recursive and node.base_path is not None:
            if node.folder is not None:
                tasks.append(self.run(node.folder, producers, session, queue))
            for site in node.sites:
                tasks.append(self.run(site, producers, session, queue))
        await asyncio.gather(*tasks)

    def add_producer_exception_handler(self, coroutine, node):
        async def wrapper(*args, **kwargs):
            try:
                await coroutine(*args, **kwargs)

            except asyncio.CancelledError as e:
                raise e

            except LoginError as e:
                if settings.loglevel == "DEBUG":
                    traceback.print_exc()
                error_msg = f"{node} login was not successful. Error: {e}."
                logger.error(error_msg)
                self.signal_handler.quit_with_error(node.unique_key, error_msg)
            except Exception as e:
                if settings.loglevel == "DEBUG":
                    traceback.print_exc()
                error_msg = f"Got error while trying to fetch the folder name. Error: {e}."
                logger.error(error_msg)
                self.signal_handler.quit_with_error(node.unique_key, error_msg)

        return wrapper
