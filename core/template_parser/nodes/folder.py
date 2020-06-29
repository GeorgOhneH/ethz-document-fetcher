import os

from PyQt5.QtGui import *

from core.template_parser.nodes.base import TemplateNode, NodeConfigs
from gui.constants import ASSETS_PATH
from settings.config import Configs

from settings.config_objs import ConfigString


class FolderConfigs(NodeConfigs):
    TITLE_NAME = "Folder"
    name = ConfigString()

    def get_name(self):
        if self.name is not None:
            return self.name
        return "+ Add Folder"

    def get_icon(self):
        return QIcon(Folder.FOLDER_ICON_PATH)


class Folder(TemplateNode):
    FOLDER_ICON_PATH = os.path.join(ASSETS_PATH, "folder.svg")

    def __init__(self, name, parent):
        super().__init__(parent=parent, folder_name=name, unique_key_args=[name])
        self.name = name

    def __str__(self):
        return self.name

    def _init_parent(self):
        return self.parent.add_folder(self)

    def get_gui_name(self):
        return self.name

    def get_gui_icon(self):
        return QIcon(self.FOLDER_ICON_PATH)

    def gui_options(self):
        return [
            ("name", self.name),
        ]

    def get_configs(self):
        folder_configs = FolderConfigs()
        folder_configs.name = self.name
        return folder_configs
