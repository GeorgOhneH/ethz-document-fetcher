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
