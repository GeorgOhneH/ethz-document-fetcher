import os

from core.template_parser.nodes.base import TemplateNode, NodeConfigs
from gui.constants import ASSETS_PATH
from settings.config_objs import ConfigString


class FolderConfigs(NodeConfigs):
    TYPE = "folder"
    TITLE_NAME = "Folder"
    name = ConfigString(gui_name="Name")

    def get_name(self):
        if self.name is not None:
            return self.name
        return "+ Add Folder"

    def get_folder_name(self):
        return self.name

    def get_icon_path(self):
        return Folder.FOLDER_ICON_PATH


class Folder(TemplateNode):
    FOLDER_ICON_PATH = os.path.join(ASSETS_PATH, "folder.svg")

    def __init__(self, name, parent, **kwargs):
        super().__init__(parent=parent,
                         folder_name=name,
                         unique_key_kwargs=dict(name=name),
                         **kwargs)
        self.name = name

    def __str__(self):
        return self.name

    def convert_to_dict(self, result=None):
        result = {"folder": self.name}
        return super().convert_to_dict(result=result)

    def get_gui_name(self):
        return self.name

    def get_gui_icon_path(self):
        return self.FOLDER_ICON_PATH

    def get_type_name(self):
        return "Folder"

    def get_configs(self):
        folder_configs = FolderConfigs(super().get_configs())
        try:
            folder_configs.name = self.name
        except ValueError:
            pass
        return folder_configs
