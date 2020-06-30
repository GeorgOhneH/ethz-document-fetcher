import logging
import time
import os

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import *

from core.storage import cache
from core.template_parser.nodes.site_configs import SiteConfigs
from core.template_parser.nodes.folder import FolderConfigs
from core.template_parser.nodes.base import NodeConfigs
from gui.template_edit.node_dialog import NodeDialog
from gui.constants import ASSETS_PATH

logger = logging.getLogger(__name__)


class TreeEditWidgetItem(QTreeWidgetItem):
    STATUS_NEW = 0
    STATUS_SET = 1

    def __init__(self, node_configs: NodeConfigs, item_status):
        super().__init__()
        self.node_configs = node_configs
        self.item_status = item_status
        self.set_flags()
        self.dialog = NodeDialog(node_configs=node_configs, parent=None)
        self.dialog.accepted.connect(self.update)

    def set_flags(self):
        standard_flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if self.item_status == self.STATUS_NEW:
            self.setFlags(standard_flags)
        elif self.node_configs.TYPE == FolderConfigs.TYPE:
            self.setFlags(standard_flags | Qt.ItemIsDropEnabled)
        elif self.node_configs.TYPE == SiteConfigs.TYPE:
            self.setFlags(standard_flags | Qt.ItemIsDropEnabled | Qt.ItemIsDragEnabled)

    def init_widgets(self):
        if self.childCount() > 2:
            self.setExpanded(True)
        self.setText(0, self.node_configs.get_name())
        self.setIcon(0, self.node_configs.get_icon())

    def open_dialog(self):
        self.dialog.show()

    def update(self):
        self.setText(0, self.node_configs.get_name())
        self.setIcon(0, self.node_configs.get_icon())
        if self.item_status == self.STATUS_NEW:
            folder_child = TreeEditWidgetItem(FolderConfigs(), self.STATUS_NEW)
            site_child = TreeEditWidgetItem(SiteConfigs(), self.STATUS_NEW)
            self.addChildren([folder_child, site_child])
            folder_child.init_widgets()
            site_child.init_widgets()
            if self.node_configs.TYPE == SiteConfigs.TYPE:
                site_sibling = TreeEditWidgetItem(SiteConfigs(), self.STATUS_NEW)
                if self.parent() is None:
                    self.treeWidget().addTopLevelItem(site_sibling)
                else:
                    self.parent().addChild(site_sibling)
                site_sibling.init_widgets()

            self.item_status = self.STATUS_SET
            self.set_flags()
