import datetime
import logging
import os

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from gui.template_view.info_view.base import InfoView
from settings import settings

logger = logging.getLogger(__name__)



class HistoryInfoView(QTreeWidget, InfoView):
    def __init__(self, parent=None):
        super().__init__(parent=parent, name="History")
        self.setExpandsOnDoubleClick(False)
        self.setColumnCount(4)
        self.setHeaderLabels(["Name", "Date Added", "Path", "Note"])
        self.read_settings()
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.prepare_menu)
        self.itemActivated.connect(self.open_file)
        qApp.aboutToQuit.connect(self.save_state)

    def init(self, widget):
        max_items = 50
        self.clear()
        for i, file in enumerate(reversed(widget.added_files)):
            if i == max_items:
                break
            item_widget = QTreeWidgetItem()
            self.addTopLevelItem(item_widget)
            self.setup_widget(widget, item_widget, file["path"], file["timestamp"])
            item_widget.setText(3, "Added New File")
            if "old_path" in file:
                item_widget.setText(3, "Replaced File")
                child = QTreeWidgetItem()
                self.setup_widget(widget, child, file["old_path"])
                item_widget.addChild(child)
                child.setText(3, "Old File")

    def setup_widget(self, widget, item, path, timestamp=None):
        file_info = QFileInfo(path)
        item.path = path
        item.setExpanded(False)
        item.setText(0, file_info.fileName())
        item.setIcon(0, QFileIconProvider().icon(file_info))
        if timestamp is not None:
            item.setText(1, str(datetime.datetime.fromtimestamp(timestamp)))

        read_path = path
        if widget.template_node.base_path is not None:
            read_path = path.split(widget.template_node.base_path)[-1]
        item.setText(2, os.path.dirname(read_path))

    def update_view(self, selected_widget):
        self.init(selected_widget)

    def open_file(self, item, column=None):
        url = QUrl.fromLocalFile(item.path)
        QDesktopServices.openUrl(url)

    def open_folder(self, item, column=None):
        url = QUrl.fromLocalFile(os.path.dirname(item.path))
        QDesktopServices.openUrl(url)

    def prepare_menu(self, point):
        item = self.itemAt(point)
        if item is None:
            return

        menu = QMenu(self)

        open_file_action = menu.addAction("Open File")
        open_file_action.triggered.connect(lambda: self.open_file(item))
        open_folder_action = menu.addAction("Open Folder")
        open_folder_action.triggered.connect(lambda: self.open_folder(item))

        menu.exec_(self.mapToGlobal(point))

    def save_state(self):
        qsettings = QSettings("eth-document-fetcher", "eth-document-fetcher")
        qsettings.setValue("infoActivityView/geometry", self.header().saveGeometry())
        qsettings.setValue("infoActivityView/windowState", self.header().saveState())

    def read_settings(self):
        qsettings = QSettings("eth-document-fetcher", "eth-document-fetcher")
        if qsettings.value("infoActivityView/geometry") is not None:
            self.header().restoreGeometry(qsettings.value("infoActivityView/geometry"))
        if qsettings.value("infoActivityView/windowState") is not None:
            self.header().restoreState(qsettings.value("infoActivityView/windowState"))
