import logging
import os
import traceback

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from core import template_parser
from gui.template_edit.view_tree_item import TreeEditWidgetItem
from settings import global_settings

logger = logging.getLogger(__name__)


class TemplateEditViewTree(QTreeWidget):
    def __init__(self, template_path, parent):
        super().__init__(parent=parent)
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

    def add_item_widget(self, template_node, widget_parent=None):
        print("node", template_node)
        widget = TreeEditWidgetItem(template_node)
        if widget_parent is None:
            self.addTopLevelItem(widget)
        else:
            widget_parent.addChild(widget)

        self.widgets.append(widget)
        return widget

    def init_view_tree(self):
        self.init_widgets(self.template.root.folder, parent=None)
        for site in [*self.template.root.sites, None]:
            print(site)
            self.init_widgets(site, parent=None)

        for widget in self.widgets:
            widget.init_widgets()

    def init_widgets(self, node, parent):
        widget = self.add_item_widget(node, parent)

        if node is None:
            return

        self.init_widgets(node.folder, parent=widget)
        for site in [*node.sites, None]:
            self.init_widgets(site, parent=widget)
