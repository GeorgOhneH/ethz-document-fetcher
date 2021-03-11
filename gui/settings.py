import logging

import gui
from gui import ConfigsDialog

logger = logging.getLogger(__name__)


class SettingsDialog(ConfigsDialog):
    def __init__(self, download_settings, parent=None):
        super().__init__(parent=parent)
        app = gui.Application.instance()
        behavior_settings = app.behavior_settings
        gui_settings = app.gui_settings

        settings_areas = [
            gui.ConfigsScrollArea(download_settings, parent=self),
            gui.ConfigsScrollArea(behavior_settings, parent=self),
            gui.ConfigsScrollArea(gui_settings, parent=self),
        ]
        self.init(settings_areas)
        self.setWindowTitle("Settings")

        self.accepted.connect(lambda: download_settings.save())
        self.accepted.connect(lambda: behavior_settings.save())
        self.accepted.connect(lambda: gui_settings.save())

        self.accepted.connect(lambda: app.settings_saved.emit())

