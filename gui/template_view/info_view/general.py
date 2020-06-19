import datetime
import logging
import os

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from gui.template_view.info_view.base import InfoView
from settings import settings

logger = logging.getLogger(__name__)


class GroupBox(QGroupBox):
    def __init__(self, title, parent=None):
        super().__init__(title, parent=parent)

    def update_content(self, selected_widget):
        pass

    @staticmethod
    def key_value_to_string(key, value):
        if value is None:
            return f"{key}: "
        return f"{key}: {value}"


class GeneralGroupBox(GroupBox):
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
            ("Name", selected_widget.template_node.get_gui_name()),
            ("Type", selected_widget.template_node.__class__.__name__),
            ("State", selected_widget.state_text()),
            ("Path", selected_widget.template_node.base_path),
            ("Sub-Folder", bool(selected_widget.template_node.folder)),
            ("Sub-Sites", len(selected_widget.template_node.sites)),
        ]
        for i, (key, value) in enumerate(attributes):
            label = self.layout.itemAt(i).widget()
            label.setText(self.key_value_to_string(key, value))


class OptionsGroupBox(GroupBox):
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


class GeneralInfoView(QScrollArea, InfoView):
    def __init__(self, parent=None):
        super().__init__(parent=parent, name="General")
        self.setWidgetResizable(True)
        self.main_widget = QWidget()
        self.main_widget.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.grid = QGridLayout()
        self.main_widget.setLayout(self.grid)
        self.general = GeneralGroupBox(title="General", parent=self)
        self.options = OptionsGroupBox(title="Options", parent=self)
        self.grid.addWidget(self.general, 0, 0)
        self.grid.addWidget(self.options, 0, 1)
        self.setWidget(self.main_widget)

    def update_view(self, selected_widget):
        self.general.update_content(selected_widget)
        self.options.update_content(selected_widget)
