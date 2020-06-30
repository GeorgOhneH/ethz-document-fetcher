import logging
import os
import traceback
import yaml

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from gui.template_edit.view_tree import TemplateEditViewTree

logger = logging.getLogger(__name__)


class TemplateEditDialog(QDialog):
    def __init__(self, parent, template_path, template_path_settings):
        super().__init__(parent=parent)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setWindowTitle("Edit")
        self.setWindowModality(Qt.ApplicationModal)
        self.template_path_settings = template_path_settings
        self.is_new = template_path is None
        self.finished.connect(self.save_geometry)

        self.button_box = QDialogButtonBox()
        self.save_btn = self.button_box.addButton("Save", QDialogButtonBox.AcceptRole)
        self.save_as_btn = self.button_box.addButton("Save As...", QDialogButtonBox.AcceptRole)
        self.cancel_btn = self.button_box.addButton(QDialogButtonBox.Cancel)
        self.button_box.clicked.connect(self.save_and_exit)
        self.button_box.rejected.connect(self.exit)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.template_view = TemplateEditViewTree(template_path=template_path, parent=self)
        self.template_dict = None

        self.layout.addWidget(self.template_view)
        self.layout.addWidget(self.button_box)

    def open(self):
        self.read_settings()
        super().open()

    def save_and_exit(self, button):
        if button is self.cancel_btn:
            return

        template_dict = self.template_view.convert_to_dict()

        if self.is_new or not os.path.isabs(self.template_path_settings.template_path) or button is self.save_as_btn:
            if os.path.isabs(self.template_path_settings.template_path):
                directory = os.path.dirname(self.template_path_settings.template_path)
            else:
                directory = QStandardPaths.writableLocation(QStandardPaths.DesktopLocation)

            path = QFileDialog.getSaveFileName(
                parent=self,
                caption="Save File",
                directory=directory,
                filter=" ".join([f"*.{extension}" for extension
                                 in self.template_path_settings['template_path'].file_extensions])
            )[0]
        elif button is self.save_btn:
            path = self.template_path_settings.template_path
        else:
            raise ValueError

        with open(path, "w+") as f:
            f.write(yaml.dump(template_dict))

        try:
            self.template_path_settings.template_path = path
        except ValueError:
            os.remove(path)
            error_dialog = QErrorMessage(self)
            error_dialog.setWindowTitle("Error")
            error_dialog.showMessage(f"{path} has not the right file format.")
            return

        self.template_path_settings.save()

        self.accept()

    def exit(self):
        self.reject()

    def closeEvent(self, event):
        self.save_geometry()
        super().closeEvent(event)

    def save_geometry(self):
        qsettings = QSettings("eth-document-fetcher", "eth-document-fetcher")
        qsettings.setValue("templateEditDialog/geometry", self.saveGeometry())

    def read_settings(self):
        qsettings = QSettings("eth-document-fetcher", "eth-document-fetcher")
        if qsettings.value("templateEditDialog/geometry") is not None:
            self.restoreGeometry(qsettings.value("templateEditDialog/geometry"))
