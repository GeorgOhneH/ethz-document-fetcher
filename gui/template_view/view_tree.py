import logging
import os
import traceback

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from core import template_parser
from gui.template_view.view_tree_item import TreeWidgetItem
from settings import settings

logger = logging.getLogger(__name__)


class TemplateViewTree(QTreeWidget):
    def __init__(self, signals, controller, parent):
        super().__init__(parent=parent)
        self.widgets = {}
        self.controller = controller
        self.thread_is_running = False
        self.setColumnCount(4)
        self.setHeaderLabels(["Name", "New Files Added", "Replaced Files", "Status"])
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.prepare_menu)
        self.template = template_parser.Template(settings.template_path)
        try:
            self.template.load()
        except Exception as e:
            if settings.loglevel == "DEBUG":
                traceback.print_exc()
            error_dialog = QErrorMessage(self)
            error_dialog.showMessage(f"Error while loading the file. Error: {e}")
        self.init_view_tree()
        self.read_settings()

        self.setup_connections(signals)
        qApp.aboutToQuit.connect(self.save_state)

    def setup_connections(self, signals):
        signals.stopped.connect(self.stop_widgets)
        signals.finished.connect(self.quit_widgets)

        signals.update_folder_name.connect(self.update_folder_name)
        signals.update_base_path.connect(self.update_base_path)

        signals.added_new_file[str, str].connect(self.added_new_file)
        signals.replaced_file[str, str].connect(self.replaced_file)
        signals.replaced_file[str, str, str].connect(self.replaced_file)

        signals.site_started[str].connect(self.site_started)
        signals.site_started[str, str].connect(self.site_started)

        signals.site_finished_successful[str].connect(self.site_finished_successful)
        signals.site_finished_successful[str, str].connect(self.site_finished_successful)

        signals.site_quit_with_warning[str].connect(self.site_quit_with_warning)
        signals.site_quit_with_warning[str, str].connect(self.site_quit_with_warning)

        signals.site_quit_with_error[str].connect(self.site_quit_with_error)
        signals.site_quit_with_error[str, str].connect(self.site_quit_with_error)

    def save_state(self):
        qsettings = QSettings("eth-document-fetcher", "eth-document-fetcher")
        qsettings.setValue("templateViewTree/geometry", self.header().saveGeometry())
        qsettings.setValue("templateViewTree/windowState", self.header().saveState())

    def read_settings(self):
        qsettings = QSettings("eth-document-fetcher", "eth-document-fetcher")
        if qsettings.value("templateViewTree/geometry") is not None:
            self.header().restoreGeometry(qsettings.value("templateViewTree/geometry"))
        if qsettings.value("templateViewTree/windowState") is not None:
            self.header().restoreState(qsettings.value("templateViewTree/windowState"))

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

    @pyqtSlot(str, str)
    @pyqtSlot(str, str, str)
    def replaced_file(self, unique_key, path, old_path=None):
        self.widgets[unique_key].replaced_file(path, old_path)

    @pyqtSlot(str)
    @pyqtSlot(str, str)
    def site_started(self, unique_key, msg=None):
        self.widgets[unique_key].set_loading(msg)

    @pyqtSlot(str)
    @pyqtSlot(str, str)
    def site_finished_successful(self, unique_key, msg=None):
        widget = self.widgets[unique_key]
        widget.set_success(msg)

    @pyqtSlot(str)
    @pyqtSlot(str, str)
    def site_quit_with_warning(self, unique_key, msg=None):
        widget = self.widgets[unique_key]
        widget.set_warning(msg)

    @pyqtSlot(str)
    @pyqtSlot(str, str)
    def site_quit_with_error(self, unique_key, msg=None):
        widget = self.widgets[unique_key]
        widget.set_error(msg)

    @pyqtSlot()
    def reset_widgets(self):
        for key, widget in self.widgets.items():
            widget.set_idle()

    @pyqtSlot()
    def stop_widgets(self):
        for key, widget in self.widgets.items():
            if widget.state == widget.STATE_LOADING:
                widget.set_warning("Interrupted by user")

    @pyqtSlot()
    def quit_widgets(self):
        for key, widget in self.widgets.items():
            if widget.state == widget.STATE_LOADING:
                widget.set_error("Site did not give a finish Signal. (You should never see this message)")

    def add_item_widget(self, template_node, unique_key, widget_parent=None):
        widget = TreeWidgetItem(template_node)
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
        run_action_recursive.setEnabled(not self.controller.thread.isRunning())
        if self.controller.thread.isRunning():
            self.controller.thread.finished.connect(lambda: run_action_recursive.setEnabled(True))
        run_action_recursive.triggered.connect(lambda: self.controller.start_thread(widget.template_node.unique_key, True))

        run_action = menu.addAction("Run")
        run_action.setEnabled(not self.controller.thread.isRunning())
        if self.controller.thread.isRunning():
            self.controller.thread.finished.connect(lambda: run_action.setEnabled(True))
        run_action.triggered.connect(lambda: self.controller.start_thread(widget.template_node.unique_key, False))

        menu.addSeparator()

        open_folder_action = menu.addAction("Open Folder")
        if widget.template_node.base_path is not None:
            base_path = os.path.join(settings.base_path, widget.template_node.base_path)
            if not os.path.exists(base_path):
                open_folder_action.setEnabled(False)
            url = QUrl.fromLocalFile(base_path)
            open_folder_action.triggered.connect(lambda: QDesktopServices.openUrl(url))
        else:
            open_folder_action.setEnabled(False)

        menu.exec_(self.mapToGlobal(point))

    def init_view_tree(self):
        if self.template.root.folder is not None:
            self.init_widgets(self.template.root.folder, parent=None)
        for site in self.template.root.sites:
            self.init_widgets(site, parent=None)

        for key, widget in self.widgets.items():
            widget.init_widgets()

    def init_widgets(self, node, parent):
        widget = self.add_item_widget(node, node.unique_key, parent)

        if node.folder is not None:
            self.init_widgets(node.folder, parent=widget)
        for site in node.sites:
            self.init_widgets(site, parent=widget)