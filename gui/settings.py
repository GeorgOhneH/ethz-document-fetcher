import logging

from gui.configs_dialoge import ConfigsDialog, ConfigsScrollArea
from settings import global_settings

logger = logging.getLogger(__name__)


class SettingsDialog(ConfigsDialog):
    def __init__(self, parent, site_settings):
        super().__init__(parent=parent)
        settings_areas = [
            ConfigsScrollArea(site_settings, parent=self),
            ConfigsScrollArea(global_settings, parent=self),
        ]
        self.init(settings_areas)
        self.setWindowTitle("Settings")

        self.accepted.connect(lambda: site_settings.save())

