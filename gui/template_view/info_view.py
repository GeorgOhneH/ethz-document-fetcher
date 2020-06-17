import os
import logging
from collections import OrderedDict

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

from settings import settings

logger = logging.getLogger(__name__)


class InfoView(object):
    def __init__(self, name):
        self.name = name
        self.button = QPushButton(name)
        self.button.setCheckable(True)

    def detect_change_selected(self, selected_widget, old_widget):
        selected_widget.signals.data_changed.connect(self.update_view)
        if old_widget is not None:
            old_widget.signals.data_changed.disconnect(self.update_view)
        self.update_view(selected_widget)

    def update_view(self, selected_widget):
        pass


class InfoGroupBox(QGroupBox):
    def __init__(self, title, parent=None):
        super().__init__(title, parent=parent)

    def update_content(self, selected_widget):
        pass

    @staticmethod
    def key_value_to_string(key, value):
        if value is None:
            return f"{key}: "
        return f"{key}: {value}"


class InfoGroupBoxGeneral(InfoGroupBox):
    def __init__(self, title, parent):
        super().__init__(title, parent=parent)
        self.layout = QVBoxLayout()
        self.layout.setAlignment(Qt.AlignTop)
        self.setLayout(self.layout)
        attributes = [
            ("Name", None),
            ("Type", None),
            ("State", None),
            ("Path", None),
            ("Sub-Folder", None),
            ("Sub-Sites", None),
        ]

        for key, value in attributes:
            label = QLabel(self.key_value_to_string(key, value))
            self.layout.addWidget(label)

    def update_content(self, selected_widget):
        attributes = [
            ("Name", selected_widget.template_node.gui_name()),
            ("Type", selected_widget.template_node.__class__.__name__),
            ("State", selected_widget.state),
            ("Path", selected_widget.template_node.base_path),
            ("Sub-Folder", bool(selected_widget.template_node.folder)),
            ("Sub-Sites", len(selected_widget.template_node.sites)),
        ]
        for i, (key, value) in enumerate(attributes):
            label = self.layout.itemAt(i).widget()
            label.setText(f"{key}: {value}")


class InfoGroupBoxOptions(InfoGroupBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.layout = QVBoxLayout()
        self.layout.setAlignment(Qt.AlignTop)
        self.setLayout(self.layout)
        self.make_layout([])

    def update_content(self, selected_widget):
        self.make_layout(selected_widget.template_node.gui_options())

    def make_layout(self, attributes):
        for i, (key, value) in enumerate(attributes):
            item = self.layout.itemAt(i)
            text = self.key_value_to_string(key, value)
            if item is None:
                label = QLabel(self.key_value_to_string(key, value))
                self.layout.addWidget(label)
            else:
                label = item.widget()
                label.setText(text)
                label.show()
        for i in range(len(attributes), self.layout.count()):
            label = self.layout.itemAt(i).widget()
            label.hide()


class InfoGeneralView(QScrollArea, InfoView):
    def __init__(self, parent=None):
        super().__init__(parent=parent, name="General")
        self.setWidgetResizable(True)
        self.main_widget = QWidget()
        self.main_widget.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.grid = QGridLayout()
        self.main_widget.setLayout(self.grid)
        self.general = InfoGroupBoxGeneral(title="General", parent=self)
        self.options = InfoGroupBoxOptions(title="Options", parent=self)
        self.grid.addWidget(self.general, 0, 0)
        self.grid.addWidget(self.options, 0, 1)
        self.setWidget(self.main_widget)

    def update_view(self, selected_widget):
        self.general.update_content(selected_widget)
        self.options.update_content(selected_widget)


class InfoFolderView(QTreeView, InfoView):
    def __init__(self, parent=None):
        super().__init__(parent=parent, name="Folder")
        self.model = QFileSystemModel()
        self.setModel(self.model)

    def change_root(self, path):
        index = self.model.setRootPath(path)
        self.setRootIndex(index)

    def update_view(self, selected_widget):
        path = selected_widget.template_node.base_path
        if path is not None:
            absolute_path = os.path.join(settings.base_path, path)
            self.change_root(absolute_path)
