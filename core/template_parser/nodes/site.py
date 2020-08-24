import asyncio
import importlib
import inspect
import logging
import os
import re
import time
import traceback

from PyQt5.QtGui import *

from core.exceptions import ParseTemplateError, ParseTemplateRuntimeError
from core.storage import cache
from core.template_parser.nodes import site_configs
from core.template_parser.nodes.base import TemplateNode
from core.template_parser.queue_wrapper import QueueWrapper
from core.template_parser.utils import get_module_function, check_if_null, dict_to_string, login_module
from core.utils import safe_path_join
from gui.constants import SITE_ICON_PATH
from settings import global_settings

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
                 parent,
                 **kwargs):
        super().__init__(parent=parent,
                         folder_name=raw_folder_name,
                         unique_key_kwargs=self.get_unique_key_kwargs(
                             raw_module_name=raw_module_name,
                             raw_folder_name=raw_folder_name,
                             use_folder=use_folder,
                             raw_function=raw_function,
                             raw_folder_function=raw_folder_function,
                             function_kwargs=function_kwargs,
                         ),
                         use_folder=use_folder,
                         is_producer=True,
                         **kwargs)
        self.raw_module_name = raw_module_name
        self.function_kwargs = function_kwargs
        self.consumer_kwargs = consumer_kwargs
        self.raw_folder_name = raw_folder_name
        self.raw_function = raw_function
        self.raw_folder_function = raw_folder_function

        self.folder_module_name, self.folder_function_name = self.get_folder_module_func_name(raw_module_name,
                                                                                              raw_folder_function,
                                                                                              raw_folder_name,
                                                                                              use_folder)
        self.module_name, self.function_name = self.get_module_func_name(raw_module_name,
                                                                         raw_function)

    @staticmethod
    def get_unique_key_kwargs(**kwargs):
        return dict(
            raw_module_name=kwargs.get("raw_module_name"),
            raw_folder_name=kwargs.get("raw_folder_name"),
            use_folder=kwargs.get("use_folder"),
            raw_function=kwargs.get("raw_function"),
            raw_folder_function=kwargs.get("raw_folder_function"),
            function_kwargs=kwargs.get("function_kwargs"),
        )

    @staticmethod
    def get_module_func_name(raw_module_name, raw_function):
        if raw_module_name != "custom":
            module_name = raw_module_name
            function_name = "producer"
        else:
            if raw_function is None:
                raise ParseTemplateError(f"Expected a 'function' field with custom")
            module_name, function_name = get_module_function(raw_function)

        module_name = "sites." + module_name

        try:
            site_module = importlib.import_module(module_name)
        except ModuleNotFoundError:
            raise ParseTemplateError(f"Site module with name: {module_name} does not exist")
        if not hasattr(site_module, function_name):
            raise ParseTemplateError(f"Function: {function_name} in module: {module_name} does not exist")

        return module_name, function_name

    @staticmethod
    def get_folder_module_func_name(raw_module_name, raw_folder_function, raw_folder_name, use_folder):
        if raw_module_name != "custom":
            folder_module_name = raw_module_name
            folder_function_name = "get_folder_name"
        else:
            folder_module_name, folder_function_name = None, None
            if raw_folder_name is None and use_folder:
                if raw_folder_function is None:
                    raise ParseTemplateError(f"Expected a 'folder_function' or 'folder_name' field with custom")
                folder_module_name, folder_function_name = get_module_function(raw_folder_function)

        if folder_module_name is not None:
            folder_module_name = "sites." + folder_module_name
            try:
                folder_module = importlib.import_module(folder_module_name)
            except ModuleNotFoundError:
                raise ParseTemplateError(f"Folder module with name: {folder_module_name} does not exist")
            if not hasattr(folder_module, folder_function_name):
                raise ParseTemplateError(f"Function: {folder_function_name} in module:"
                                         f" {folder_module_name} does not exist")

        return folder_module_name, folder_function_name

    def __str__(self):
        return self.module_name

    def convert_to_dict(self, result=None):
        attributes = {
            "module": self.raw_module_name,
            "use_folder": self.use_folder,
            "folder_name": self.raw_folder_name,
            "function": self.raw_function,
            "folder_function": self.raw_folder_function,
            **self.function_kwargs,
            **self.consumer_kwargs,
        }
        result = {}
        for key, value in attributes.items():
            if value is not None:
                result[key] = value
        return super().convert_to_dict(result=result)

    def get_gui_name(self):
        if self.folder_name is not None:
            return self.folder_name
        return self.raw_module_name

    def get_type_name(self):
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

    def get_configs(self):
        configs = site_configs.SiteConfigs()
        attributes = [
            "raw_module_name",
            "use_folder",
            "raw_folder_name",
            "raw_function",
            "raw_folder_function",
            "consumer_kwargs",
            "function_kwargs",
        ]
        for attribute in attributes:
            try:
                setattr(configs, attribute, getattr(self, attribute))
            except ValueError as e:
                logger.debug(f"Tried to set wrong value {attribute}. Error: {str(e)}")

        return configs

    async def add_producers(self, producers, session, queue, site_settings, cancellable_pool, signal_handler):
        if check_if_null(self.function_kwargs):
            raise ParseTemplateRuntimeError("Found null field")

        site_module = importlib.import_module(self.module_name)
        producer_function = getattr(site_module, self.function_name)

        await login_module(session, site_settings, site_module)

        if self.base_path is None:
            self.folder_name = await self.retrieve_folder_name(session, signal_handler)

            self.base_path = safe_path_join(self.parent.base_path, self.folder_name)
            signal_handler.update_base_path(self.unique_key, self.base_path)

        queue_wrapper = QueueWrapper(queue,
                                     signal_handler=signal_handler,
                                     unique_key=self.unique_key,
                                     site_settings=site_settings,
                                     cancellable_pool=cancellable_pool,
                                     **self.consumer_kwargs)

        coroutine = self.exception_handler(producer_function, signal_handler)(session=session,
                                                                              queue=queue_wrapper,
                                                                              base_path=self.base_path,
                                                                              site_settings=site_settings,
                                                                              **self.function_kwargs)
        producers.append(asyncio.ensure_future(coroutine))

    async def retrieve_folder_name(self, session, signal_handler):
        if self.folder_name is not None or self.folder_module_name is None:
            return self.folder_name

        folder_module = importlib.import_module(self.folder_module_name)
        function = getattr(folder_module, self.folder_function_name)
        logger.debug(f"Calling folder function: {function.__module__}."
                     f"{function.__name__}<{dict_to_string(self.function_kwargs)}>")
        folder_name = await function(session=session, **self.function_kwargs)

        folder_name_cache = cache.get_json("folder_name")
        folder_name_cache[self.kwargs_hash] = folder_name

        signal_handler.update_folder_name(self.unique_key, folder_name)
        return folder_name

    def exception_handler(self, function, signal_handler):
        unique_key = self.unique_key

        async def wrapper(session, queue, base_path, site_settings, *args, **kwargs):
            function_name = f"{function.__module__}.{function.__name__}"
            function_name_kwargs = f"{function_name}<{dict_to_string(kwargs)}>"
            try:
                logger.debug(f"Starting: {function_name_kwargs}")
                signal_handler.start(unique_key)
                t = time.time()
                result = await function(session=session, queue=queue, base_path=base_path,
                                        site_settings=site_settings, *args, **kwargs)
                logger.debug(f"Finished: {function_name_kwargs}, time: {(time.time() - t):.2f}")
                return result
            except asyncio.CancelledError as e:
                raise e
            except TypeError as e:
                if global_settings.loglevel == "DEBUG":
                    traceback.print_exc()
                keyword = re.findall("'(.+)'", e.args[0])
                logger.error(f"The producer {function_name_kwargs} got an unexpected keyword: {keyword}."
                             f" Stopping the producer..")
                signal_handler.got_error(unique_key, f"Unexpected keyword: {keyword}.")
                return
            except Exception as e:
                if global_settings.loglevel == "DEBUG":
                    traceback.print_exc()
                logger.error(
                    f"Got an unexpected error from producer: {function_name_kwargs}, Error: {type(e).__name__}: {e}")
                signal_handler.got_error(self.unique_key, f"Error: {type(e).__name__}: {e}")
                return
            finally:
                signal_handler.finished(unique_key)

        return wrapper
