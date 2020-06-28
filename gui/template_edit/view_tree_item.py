import logging
import time
import os

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import *

from core.storage import cache
from core.template_parser.nodes.base import NodeConfigs
from gui.template_edit.node_dialog import NodeDialog
from gui.constants import ASSETS_PATH

logger = logging.getLogger(__name__)


class TreeEditWidgetItem(QTreeWidgetItem):
    def __init__(self, node_configs: NodeConfigs):
        super().__init__()
        self.node_configs = node_configs
        self.dialog = NodeDialog(node_configs=node_configs, parent=None)

    def init_widgets(self):
        if self.childCount() > 2:
            self.setExpanded(True)
        self.setText(0, self.node_configs.get_name())

    def open_dialog(self):
        self.dialog.open()

