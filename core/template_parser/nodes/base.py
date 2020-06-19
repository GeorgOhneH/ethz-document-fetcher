import hashlib
import os

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from core.storage import cache
from core.utils import safe_path_join
from gui.constants import ASSETS_PATH


class TemplateNode(object):
    DEFAULT_ICON_PATH = os.path.join(ASSETS_PATH, "globe.svg")

    def __init__(self, parent, folder_name=None, unique_key_args=None, use_folder=True):
        if unique_key_args is None:
            unique_key_args = []
        self.position = None
        self.use_folder = use_folder
        self.parent = parent
        self.folder = None
        self.sites = []
        child_position = self._init_parent()

        self.unique_key = self._init_unique_key(child_position, *unique_key_args)
        self.base_path = self._init_base_path(folder_name, use_folder)

    def __str__(self):
        return self.unique_key

    def _init_parent(self):
        raise NotImplementedError()

    def add_site(self, child):
        if child.parent is None:
            raise ValueError("Child already has a parent")
        self.sites.append(child)
        child.parent = self
        return f"site:{len(self.sites) - 1}"

    def add_folder(self, folder):
        if folder.parent is None:
            raise ValueError("Child already has a parent")
        self.folder = folder
        folder.parent = self
        return "folder"

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

    def _init_unique_key(self, child_position, *args):
        if self.parent.position is None:
            raise ValueError("parents position must be set")
        self.position = self.parent.position + child_position
        unique_string = self.position + "".join([f"{value}" for value in args])
        return hashlib.md5(unique_string.encode('utf-8')).hexdigest()

    def get_gui_name(self):
        return str(self)

    def get_gui_icon(self):
        return QIcon(self.DEFAULT_ICON_PATH)

    def gui_options(self):
        return []

    async def add_producers(self, producers, session, queue, signal_handler):
        pass
