import logging

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from gui.application import Application
from gui.configs_dialoge import ConfigsDialog, ConfigsScrollArea

logger = logging.getLogger(__name__)


class SettingsDialog(ConfigsDialog):
    settings_saved = pyqtSignal()

    def __init__(self, download_settings):
        super().__init__(parent=None)
        behavior_settings = Application.instance().behavior_settings
        gui_settings = Application.instance().gui_settings

        settings_areas = [
            ConfigsScrollArea(download_settings, parent=self),
            ConfigsScrollArea(behavior_settings, parent=self),
            ConfigsScrollArea(gui_settings, parent=self),
        ]
        self.init(settings_areas)
        self.setWindowTitle("Settings")

        self.accepted.connect(lambda: download_settings.save())
        self.accepted.connect(lambda: behavior_settings.save())
        self.accepted.connect(lambda: gui_settings.save())

        self.accepted.connect(lambda: self.settings_saved.emit())

