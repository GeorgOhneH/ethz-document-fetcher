from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


class SettingsWidget(QDialog):
    def __init__(self, parent, site_settings):
        super().__init__(parent=parent)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setModal(True)
        self.setWindowTitle("Settings")
        self.site_settings = site_settings

        self.required = QGroupBox()
        self.required.setTitle("Required")
        self.required.setLayout(QVBoxLayout())
        self.optional = QGroupBox()
        self.optional.setTitle("Optional")
        self.optional.setLayout(QVBoxLayout())

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.layout.addWidget(self.required)
        self.layout.addWidget(self.optional)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.save_and_exit)
        self.button_box.rejected.connect(self.exit)
        self.layout.addWidget(self.button_box)
        self.init_widgets()

    def open(self):
        self.update_widgets()
        super(SettingsWidget, self).open()

    def init_widgets(self):
        for value in self.site_settings:
            widget = value.get_widget()
            if value.optional:
                self.optional.layout().addWidget(widget)
            else:
                self.required.layout().addWidget(widget)

    def update_widgets(self):
        for value in self.site_settings:
            value.update_widget()

    def save_and_exit(self):
        for value in self.site_settings:
            if not value.is_valid_from_widget():
                return

        for value in self.site_settings:
            value.set_from_widget()
        self.site_settings.save()
        self.accept()

    def exit(self):
        self.reject()

