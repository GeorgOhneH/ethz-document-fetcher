import logging

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from core.template_parser.nodes.base import NodeConfigs
from core.template_parser.nodes.folder import FolderConfigs
from core.template_parser.nodes.site_configs import SiteConfigs
from gui.template_edit.node_dialog import NodeDialog
from gui.dynamic_widgets import DynamicIcon

logger = logging.getLogger(__name__)


class TreeEditWidgetItem(QTreeWidgetItem):
    STATUS_NEW = 0
    STATUS_SET = 1

    def __init__(self, node_configs: NodeConfigs, item_status):
        super().__init__()
        self.node_configs = node_configs
        self.item_status = item_status
        self.dialog = None
        self.set_flags()

    def set_flags(self):
        standard_flags = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if self.item_status == self.STATUS_NEW:
            self.setFlags(standard_flags)
        else:
            self.setFlags(standard_flags | Qt.ItemIsDropEnabled | Qt.ItemIsDragEnabled)

    def init_widgets(self):
        if self.childCount() > 2:
            self.setExpanded(True)
        self._init_widgets()

    def _init_widgets(self):
        self.setText(0, self.node_configs.get_name())
        self.setIcon(0, DynamicIcon(self.node_configs.get_icon_path()))
        self.setText(1, self.node_configs.get_folder_name())
        self.setText(2, self.node_configs.get_note())
        self.setForeground(2, QBrush(Qt.red))

    def open_dialog(self):
        self.dialog = NodeDialog(node_configs=self.node_configs, parent=self.treeWidget())
        self.dialog.accepted.connect(self.update)
        self.dialog.exec()

    def update(self):
        self._init_widgets()
        if self.item_status == self.STATUS_NEW:
            folder_child = TreeEditWidgetItem(FolderConfigs(), self.STATUS_NEW)
            site_child = TreeEditWidgetItem(SiteConfigs(), self.STATUS_NEW)
            self.addChild(folder_child)
            self.addChild(site_child)
            folder_child.init_widgets()
            site_child.init_widgets()

            sibling = None
            if self.node_configs.TYPE == SiteConfigs.TYPE:
                sibling = TreeEditWidgetItem(SiteConfigs(), self.STATUS_NEW)
            elif self.node_configs.TYPE == FolderConfigs.TYPE:
                sibling = TreeEditWidgetItem(FolderConfigs(), self.STATUS_NEW)

            if sibling is not None:
                if self.parent() is None:
                    self.treeWidget().addTopLevelItem(sibling)
                else:
                    self.parent().addChild(sibling)
                sibling.init_widgets()

            self.item_status = self.STATUS_SET
            self.set_flags()
            self.treeWidget().order_item(self)
