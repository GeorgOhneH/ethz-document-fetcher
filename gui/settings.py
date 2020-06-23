import logging

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from settings import global_settings

logger = logging.getLogger(__name__)


class ErrorLabel(QWidget):
    data_changed_signal = pyqtSignal()

    def __init__(self, config_widget, parent=None):
        super().__init__(parent=parent)
        self.config_widget = config_widget
        self.config_widget.data_changed_signal.connect(self.data_changed)

        self.error_label = QLabel()
        self.error_label.setStyleSheet("QLabel { color : red; }")
        if not self.set_error_msg():
            self.error_label.hide()

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.setLayout(self.layout)
        self.layout.addWidget(self.config_widget)
        self.layout.addWidget(self.error_label)

    def set_error_msg(self):
        value = self.config_widget.get_value()
        if self.config_widget.config_obj.is_valid(value):
            return False
        msg = self.config_widget.config_obj.msg
        self.error_label.setText(msg)
        return True

    def data_changed(self, *args, **kwargs):
        if self.set_error_msg():
            self.error_label.show()
        else:
            self.error_label.hide()
        self.data_changed_signal.emit()


class SettingsDialog(QDialog):
    def __init__(self, parent, site_settings):
        super().__init__(parent=parent)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setModal(True)
        self.setWindowTitle("Settings")
        self.finished.connect(self.save_geometry)

        self.settings_areas = [
            SettingScrollArea(site_settings, parent=self),
            SettingScrollArea(global_settings, save_changes=False, parent=self),
        ]

        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("QTabWidget::pane { border: none; }")

        for settings_area in self.settings_areas:
            settings_area.data_changed_signal.connect(self.data_changed)
            self.tab_widget.addTab(settings_area, settings_area.settings.NAME)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.layout.addWidget(self.tab_widget)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.save_and_exit)
        self.button_box.rejected.connect(self.exit)
        self.layout.addWidget(self.button_box)
        self.init_widgets()

    def open(self):
        self.update_widgets()
        self.read_settings()
        super(SettingsDialog, self).open()

    def init_widgets(self):
        for settings_area in self.settings_areas:
            settings_area.init_widgets()

    def update_widgets(self):
        for settings_area in self.settings_areas:
            settings_area.update_widgets()

    def save_and_exit(self):
        if not self.settings_are_valid():
            return
        for settings_area in self.settings_areas:
            settings_area.apply_value()
        self.accept()

    def exit(self):
        self.reject()

    def settings_are_valid(self):
        for settings_area in self.settings_areas:
            if not settings_area.is_valid():
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
        qsettings = QSettings("eth-document-fetcher", "eth-document-fetcher")
        qsettings.setValue("settingsDialog/geometry", self.saveGeometry())

    def read_settings(self):
        qsettings = QSettings("eth-document-fetcher", "eth-document-fetcher")
        if qsettings.value("settingsDialog/geometry") is not None:
            self.restoreGeometry(qsettings.value("settingsDialog/geometry"))


class SettingScrollArea(QScrollArea):
    data_changed_signal = pyqtSignal()

    def __init__(self, settings, save_changes=True, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)

        self.main_widget = QWidget()
        self.main_widget.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

        self.settings = settings
        self.save_changes = save_changes

        self.required = QGroupBox()
        self.required.setTitle("General" + (" (Requires Restart)" if not save_changes else ""))
        self.required.setLayout(QVBoxLayout())
        self.optional = QGroupBox()
        self.optional.setTitle("Optional" + (" (Requires Restart)" if not save_changes else ""))
        self.optional.setLayout(QVBoxLayout())

        self.layout = QVBoxLayout()
        self.main_widget.setLayout(self.layout)
        self.layout.addWidget(self.required)
        self.layout.addWidget(self.optional)

        self.setWidget(self.main_widget)

    def init_widgets(self):
        for value in self.settings:
            widget = value.get_widget()
            label = ErrorLabel(widget, parent=self)
            label.data_changed_signal.connect(self.data_changed)
            if value.optional:
                self.optional.layout().addWidget(label)
            else:
                self.required.layout().addWidget(label)

        if self.optional.layout().count() == 0:
            self.optional.hide()
        if self.required.layout().count() == 0:
            self.required.hide()

    def update_widgets(self):
        if not self.save_changes:
            return
        for value in self.settings:
            value.update_widget()

    def is_valid(self):
        for value in self.settings:
            if not value.is_valid_from_widget():
                return False
        return True

    def apply_value(self):
        if not self.save_changes:
            return
        for value in self.settings:
            value.set_from_widget()
        self.settings.save()

    def data_changed(self):
        self.data_changed_signal.emit()
