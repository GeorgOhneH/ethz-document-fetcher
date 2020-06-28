import logging

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from gui.configs_dialoge import ConfigsDialog, ConfigsScrollArea

from settings import global_settings

logger = logging.getLogger(__name__)


class NodeDialog(ConfigsDialog):
    def __init__(self, parent, node_configs):
        super(QDialog, self).__init__(parent=parent)
        settings_areas = [
            ConfigsScrollArea(node_configs, parent=self),
        ]
        super().__init__(*settings_areas, parent=parent)
        self.setWindowTitle("WDW")


class SettingScrollArea(ConfigsScrollArea):
    def __init__(self, settings, save_changes=True, parent=None):
        super().__init__(parent=parent, configs=settings)
        self.save_changes = save_changes
        self.required.setTitle("General" + (" (Requires Restart)" if not save_changes else ""))
        self.optional.setTitle("Optional" + (" (Requires Restart)" if not save_changes else ""))
