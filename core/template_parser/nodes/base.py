import hashlib
import os

from PyQt5.QtGui import *

from core.storage import cache
from core.utils import safe_path_join
from gui.constants import ASSETS_PATH
from settings.config import Configs


class NodeConfigs(Configs):
    TYPE = "base"
    TITLE_NAME = "Node"

    def get_name(self):
        raise NotImplementedError

    def get_icon(self):
        return QIcon(TemplateNode.DEFAULT_ICON_PATH)


class TemplateNode(object):
    DEFAULT_ICON_PATH = os.path.join(ASSETS_PATH, "globe.svg")

    def __init__(self, parent,
                 folder_name=None,
                 unique_key_args=None,
                 use_folder=True,
                 is_producer=False,
                 meta_data=None):
        if meta_data is None:
            meta_data = {}
        self.meta_data = meta_data
        self.is_producer = is_producer
        if unique_key_args is None:
            unique_key_args = []
        self.position = None
        self.use_folder = use_folder
        self.parent = parent
        self.children = []
        self.child_index = self._init_parent()

        self.unique_key = self._init_unique_key(self.child_index, *unique_key_args)
        self.base_path = self._init_base_path(folder_name, use_folder)

    def __str__(self):
        return self.unique_key

    def _init_parent(self):
        return self.parent.add_node(self)

    def add_node(self, node):
        self.children.append(node)
        node.parent = self
        return f"{len(self.children) - 1}:"

    def _init_base_path(self, folder_name, use_folder):
        if not self.use_folder:
            return self.parent.base_path

        if folder_name is None:
            folder_name_cache = cache.get_json("folder_name")
            folder_name = folder_name_cache.get(self.unique_key, None)

        if folder_name is None:
            return None

        if self.parent.base_path is None:
            return None

        return safe_path_join(self.parent.base_path, folder_name)

    def _init_unique_key(self, child_index, *args):
        if self.parent.position is None:
            raise ValueError("parents position must be set")
        self.position = self.parent.position + child_index
        unique_string = self.position + "".join([f"{value}" for value in args])
        return hashlib.md5(unique_string.encode('utf-8')).hexdigest()

    def convert_to_dict(self, result=None):
        if result is None:
            result = {}

        children = []

        for node in self.children:
            children.append(node.convert_to_dict())

        if self.meta_data:
            result["meta_data"] = self.meta_data

        if len(children) > 0:
            result["children"] = children

        return result

    def get_gui_name(self):
        return str(self)

    def get_gui_icon(self):
        return QIcon(self.DEFAULT_ICON_PATH)

    def gui_options(self):
        return []

    def get_configs(self):
        return NodeConfigs()

    async def add_producers(self, producers, session, queue, site_settings, cancellable_pool, signal_handler):
        pass
