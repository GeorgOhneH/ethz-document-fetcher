import logging
import os
import importlib

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from core import template_parser
from gui.template_view.view_tree_item import TreeWidgetItem
from gui.utils import widget_read_settings, widget_save_settings
from settings import gui_settings

logger = logging.getLogger(__name__)


class HeaderItem(QTreeWidgetItem):
    def __init__(self):
        super().__init__()
        self.added_new_count = 0
        self.replaced_count = 0
        self.setText(TreeWidgetItem.COLUMN_NAME, "Name")
        self.setText(TreeWidgetItem.COLUMN_STATE, "State")
        self.setText(TreeWidgetItem.COLUMN_TYPE, "Type")
        self.setTextAlignment(TreeWidgetItem.COLUMN_ADDED_FILE, Qt.AlignRight | Qt.AlignVCenter)
        self.setTextAlignment(TreeWidgetItem.COLUMN_REPLACED_FILE, Qt.AlignRight | Qt.AlignVCenter)
        self.set_text_replaced()
        self.set_text_added()

    def set_text_added(self):
        self.setText(TreeWidgetItem.COLUMN_ADDED_FILE, f"New Files Added ({self.added_new_count})")

    def set_text_replaced(self):
        self.setText(TreeWidgetItem.COLUMN_REPLACED_FILE, f"Replaced Files ({self.replaced_count})")

    def added_new_file(self):
        self.added_new_count += 1
        self.set_text_added()

    def replaced_file(self):
        self.replaced_count += 1
        self.set_text_replaced()

    def reset(self):
        self.replaced_count = 0
        self.added_new_count = 0
        self.set_text_added()
        self.set_text_replaced()


class TemplateViewTree(QTreeWidget):
    def __init__(self, template_path, signals, controller, parent):
        super().__init__(parent=parent)
        self.widgets = {}
        self.controller = controller
        self.setColumnCount(5)
        self.header_item = HeaderItem()
        self.setHeaderItem(self.header_item)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.prepare_menu)

        self.template = None
        self._template_load_error = False
        self.init(template_path)

        self.read_settings()

        self.connection_map = [
            (signals.stopped, self.stop_widgets),
            (signals.finished, self.quit_widgets),
            (signals.update_folder_name, self.update_folder_name),
            (signals.update_base_path, self.update_base_path),
            (signals.added_new_file[str, str], self.added_new_file),
            (signals.replaced_file[str, str], self.replaced_file),
            (signals.replaced_file[str, str, str], self.replaced_file),
            (signals.site_started[str], self.site_started),
            (signals.site_started[str, str], self.site_started),
            (signals.site_finished[str], self.site_finished),
            (signals.site_finished[str, str], self.site_finished),
            (signals.got_warning[str], self.got_warning),
            (signals.got_warning[str, str], self.got_warning),
            (signals.got_error[str], self.got_error),
            (signals.got_error[str, str], self.got_error),
            (qApp.aboutToQuit, self.save_state),
        ]

        self.setup_connections()

    def init(self, template_path):
        self.template = template_parser.Template(path=template_path)
        self.header_item.reset()
        try:
            self.template.load()
            self._template_load_error = False
        except Exception as e:
            msg = f"Error while loading the file. {e.__class__.__name__}: {e}"
            logger.error(msg, exc_info=True)
            self._template_load_error = True
            error_dialog = QErrorMessage(self)
            error_dialog.setWindowTitle("Error")
            error_dialog.showMessage(msg)
            error_dialog.raise_()
        self.init_view_tree()

    def setup_connections(self):
        for signal, func in self.connection_map:
            signal.connect(func)

    def disconnect_connections(self):
        for signal, func in self.connection_map:
            signal.disconnect(func)

    def save_state(self):
        widget_save_settings(self.header(), name="templateViewTreeHeader")

    def read_settings(self):
        widget_read_settings(self.header(), name="templateViewTreeHeader")

    def save_template_file(self):
        if self._template_load_error:
            logger.warning("Error on load. Not saving template")
            return

        logger.debug("Saving Template")
        for widget in self.widgets.values():
            node = widget.template_node
            node.meta_data["check_state"] = int(widget.get_check_state())

        self.template.save_template()

    def emit_item_changed(self, item, column):
        self.itemChanged.emit(item, column)

    def set_check_state_to_all(self, state):
        for widget in self.widgets.values():
            widget.set_check_state(state)

    def get_checked(self):
        return [widget for widget in self.widgets.values() if widget.get_check_state() != Qt.Unchecked]

    @pyqtSlot(str, str)
    def update_folder_name(self, unique_key, folder_name):
        logger.debug(f"{unique_key} folder_name got updated to {folder_name}")
        self.widgets[unique_key].set_folder_name(folder_name)

    @pyqtSlot(str, str)
    def update_base_path(self, unique_key, base_path):
        logger.debug(f"{unique_key} base_path got updated to {base_path}")
        self.widgets[unique_key].set_base_path(base_path)

    @pyqtSlot(str, str)
    def added_new_file(self, unique_key, path):
        self.widgets[unique_key].added_new_file(path)
        self.header_item.added_new_file()

    @pyqtSlot(str, str)
    @pyqtSlot(str, str, str)
    def replaced_file(self, unique_key, path, old_path=None):
        self.widgets[unique_key].replaced_file(path, old_path)
        self.header_item.replaced_file()

    @pyqtSlot(str)
    @pyqtSlot(str, str)
    def site_started(self, unique_key, msg=None):
        self.widgets[unique_key].set_loading(msg)

    @pyqtSlot(str)
    @pyqtSlot(str, str)
    def site_finished(self, unique_key, msg=None):
        widget = self.widgets[unique_key]
        widget.set_success(msg)

    @pyqtSlot(str)
    @pyqtSlot(str, str)
    def got_warning(self, unique_key, msg=None):
        widget = self.widgets[unique_key]
        widget.got_warning(msg)

    @pyqtSlot(str)
    @pyqtSlot(str, str)
    def got_error(self, unique_key, msg=None):
        widget = self.widgets[unique_key]
        widget.got_error(msg)

    @pyqtSlot()
    def reset_widgets(self):
        for key, widget in self.widgets.items():
            widget.reset()

    @pyqtSlot()
    def stop_widgets(self):
        for key, widget in self.widgets.items():
            widget.got_warning("Interrupted by user")

    @pyqtSlot()
    def quit_widgets(self):
        for key, widget in self.widgets.items():
            if widget.state == widget.STATE_LOADING:
                widget.set_error("Site did not give a finish Signal. (You should never see this message)")

    def add_item_widget(self, template_node, unique_key, widget_parent=None):
        widget = TreeWidgetItem(template_node, self.controller)
        if widget_parent is None:
            self.addTopLevelItem(widget)
        else:
            widget_parent.addChild(widget)

        self.widgets[unique_key] = widget
        return widget

    def prepare_menu(self, point):
        widget = self.itemAt(point)
        if widget is None:
            return

        menu = QMenu(self)

        run_action_recursive = menu.addAction("Run recursive")
        run_action_recursive.setEnabled(not self.controller.thread.isRunning() and
                                        widget.template_node.parent.base_path is not None)
        if self.controller.thread.isRunning():
            self.controller.thread.finished.connect(lambda template_node=widget.template_node:
                                                    run_action_recursive.setEnabled(
                                                        template_node.parent.base_path is not None))
        run_action_recursive.triggered.connect(
            lambda: self.controller.start_thread([widget.template_node.unique_key], True))

        run_action = menu.addAction("Run")
        run_action.setEnabled(not self.controller.thread.isRunning()
                              and widget.template_node.parent.base_path is not None)
        if self.controller.thread.isRunning():
            self.controller.thread.finished.connect(lambda template_node=widget.template_node:
                                                    run_action_recursive.setEnabled(
                                                        template_node.parent.base_path is not None))
        run_action.triggered.connect(lambda: self.controller.start_thread([widget.template_node.unique_key], False))

        menu.addSeparator()

        open_folder_action = menu.addAction("Open Folder")
        if widget.template_node.base_path is not None and self.controller.site_settings.base_path is not None:
            base_path = os.path.join(self.controller.site_settings.base_path, widget.template_node.base_path)
            if not os.path.exists(base_path):
                open_folder_action.setEnabled(False)
            url = QUrl.fromLocalFile(base_path)
            open_folder_action.triggered.connect(lambda: QDesktopServices.openUrl(url))
        else:
            open_folder_action.setEnabled(False)

        menu.addSeparator()

        open_website_action = menu.addAction("Open Website")
        if widget.template_node.has_website_url():
            open_website_action.setEnabled(True)
            open_website_action.triggered.connect(
                lambda: QDesktopServices.openUrl(QUrl(widget.template_node.get_website_url())))
        else:
            open_website_action.setEnabled(False)

        menu.exec_(self.mapToGlobal(point))

    def init_view_tree(self):
        self.widgets.clear()
        self.clear()

        for child in self.template.root.children:
            self.init_widgets(child, parent=None)

        for key, widget in self.widgets.items():
            widget.init_widgets()

    def init_widgets(self, node, parent):
        widget = self.add_item_widget(node, node.unique_key, parent)

        for child in node.children:
            self.init_widgets(child, parent=widget)
