import logging

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from gui.template_view.info_view.base import InfoView
from settings.config_objs import ConfigDict

logger = logging.getLogger(__name__)


class GroupBox(QGroupBox):
    def __init__(self, title, parent=None):
        super().__init__(title, parent=parent)

    def update_content(self, selected_widget):
        pass

    @staticmethod
    def value_to_string(value):
        if value is None:
            return ""
        if isinstance(value, (list, set)):
            value = "[" + " ".join(value) + "]"
        return f"{value}"


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
            label = QLabel(f"{key}: {self.value_to_string(value)}")
            self.layout.addWidget(label)

    def set_attributes(self, attributes):
        for i, (key, value) in enumerate(attributes):
            label = self.layout.itemAt(i).widget()
            label.setText(f"{key}: {self.value_to_string(value)}")

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

    def reset_widget(self):
        for i in range(self.layout.count()):
            label = self.layout.itemAt(i).widget()
            label.hide()

    def update_content(self, selected_widget):
        self.make_layout(selected_widget.template_node.get_configs())

    def make_layout(self, configs):
        self._update_layout(configs, self.layout)

    def _update_layout(self, config_objs, layout):
        active_config_objs = list(filter(lambda x: x.is_active(), config_objs))
        for i, config_obj in enumerate(active_config_objs):
            layout_item = layout.itemAt(i)

            if layout_item is not None:
                if not isinstance(config_obj, ConfigDict) and isinstance(layout_item.widget(), QLabel):
                    layout_item.widget().setText(f"{config_obj.get_gui_name()}:"
                                                 f" {self.value_to_string(config_obj.get())}")
                    continue
                elif isinstance(config_obj, ConfigDict) and isinstance(layout_item.widget(), GroupBox):
                    layout_item.widget().setTitle(config_obj.get_gui_name())
                    self._update_layout(config_obj.layout.values(), layout_item.widget().layout())
                    continue

                child = layout.takeAt(i)
                child.widget().setParent(None)

            if not isinstance(config_obj, ConfigDict):
                widget = QLabel(f"{config_obj.get_gui_name()}: {self.value_to_string(config_obj.get())}")
            else:
                widget = QGroupBox()
                widget.setTitle(config_obj.get_gui_name())
                widget.setLayout(QVBoxLayout())
                self._update_layout(config_obj.layout.values(), widget.layout())

            layout.insertWidget(i, widget)

        while layout.count() > len(active_config_objs):
            child = layout.takeAt(len(active_config_objs))
            if child is not None:
                child.widget().setParent(None)


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
