import datetime
import logging
import os

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from gui.template_view.info_view.base import InfoView
from gui.constants import EMPTY_FOLDER_PATH

logger = logging.getLogger(__name__)


class FolderInfoView(QTreeView, InfoView):
    def __init__(self, controller, parent=None):
        super().__init__(parent=parent, name="Folder", controller=controller)
        self.model = QFileSystemModel()
        self.setModel(self.model)
        self.read_settings()
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.prepare_menu)
        self.activated.connect(self.open_file_with_index)
        qApp.aboutToQuit.connect(self.save_state)

    def change_root(self, path):
        if path is None or not os.path.exists(path):
            index = self.model.setRootPath(EMPTY_FOLDER_PATH)
        else:
            index = self.model.setRootPath(path)
        self.setRootIndex(index)

    def update_view(self, selected_widget):
        path = selected_widget.template_node.base_path
        if path is not None and self.controller.site_settings.base_path is not None:
            absolute_path = os.path.join(self.controller.site_settings.base_path, path)
            self.change_root(absolute_path)
        else:
            self.change_root(None)

    def open_file_with_index(self, index):
        if not index.isValid():
            return

        file_info = self.model.fileInfo(index)
        if file_info.isFile():
            self.open_file(file_info.filePath())

    def open_file(self, path):
        url = QUrl.fromLocalFile(path)
        QDesktopServices.openUrl(url)

    def open_folder(self, path):
        url = QUrl.fromLocalFile(os.path.dirname(path))
        QDesktopServices.openUrl(url)

    def prepare_menu(self, point):
        index = self.indexAt(point)
        if not index.isValid():
            return

        file_info = self.model.fileInfo(index)

        menu = QMenu(self)
        if file_info.isFile():
            open_file_action = menu.addAction("Open File")
            open_file_action.triggered.connect(lambda: self.open_file(file_info.filePath()))
            open_folder_action = menu.addAction("Open Folder")
            open_folder_action.triggered.connect(lambda: self.open_folder(file_info.filePath()))
        else:
            open_folder_action = menu.addAction("Open Folder")
            open_folder_action.triggered.connect(lambda: self.open_file(file_info.filePath()))

        menu.exec_(self.mapToGlobal(point))

    def save_state(self):
        qsettings = QSettings("eth-document-fetcher", "eth-document-fetcher")
        qsettings.setValue("infoFolderView/geometry", self.header().saveGeometry())
        qsettings.setValue("infoFolderView/windowState", self.header().saveState())

    def read_settings(self):
        qsettings = QSettings("eth-document-fetcher", "eth-document-fetcher")
        if qsettings.value("infoFolderView/geometry") is not None:
            self.header().restoreGeometry(qsettings.value("infoFolderView/geometry"))
        if qsettings.value("infoFolderView/windowState") is not None:
            self.header().restoreState(qsettings.value("infoFolderView/windowState"))
