import logging

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from gui.configs_dialoge import ConfigsDialog, ConfigsScrollArea

from settings import global_settings

logger = logging.getLogger(__name__)


class SettingsDialog(ConfigsDialog):
    def __init__(self, parent, site_settings):
        super().__init__(parent=parent)
        settings_areas = [
            SettingScrollArea(site_settings, parent=self),
            SettingScrollArea(global_settings, save_changes=False, parent=self),
        ]
        self.init(settings_areas)
        self.setWindowTitle("Settings")


class SettingScrollArea(ConfigsScrollArea):
    def __init__(self, settings, save_changes=True, parent=None):
        super().__init__(parent=parent, configs=settings)
        self.save_changes = save_changes
        self.required.setTitle("General" + (" (Requires Restart)" if not save_changes else ""))
        self.optional.setTitle("Optional" + (" (Requires Restart)" if not save_changes else ""))

    def update_widgets(self):
        if not self.save_changes:
            return
        super(SettingScrollArea, self).update_widgets()

    def apply_value(self):
        if not self.save_changes:
            return
        super(SettingScrollArea, self).apply_value()
        self.configs.save()
