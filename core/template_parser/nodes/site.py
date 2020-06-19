import importlib
import inspect
import traceback
import re
import os
import time
import logging
import asyncio

from PyQt5.QtGui import *

from core.storage import cache
from core.exceptions import ParseTemplateError, ParseTemplateRuntimeError
from core.template_parser.nodes.base import TemplateNode
from core.template_parser.queue_wrapper import QueueWrapper
from core.template_parser.utils import get_module_function, check_if_null, dict_to_string, login_module
from core.utils import safe_path_join
from gui.constants import SITE_ICON_PATH
from settings import settings

logger = logging.getLogger(__name__)


class Site(TemplateNode):
    def __init__(self,
                 raw_module_name,
                 use_folder,
                 raw_folder_name,
                 raw_function,
                 raw_folder_function,
                 function_kwargs,
                 consumer_kwargs,
                 parent):
        super().__init__(parent=parent,
                         folder_name=raw_folder_name,
                         unique_key_args=[
                             raw_module_name,
                             function_kwargs,
                             raw_folder_name,
                             use_folder,
                             raw_function,
                             raw_folder_function,
                             function_kwargs,
                         ],
                         use_folder=use_folder)
        self.raw_module_name = raw_module_name
        self.function_kwargs = function_kwargs
        self.consumer_kwargs = consumer_kwargs
        self.raw_folder_name = raw_folder_name
        self.raw_function = raw_function
        self.raw_folder_function = raw_folder_function

        self.folder_function_name = None
        self.folder_module_name = None
        self.function_name = None
        self.module_name = None
        self.folder_name = None

        self.init()

    def _init_parent(self):
        return self.parent.add_site(self)

    def init(self):
        folder_name = self.raw_folder_name
        if self.raw_folder_name is None:
            folder_name_cache = cache.get_json("folder_name")
            folder_name = folder_name_cache.get(self.unique_key, None)

        if self.raw_module_name != "custom":
            module_name = self.raw_module_name
            folder_module_name = self.raw_module_name
            function_name = "producer"
            folder_function_name = "get_folder_name"
        else:
            if self.raw_function is None:
                raise ParseTemplateError(f"Expected a 'function' field with custom")
            module_name, function_name = get_module_function(self.raw_function)
            if self.raw_folder_name is None and self.use_folder:
                if self.raw_folder_function is None:
                    raise ParseTemplateError(f"Expected a 'folder_function' or 'folder_name' field with custom")
                folder_module_name, folder_function_name = get_module_function(self.raw_folder_function)
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

        self.folder_function_name = folder_function_name
        self.folder_module_name = folder_module_name
        self.function_name = function_name
        self.module_name = module_name
        self.folder_name = folder_name

    def __str__(self):
        return self.module_name

    def get_gui_name(self):
        if self.folder_name is not None:
            return self.folder_name
        return self.raw_module_name

    def get_gui_icon(self):
        image_files = os.listdir(SITE_ICON_PATH)
        file_name = None
        for image_file in image_files:
            if self.raw_module_name in image_file:
                file_name = image_file
                break
        if file_name is None:
            return super(Site, self).get_gui_icon()

        path = os.path.join(SITE_ICON_PATH, file_name)
        return QIcon(path)

    def gui_options(self):
        result = [("module", self.raw_module_name)]
        if self.raw_module_name == "custom":
            result.append(("function", self.raw_function))
        result.append(("use_folder", self.use_folder))
        if self.use_folder:
            if self.raw_module_name == "custom" and self.raw_folder_function is not None:
                result.append(("folder_function", self.raw_folder_function))
            else:
                result.append(("folder_name", self.raw_folder_name))

        site_module = importlib.import_module(self.module_name)
        producer_function = getattr(site_module, self.function_name)

        for name, parameter in inspect.signature(producer_function).parameters.items():
            if name in ["session", "queue", "base_path"]:
                continue
            if name in self.function_kwargs:
                result.append((name, self.function_kwargs[name]))
                continue

            result.append((name, parameter.default if parameter.default is not parameter.empty else None))

        for key, value in self.consumer_kwargs.items():
            result.append((key, value))

        return result

    async def add_producers(self, producers, session, queue, signal_handler):
        signal_handler.start(self.unique_key)

        if check_if_null(self.function_kwargs):
            raise ParseTemplateRuntimeError("Found null field")

        site_module = importlib.import_module(self.module_name)
        producer_function = getattr(site_module, self.function_name)

        await login_module(session, site_module)

        if self.base_path is None:
            folder_name = await self.get_folder_name(session, signal_handler)

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

        folder_name_cache = cache.get_json("folder_name")
        folder_name_cache[self.unique_key] = folder_name

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
