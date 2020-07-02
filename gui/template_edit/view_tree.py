import logging
import os
import traceback

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from core import template_parser
from settings.config import Configs
from core.template_parser.nodes import Folder, Site
from core.template_parser.nodes.site_configs import SiteConfigs
from core.template_parser.nodes.folder import FolderConfigs
from gui.template_edit.view_tree_item import TreeEditWidgetItem
from settings import global_settings

logger = logging.getLogger(__name__)


class TemplateEditViewTree(QTreeWidget):
    def __init__(self, template_path, parent):
        super().__init__(parent=parent)
        self.setExpandsOnDoubleClick(False)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        self.viewport().setAcceptDrops(True)

        self.setColumnCount(1)
        self.setHeaderLabels(["Name"])

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.prepare_menu)
        self.setDragDropMode(QAbstractItemView.InternalMove)
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

        self.itemActivated.connect(self.edit_item)

    def edit_item(self, item, column=None):
        item.open_dialog()

    def add_item_widget(self, node_configs, item_status, widget_parent=None):
        widget = TreeEditWidgetItem(node_configs, item_status)
        if widget_parent is None:
            self.addTopLevelItem(widget)
        else:
            widget_parent.addChild(widget)

        self.widgets.append(widget)
        return widget

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            selected_items = self.selectedItems()
            if selected_items:
                self.delete_item(selected_items[0])
        super().keyPressEvent(event)

    def delete_item(self, item):
        if item.item_status == item.STATUS_NEW:
            return
        result = QMessageBox.question(self,
                                      "Are you sure?",
                                      "This will also delete all children",
                                      QMessageBox.Ok | QMessageBox.Cancel)

        if result != QMessageBox.Ok:
            return
        root = self.invisibleRootItem()
        (item.parent() or root).removeChild(item)

    def init_view_tree(self):
        for child in self.template.root.children:
            self.init_widgets(child, parent=None)
        self.add_item_widget(SiteConfigs(), TreeEditWidgetItem.STATUS_NEW)
        self.add_item_widget(FolderConfigs(), TreeEditWidgetItem.STATUS_NEW)

        for widget in self.widgets:
            widget.init_widgets()

    def init_widgets(self, node, parent):
        widget = self.add_item_widget(node.get_configs(), TreeEditWidgetItem.STATUS_SET, parent)

        for child in node.children:
            self.init_widgets(child, parent=widget)
        self.add_item_widget(SiteConfigs(), TreeEditWidgetItem.STATUS_NEW, widget_parent=widget)
        self.add_item_widget(FolderConfigs(), TreeEditWidgetItem.STATUS_NEW, widget_parent=widget)

    def convert_to_dict(self):
        template = template_parser.Template(path=None)
        root = template.root
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            self.item_to_template(item, root)

        return template.convert_to_dict()

    def convert_to_template(self, item, parent):
        for i in range(item.childCount()):
            child = item.child(i)
            self.item_to_template(child, parent)

    def item_to_template(self, item, parent):
        if item.item_status == TreeEditWidgetItem.STATUS_NEW:
            return

        kwargs = {config_obj.name: config_obj.get() for config_obj in item.node_configs}
        if item.node_configs.TYPE == FolderConfigs.TYPE:
            folder = Folder(**kwargs, parent=parent)
            self.convert_to_template(item, folder)
        elif item.node_configs.TYPE == SiteConfigs.TYPE:
            site = Site(**kwargs, parent=parent)
            self.convert_to_template(item, site)
        else:
            raise ValueError("Not valid type")

    def prepare_menu(self, point):
        item = self.itemAt(point)
        if item is None:
            return

        menu = QMenu(self)
        edit_action = menu.addAction("Edit")
        edit_action.triggered.connect(lambda: self.edit_item(item))
        delete_action = menu.addAction("Delete")
        delete_action.triggered.connect(lambda: self.delete_item(item))
        delete_action.setEnabled(item.item_status != item.STATUS_NEW)
        menu.exec_(self.mapToGlobal(point))
