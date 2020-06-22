import os

from PyQt5.QtGui import *

from core.template_parser.nodes.base import TemplateNode
from gui.constants import ASSETS_PATH


class Folder(TemplateNode):
    FOLDER_ICON_PATH = os.path.join(ASSETS_PATH, "folder.svg")

    def __init__(self, name, parent, site_settings):
        super().__init__(parent=parent, site_settings=site_settings, folder_name=name, unique_key_args=[name])
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
