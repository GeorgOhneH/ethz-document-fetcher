import hashlib
import os

from PyQt5.QtGui import *

from core.template_parser.nodes.utils import get_kwargs_hash, get_folder_name_from_hash
from core.utils import safe_path_join
from gui.constants import ASSETS_PATH
from settings.config import Configs


class NodeConfigs(Configs):
    TYPE = "base"
    TITLE_NAME = "Node"

    def get_name(self):
        raise NotImplementedError

    def get_folder_name(self):
        return None

    def get_icon_path(self):
        return TemplateNode.DEFAULT_ICON_PATH


class TemplateNode(object):
    DEFAULT_ICON_PATH = os.path.join(ASSETS_PATH, "globe.svg")

    def __init__(self, parent,
                 folder_name=None,
                 unique_key_kwargs=None,
                 use_folder=True,
                 is_producer=False,
                 meta_data=None):
        if meta_data is None:
            meta_data = {}
        if unique_key_kwargs is None:
            unique_key_kwargs = {}
        self.unique_key_kwargs = unique_key_kwargs
        self.meta_data = meta_data
        self.is_producer = is_producer
        self.use_folder = use_folder
        self.parent = parent
        self.children = []

        self.child_index = self._init_parent()
        self.position = self._init_position()
        self.kwargs_hash = get_kwargs_hash(self.unique_key_kwargs)

        self.unique_key = self._init_unique_key()
        self.folder_name = self._init_folder_name(folder_name)
        self.base_path = self._init_base_path(use_folder)

    def __str__(self):
        return self.unique_key

    def _init_position(self):
        return self.parent.position + self.child_index

    def _init_parent(self):
        return self.parent.add_node(self)

    def add_node(self, node):
        self.children.append(node)
        node.parent = self
        return f"{len(self.children) - 1}:"

    def _init_base_path(self, use_folder):
        if not self.use_folder:
            return self.parent.base_path

        if self.folder_name is None:
            return

        if self.parent.base_path is None:
            return

        return safe_path_join(self.parent.base_path, self.folder_name)

    def _init_folder_name(self, folder_name):
        if folder_name is None:
            folder_name = get_folder_name_from_hash(self.kwargs_hash)

        return folder_name

    def _init_unique_key(self):
        unique_string = self.position + self.kwargs_hash
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

    def get_type_name(self):
        return "Base"

    def get_gui_icon_path(self):
        return self.DEFAULT_ICON_PATH

    def get_configs(self):
        return NodeConfigs()

    async def add_producers(self, producers, session, queue, site_settings, cancellable_pool, signal_handler):
        pass

    def has_website_url(self):
        return False

    def get_website_url(self):
        raise NotImplemented
