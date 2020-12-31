import logging

from PyQt5.QtCore import *

from gui.configs_dialoge import ConfigsDialog, ConfigsScrollArea
from settings import advanced_settings, gui_settings

logger = logging.getLogger(__name__)


class SettingsDialog(ConfigsDialog):
    settings_saved = pyqtSignal()

    def __init__(self, parent, site_settings):
        super().__init__(parent=parent)
        settings_areas = [
            ConfigsScrollArea(site_settings, parent=self),
            ConfigsScrollArea(advanced_settings, parent=self),
            ConfigsScrollArea(gui_settings, parent=self),
        ]
        self.init(settings_areas)
        self.setWindowTitle("Settings")

        self.accepted.connect(lambda: site_settings.save())
        self.accepted.connect(lambda: advanced_settings.save())
        self.accepted.connect(lambda: gui_settings.save())

        self.accepted.connect(lambda: self.settings_saved.emit())

