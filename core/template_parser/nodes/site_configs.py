import importlib
import inspect
import logging
import os
import copy

from PyQt5.QtGui import *

from core.constants import ROOT_PATH
from core.exceptions import ParseTemplateError
from core.template_parser import nodes
from core.template_parser.nodes.base import NodeConfigs
from core.template_parser.nodes.utils import get_folder_name_from_kwargs
from gui.constants import SITE_ICON_PATH
from settings.config_objs import ConfigString, ConfigBool, ConfigOptions, ConfigDict, ConfigListString
from sites.constants import POSSIBLE_LOGIN_FUNCTIONS

logger = logging.getLogger(__name__)


class FunctionKwargsConfigDict(ConfigDict):
    def __init__(self, *args, **kwargs):
        super().__init__(layout={}, *args, **kwargs)
        self.current_module = None
        self.current_function = None
        self.widget_layouts = {}
        self.layouts = {}

    def set(self, value):
        raw_module_name = self.instance["raw_module_name"].get()
        raw_function = self.instance["raw_function"].get()
        self.change_layout(raw_module_name, raw_function)
        super().set(value)

    def cancel(self):
        raw_module_name = self.instance["raw_module_name"].get()
        raw_function = self.instance["raw_function"].get()
        self.change_layout(raw_module_name, raw_function)

    def change_layout(self, current_module, current_function):
        key = str(current_module) + (str(current_function) if current_module == "custom" else "")
        if key in self.layouts:
            if self.layouts[key] is self.layout:
                return
        else:
            layout = self.create_layout(current_module, current_function)
            self.layouts[key] = layout

        self.layout = self.layouts[key]

        if self.widget is not None:
            self.widget.config_widget.clear()
            self.widget.config_widget.init()

    @staticmethod
    def create_layout(raw_module_name, raw_function):
        result = {}

        if raw_module_name is None:
            return {}

        try:
            module_name, function_name = nodes.Site.get_module_func_name(raw_module_name,
                                                                         raw_function)
        except ParseTemplateError:
            return {}

        site_module = importlib.import_module(module_name)
        producer_function = getattr(site_module, function_name)

        try:
            for name, parameter in inspect.signature(producer_function).parameters.items():
                if name in ["session", "queue", "base_path", "site_settings"]:
                    continue
                default_value = parameter.default if parameter.default is not parameter.empty else None
                optional = parameter.default != parameter.empty

                if isinstance(parameter.annotation, ConfigString):
                    config_obj = copy.deepcopy(parameter.annotation)
                elif parameter.annotation is bool or isinstance(default_value, bool):
                    config_obj = ConfigBool(default=default_value, optional=optional)
                elif parameter.annotation is list or isinstance(default_value, list):
                    config_obj = ConfigListString(default=default_value, optional=optional)
                else:
                    config_obj = ConfigString(default=default_value, optional=optional)
                result[name] = config_obj
        except TypeError:
            return {}

        return result

    def reset_widget(self):
        raw_module_name = self.instance["raw_module_name"].get()
        raw_function = self.instance["raw_function"].get()
        self.change_layout(raw_module_name, raw_function)
        super().reset_widget()

    def update_widget(self):
        raw_module_name = self.instance["raw_module_name"].get_from_widget()
        raw_function = self.instance["raw_function"].get_from_widget()
        self.change_layout(raw_module_name, raw_function)
        super().update_widget()


class FunctionConfigString(ConfigString):
    def _test(self, value, from_widget):
        if from_widget:
            raw_module_name = self.instance["raw_module_name"].get_from_widget()
        else:
            raw_module_name = self.instance["raw_module_name"].get()

        try:
            nodes.Site.get_module_func_name(raw_module_name, value)
        except ParseTemplateError as e:
            raise ValueError(str(e))


class FunctionFolderConfigString(ConfigString):
    def _test(self, value, from_widget):
        if from_widget:
            raw_module_name = self.instance["raw_module_name"].get_from_widget()
            raw_folder_function = self.instance["raw_folder_function"].get_from_widget()
            raw_folder_name = self.instance["raw_folder_name"].get_from_widget()
            use_folder = self.instance["use_folder"].get_from_widget()
        else:
            raw_module_name = self.instance["raw_module_name"].get()
            raw_folder_function = self.instance["raw_folder_function"].get()
            raw_folder_name = self.instance["raw_folder_name"].get()
            use_folder = self.instance["use_folder"].get()

        try:
            nodes.Site.get_folder_module_func_name(raw_module_name,
                                                   raw_folder_function,
                                                   raw_folder_name,
                                                   use_folder)
        except ParseTemplateError as e:
            raise ValueError(str(e))


class FunctionLoginConfigString(ConfigString):
    def _test(self, value, from_widget):
        if from_widget:
            raw_login_function = self.instance["raw_login_function"].get_from_widget()
            raw_module_name = self.instance["raw_module_name"].get_from_widget()
        else:
            raw_login_function = self.instance["raw_login_function"].get()
            raw_module_name = self.instance["raw_module_name"].get()

        try:
            nodes.Site.get_login_func_name(raw_module_name, raw_login_function)
        except ParseTemplateError as e:
            raise ValueError(str(e))


def raw_folder_name_active(instance: NodeConfigs, from_widget, parent):
    if from_widget:
        use_folder = instance.get_config_obj("use_folder").get_from_widget()
        folder_function = instance.get_config_obj("raw_folder_function").get_from_widget()
        raw_module_name = instance.get_config_obj("raw_module_name").get_from_widget()
    else:
        use_folder = instance.get_config_obj("use_folder").get()
        folder_function = instance.get_config_obj("raw_folder_function").get()
        raw_module_name = instance.get_config_obj("raw_module_name").get()

    return use_folder and (folder_function is None or raw_module_name != "custom")


def raw_function_active(instance, from_widget, parent):
    if from_widget:
        raw_module_name = instance.get_config_obj("raw_module_name").get_from_widget()
    else:
        raw_module_name = instance.get_config_obj("raw_module_name").get()

    return raw_module_name == "custom"


def folder_function_active(instance, from_widget, parent):
    if from_widget:
        raw_module_name = instance.get_config_obj("raw_module_name").get_from_widget()
        use_folder = instance.get_config_obj("use_folder").get_from_widget()
        raw_folder_name = instance.get_config_obj("raw_folder_name").get_from_widget()
    else:
        raw_module_name = instance.get_config_obj("raw_module_name").get()
        use_folder = instance.get_config_obj("use_folder").get()
        raw_folder_name = instance.get_config_obj("raw_folder_name").get()

    return raw_module_name == "custom" and use_folder and raw_folder_name is None


def raw_login_function_active(instance, from_widget, parent):
    if from_widget:
        raw_module_name = instance.get_config_obj("raw_module_name").get_from_widget()
    else:
        raw_module_name = instance.get_config_obj("raw_module_name").get()

    return raw_module_name in POSSIBLE_LOGIN_FUNCTIONS


def get_module_names():
    sites_path = os.path.join(ROOT_PATH, "sites")
    result = []
    for file_name in os.listdir(sites_path):
        if "." in file_name:
            continue

        if file_name in ["aai_logon", "__pycache__"]:
            continue

        result.append(file_name)
    return result


class SiteConfigs(NodeConfigs):
    TYPE = "site"
    TITLE_NAME = "Site"

    raw_module_name = ConfigOptions(optional=False, options=get_module_names(), gui_name="Module")
    use_folder = ConfigBool(default=True, gui_name="Use Folder")
    raw_folder_name = ConfigString(optional=True, active_func=raw_folder_name_active,
                                   gui_name="Folder Name", gray_out=True)
    raw_function = FunctionConfigString(active_func=raw_function_active, gui_name="Function")
    raw_folder_function = FunctionFolderConfigString(active_func=folder_function_active, gui_name="Function for Folder")

    raw_login_function = FunctionLoginConfigString(optional=True, gui_name="Login Function",
                                                   active_func=raw_login_function_active)

    consumer_kwargs = ConfigDict(layout={
        "allowed_extensions": ConfigListString(optional=True, gui_name="Allowed Extensions",
                                               hint_text="Add 'video' for all video types"),
        "forbidden_extensions": ConfigListString(optional=True, gui_name="Forbidden Extensions",
                                                 hint_text="Add 'video' for all video types"),
    }, gui_name="Download Arguments")

    function_kwargs = FunctionKwargsConfigDict(gui_name="Function Specific Arguments")

    def get_name(self):
        if self.raw_module_name is not None:
            return self.raw_module_name
        return "+ Add Site"

    def get_folder_name(self):
        if self.raw_module_name is None:
            return None
        if not self.use_folder:
            return "<No Folder>"
        if self.raw_folder_name:
            return self.raw_folder_name

        kwargs = nodes.Site.get_unique_key_kwargs(**self.to_dict())
        return get_folder_name_from_kwargs(kwargs)

    def get_icon(self):
        image_files = os.listdir(SITE_ICON_PATH)
        file_name = None
        for image_file in image_files:
            if self.raw_module_name is not None and self.raw_module_name in image_file:
                file_name = image_file
                break
        if file_name is None:
            return super(SiteConfigs, self).get_icon()

        path = os.path.join(SITE_ICON_PATH, file_name)
        return QIcon(path)
