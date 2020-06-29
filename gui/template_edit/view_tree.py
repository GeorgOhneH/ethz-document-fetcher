import logging
import os
import traceback

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from core import template_parser
from settings.config import Configs
from core.template_parser.nodes.site_configs import SiteConfigs
from core.template_parser.nodes.folder import FolderConfigs
from gui.template_edit.view_tree_item import TreeEditWidgetItem
from settings import global_settings

logger = logging.getLogger(__name__)


class TemplateEditViewTree(QTreeWidget):
    def __init__(self, template_path, parent):
        super().__init__(parent=parent)
        self.setExpandsOnDoubleClick(False)
        self.widgets = []
        self.template = template_parser.Template(path=template_path)
        try:
            self.template.load()
        except Exception as e:
            if global_settings.loglevel == "DEBUG":
                traceback.print_exc()
            error_dialog = QErrorMessage(self)
            error_dialog.setWindowTitle("Error")
            error_dialog.showMessage(f"Error while loading the file. Error: {e}")
        self.init_view_tree()

        self.itemActivated.connect(self.open_dialog)

    def open_dialog(self, item, column):
        item.open_dialog()

    def add_item_widget(self, node_configs, widget_parent=None):
        widget = TreeEditWidgetItem(node_configs)
        if widget_parent is None:
            self.addTopLevelItem(widget)
        else:
            widget_parent.addChild(widget)

        self.widgets.append(widget)
        return widget

    def init_view_tree(self):
        if self.template.root.folder is None:
            self.add_item_widget(FolderConfigs())
        else:
            self.init_widgets(self.template.root.folder, parent=None)
        for site in self.template.root.sites:
            self.init_widgets(site, parent=None)
        self.add_item_widget(SiteConfigs())

        for widget in self.widgets:
            widget.init_widgets()

    def init_widgets(self, node, parent):
        widget = self.add_item_widget(node.get_configs(), parent)

        if node.folder is None:
            self.add_item_widget(FolderConfigs(), widget_parent=widget)
        else:
            self.init_widgets(node.folder, parent=widget)

        for site in node.sites:
            self.init_widgets(site, parent=widget)
        self.add_item_widget(SiteConfigs(), widget_parent=widget)
