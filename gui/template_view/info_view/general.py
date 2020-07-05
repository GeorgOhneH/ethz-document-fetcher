import logging

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from gui.template_view.info_view.base import InfoView

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
        if isinstance(value, (list, set)):
            value = "[" + " ".join(value) + "]"
        return f"{key}: {value}"


class GeneralGroupBox(GroupBox):
    def __init__(self, title, parent):
        super().__init__(title, parent=parent)
        self.layout = QVBoxLayout()
        self.layout.setAlignment(Qt.AlignTop)
        self.setLayout(self.layout)
        self.default_attributes = [
            ("Name", None),
            ("Type", None),
            ("State", None),
            ("Path", None),
            ("Selected", None),
            ("Children", None),
        ]
        self.init()

    def init(self):
        for key, value in self.default_attributes:
            label = QLabel(self.key_value_to_string(key, value))
            self.layout.addWidget(label)

    def set_attributes(self, attributes):
        for i, (key, value) in enumerate(attributes):
            label = self.layout.itemAt(i).widget()
            label.setText(self.key_value_to_string(key, value))

    def reset_widget(self):
        self.set_attributes(self.default_attributes)

    def update_content(self, selected_widget):
        attributes = [
            ("Name", selected_widget.template_node.get_gui_name()),
            ("Type", selected_widget.template_node.__class__.__name__),
            ("State", selected_widget.state_text()),
            ("Path", selected_widget.template_node.base_path),
            ("Selected", "No" if selected_widget.get_check_state() == Qt.Unchecked else "Yes"),
            ("Children", len(selected_widget.template_node.children)),
        ]
        self.set_attributes(attributes)


class OptionsGroupBox(GroupBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.layout = QVBoxLayout()
        self.layout.setAlignment(Qt.AlignTop)
        self.setLayout(self.layout)
        self.make_layout([])

    def reset_widget(self):
        for i in range(self.layout.count()):
            label = self.layout.itemAt(i).widget()
            label.hide()

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
    def __init__(self, controller, parent=None):
        super().__init__(parent=parent, name="General", controller=controller)
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

    def reset_widget(self):
        self.general.reset_widget()
        self.options.reset_widget()
