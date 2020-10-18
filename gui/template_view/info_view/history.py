import datetime
import logging
import os

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from gui.template_view.info_view.base import InfoView
from gui.utils import format_bytes, widget_read_settings, widget_save_settings

logger = logging.getLogger(__name__)


def get_values_sorted_after_key(d: dict):
    return [value for key, value in sorted(d.items(), key=lambda k_v: k_v[0])]


class LazyStandardItemModel(QStandardItemModel):
    COLUMN_NAME = 0
    COLUMN_SIZE = 1
    COLUMN_DATE = 2
    COLUMN_PATH = 3
    COLUMN_NOTE = 4

    def __init__(self, widget=None):
        super().__init__()
        self.setColumnCount(5)
        self.setHorizontalHeaderLabels(["Name", "Size", "Date Added", "Path", "Note"])
        self.model_data = None
        self.widget = None
        if widget is not None:
            self._init(widget)

    def _init(self, widget):
        self.model_data = list(reversed(widget.load_from_cache("added_files")))
        self.widget = widget

    def set_widget(self, widget):
        if widget is self.widget:
            self.update_data()
            return
        self._init(widget)
        self.clear_rows()
        self.fetchMore()

    def clear_rows(self):
        self.removeRows(0, self.rowCount())

    def reset(self):
        self.clear_rows()
        self.widget = None
        self.model_data = None

    def update_data(self):
        root = self.invisibleRootItem()
        first_old_file = None
        if len(self.model_data) != 0:
            first_old_file = self.model_data[0]
        new_data = list(reversed(self.widget.load_from_cache("added_files")))
        items_list = []
        for new_file in new_data:
            if new_file == first_old_file:
                break
            items = self.get_items(new_file)
            items_list.append(items)

        for items in reversed(items_list):
            root.insertRow(0, items)

        self.model_data = new_data

    def canFetchMore(self, parent: QModelIndex):
        if self.model_data is None:
            return False
        if parent.isValid():  # only root
            return False
        root = self.invisibleRootItem()
        return root.rowCount() < len(self.model_data)

    def fetchMore(self, parent: QModelIndex = None):
        if self.model_data is None:
            return
        root = self.invisibleRootItem()
        for _ in range(5):
            if root.rowCount() >= len(self.model_data):
                return
            file = self.model_data[root.rowCount()]
            items = self.get_items(file)
            root.appendRow(items)

    def get_items(self, file):
        items = self.prepare_items(path=file["path"], timestamp=file["timestamp"])
        items[self.COLUMN_NOTE] = QStandardItem("Added New File")
        if "old_path" in file:
            items[self.COLUMN_NOTE] = QStandardItem("Replaced File")
            if file["old_path"] is None:
                return
            children = self.prepare_items(path=file["old_path"])
            children[self.COLUMN_NOTE] = QStandardItem("Old File")
            items[0].appendRow(get_values_sorted_after_key(children))
        return get_values_sorted_after_key(items)

    def prepare_items(self, path, timestamp=None):
        items = {}
        file_info = QFileInfo(path)
        items[self.COLUMN_NAME] = QStandardItem(QFileIconProvider().icon(file_info),
                                                file_info.fileName())

        column_size_item = QStandardItem(format_bytes(file_info.size()))
        column_size_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        items[self.COLUMN_SIZE] = column_size_item

        timestamp_string = ""
        if timestamp is not None:
            timestamp_string = QStandardItem(str(datetime.datetime.fromtimestamp(timestamp)))
        items[self.COLUMN_DATE] = QStandardItem(timestamp_string)

        read_path = path
        if self.widget.template_node.base_path is not None:
            read_path = path.split(self.widget.template_node.base_path)[-1]
        items[self.COLUMN_PATH] = QStandardItem(os.path.dirname(read_path))
        items[self.COLUMN_PATH].path = path
        return items


class HistoryInfoView(QTreeView, InfoView):
    def __init__(self, controller, parent=None):
        super().__init__(parent=parent, name="History", controller=controller)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setExpandsOnDoubleClick(False)
        self.model = LazyStandardItemModel()
        self.setModel(self.model)
        self.read_settings()
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.prepare_menu)
        self.activated.connect(self.open_file)
        qApp.aboutToQuit.connect(self.save_state)

    def init(self, widget):
        if self.model.widget is not widget:
            self.scrollToTop()
        self.model.set_widget(widget)

    def reset_widget(self):
        self.model.reset()

    def update_view(self, selected_widget):
        self.init(selected_widget)

    def open_file(self, index):
        path_index = index.siblingAtColumn(self.model.COLUMN_PATH)
        path = self.model.itemFromIndex(path_index).path

        url = QUrl.fromLocalFile(path)
        QDesktopServices.openUrl(url)

    def open_folder(self, index):
        path_index = index.siblingAtColumn(self.model.COLUMN_PATH)
        path = self.model.itemFromIndex(path_index).path
        url = QUrl.fromLocalFile(os.path.dirname(path))
        QDesktopServices.openUrl(url)

    def prepare_menu(self, point):
        index = self.indexAt(point)
        if not index.isValid():
            return

        menu = QMenu(self)

        open_file_action = menu.addAction("Open File")
        open_file_action.triggered.connect(lambda: self.open_file(index))
        open_folder_action = menu.addAction("Open Folder")
        open_folder_action.triggered.connect(lambda: self.open_folder(index))

        menu.exec_(self.mapToGlobal(point))

    def save_state(self):
        widget_save_settings(self.header(), name="infoActivityViewHeader")

    def read_settings(self):
        widget_read_settings(self.header(), name="infoActivityViewHeader")
