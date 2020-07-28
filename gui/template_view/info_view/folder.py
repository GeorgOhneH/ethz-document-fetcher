import logging
import os
import shutil

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from gui.constants import EMPTY_FOLDER_PATH
from gui.template_view.info_view.base import InfoView

logger = logging.getLogger(__name__)


class FolderInfoView(QTreeView, InfoView):
    def __init__(self, controller, parent=None):
        super().__init__(parent=parent, name="Folder", controller=controller)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.model = QFileSystemModel()
        self.setModel(self.model)
        self.read_settings()
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.prepare_menu)
        self.activated.connect(self.open_file_with_index)
        qApp.aboutToQuit.connect(self.save_state)

    def reset_widget(self):
        self.change_root(None)

    def change_root(self, path):
        if path is None or not os.path.exists(path):
            index = self.model.setRootPath(EMPTY_FOLDER_PATH)
        else:
            index = self.model.setRootPath(path)
        self.setRootIndex(index)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            selected_indexes = self.selectedIndexes()
            if selected_indexes:
                self.delete_item(selected_indexes)
        super().keyPressEvent(event)

    def delete_item(self, indexes):
        if not indexes:
            return

        paths = set()
        for index in indexes:
            if not index.isValid():
                continue
            file_info = self.model.fileInfo(index)
            if os.path.exists(file_info.absoluteFilePath()):
                paths.add(file_info.absoluteFilePath())

        result = QMessageBox.question(self,
                                      "Are you sure?",
                                      f"This will delete {len(paths)} file/folders",
                                      QMessageBox.Ok | QMessageBox.Cancel)

        if result != QMessageBox.Ok:
            return

        for path in paths:
            if os.path.exists(path):
                if os.path.isfile(path):
                    os.remove(path)
                else:
                    shutil.rmtree(path)

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
        menu.addSeparator()

        delete_action = menu.addAction("Delete")
        delete_action.triggered.connect(lambda: self.delete_item([index]))

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
