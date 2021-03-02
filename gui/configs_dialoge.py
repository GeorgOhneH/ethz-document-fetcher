import logging
import time

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from gui.utils import widget_save_settings, widget_read_settings

logger = logging.getLogger(__name__)


class ConfigsDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent=parent)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setModal(True)
        self.finished.connect(self.save_geometry)
        self.rejected.connect(self.cancel)

        self.configs_areas = None
        self.layout = None
        self.button_box = None

    def init(self, configs_areas):
        self.configs_areas = configs_areas

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        if len(self.configs_areas) != 1:
            tab_widget = QTabWidget()
            tab_widget.setStyleSheet("QTabWidget::pane { border: none; }")

            for configs_area in self.configs_areas:
                configs_area.data_changed_signal.connect(self.data_changed)
                tab_widget.addTab(configs_area, configs_area.configs.NAME)

            self.layout.addWidget(tab_widget)

        else:
            self.configs_areas[0].data_changed_signal.connect(self.data_changed)
            self.layout.addWidget(self.configs_areas[0])

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.save_and_exit)
        self.button_box.rejected.connect(self.exit)
        self.layout.addWidget(self.button_box)
        self.init_widgets()
        self.data_changed()

    def _show_or_open_or_exec(self):
        self.reset_widgets()
        self.update_visibility()
        self.read_settings()

    def open(self):
        self._show_or_open_or_exec()
        super().open()

    def exec(self):
        self._show_or_open_or_exec()
        super().exec()

    def show(self):
        self._show_or_open_or_exec()
        super().show()

    def init_widgets(self):
        for configs_area in self.configs_areas:
            configs_area.init_widgets()

    def reset_widgets(self):
        for configs_area in self.configs_areas:
            configs_area.reset_widgets()

    def update_visibility(self):
        for configs_area in self.configs_areas:
            configs_area.update_visibility()

    def cancel(self):
        for configs_area in self.configs_areas:
            configs_area.cancel()

    def save_and_exit(self):
        if not self.settings_are_valid():
            return
        for configs_area in self.configs_areas:
            configs_area.apply_value()
        self.accept()

    def exit(self):
        self.reject()

    def settings_are_valid(self):
        for configs_area in self.configs_areas:
            if not configs_area.is_valid():
                return False
        return True

    def closeEvent(self, event):
        self.save_geometry()
        super(QDialog, self).closeEvent(event)

    def data_changed(self):
        ok_button = self.button_box.button(QDialogButtonBox.Ok)
        cancel_button = self.button_box.button(QDialogButtonBox.Cancel)
        valid_settings = self.settings_are_valid()
        ok_button.setEnabled(valid_settings)
        cancel_button.setDefault(not valid_settings)
        ok_button.setDefault(valid_settings)

    def save_geometry(self):
        widget_save_settings(self, save_state=False)

    def read_settings(self):
        self.resize(self.sizeHint() + QSize(20, 20))
        widget_read_settings(self, save_state=False)


class ConfigsScrollArea(QScrollArea):
    data_changed_signal = pyqtSignal()

    def __init__(self, configs, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)

        self.main_widget = QWidget()
        self.main_widget.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

        self.configs = configs

        self.required = QGroupBox()
        self.required.setTitle("General")
        self.required.setLayout(QVBoxLayout())
        self.optional = QGroupBox()
        self.optional.setTitle("Optional")
        self.optional.setLayout(QVBoxLayout())

        self.layout = QVBoxLayout()
        self.main_widget.setLayout(self.layout)
        self.layout.addWidget(self.required)
        self.layout.addWidget(self.optional)

        self.setWidget(self.main_widget)

    def init_widgets(self):
        for config_obj in self.configs:
            widget = config_obj.get_widget()
            widget.data_changed_signal.connect(self.data_changed)
            if config_obj.optional:
                self.optional.layout().addWidget(widget)
            else:
                self.required.layout().addWidget(widget)

        for config_obj in self.configs:
            config_obj.update_visibility()
            config_obj.update_widget()

        self.update_group_box_visibility(self.optional)
        self.update_group_box_visibility(self.required)

    @staticmethod
    def update_group_box_visibility(widget):
        for i in range(widget.layout().count()):
            config_widget = widget.layout().itemAt(i).widget()
            if not config_widget.isHidden():
                widget.show()
                return
        widget.hide()

    def reset_widgets(self):
        for config_obj in self.configs:
            config_obj.reset_widget()

    def update_widgets(self):
        for config_obj in self.configs:
            config_obj.update_widget()

    def update_visibility(self):
        for config_obj in self.configs:
            config_obj.update_visibility()

    def cancel(self):
        for config_obj in self.configs:
            config_obj.cancel()

    def is_valid(self):
        for config_obj in self.configs:
            if not config_obj.is_valid_from_widget():
                return False
        return True

    def apply_value(self):
        for config_obj in self.configs:
            config_obj.set_from_widget()

    def data_changed(self):
        self.update_widgets()
        self.update_visibility()
        self.update_group_box_visibility(self.optional)
        self.update_group_box_visibility(self.required)
        self.data_changed_signal.emit()
