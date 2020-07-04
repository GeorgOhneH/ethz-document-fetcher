import logging

from gui.configs_dialoge import ConfigsDialog, ConfigsScrollArea

logger = logging.getLogger(__name__)


class NodeDialog(ConfigsDialog):
    def __init__(self, parent, node_configs):
        super().__init__(parent=parent)
        settings_areas = [
            ConfigsScrollArea(node_configs, parent=self),
        ]
        self.init(settings_areas)
        self.setWindowTitle(node_configs.TITLE_NAME)


class SettingScrollArea(ConfigsScrollArea):
    def __init__(self, settings, save_changes=True, parent=None):
        super().__init__(parent=parent, configs=settings)
        self.save_changes = save_changes
        self.required.setTitle("General" + (" (Requires Restart)" if not save_changes else ""))
        self.optional.setTitle("Optional" + (" (Requires Restart)" if not save_changes else ""))
