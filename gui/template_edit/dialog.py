import logging
import os

import yaml
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

import gui
import gui.utils
from gui.constants import ROOT_PATH
from gui.template_edit.view_tree import TemplateEditViewTree

logger = logging.getLogger(__name__)


class TemplateEditDialog(QDialog):
    def __init__(self, parent, template_path):
        super().__init__(parent=parent, flags=Qt.Window)
        self.setWindowTitle("Edit")
        self.setWindowModality(Qt.ApplicationModal)

        self.button_box = QDialogButtonBox()
        self.save_btn = self.button_box.addButton("Save", QDialogButtonBox.YesRole)
        self.save_as_btn = self.button_box.addButton("Save As...", QDialogButtonBox.YesRole)
        self.cancel_btn = self.button_box.addButton(QDialogButtonBox.Cancel)

        # remove focus so you can press enter, without closing the dialog
        for button in self.button_box.buttons():
            button.setAutoDefault(False)
            button.setDefault(False)

        self.button_box.clicked.connect(self.save_and_exit)
        self.button_box.rejected.connect(self.exit)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.template_view = TemplateEditViewTree(template_path=template_path, parent=self)

        self.layout.addWidget(self.template_view)
        self.layout.addWidget(self.button_box)

        self.finished.connect(self.save_geometry)
        self.finished.connect(self.template_view.save_state)

        app = gui.Application.instance()
        self.accepted.connect(lambda: app.edit_saved.emit())

        self.is_new = template_path is None

    def reset_template(self, template_path):
        self.is_new = template_path is None
        self.template_view.reset_template(template_path=template_path)

    def open(self):
        self.read_settings()
        super().open()
        # to remove focus the the treewidget
        self.save_btn.setFocus()

    def save_and_exit(self, button):
        if button is self.cancel_btn:
            return

        template_dict = self.template_view.convert_to_dict()

        template_path_settings = gui.Application.instance().template_path_settings

        path = template_path_settings.template_path
        if self.is_new or \
                os.path.normcase(ROOT_PATH) in os.path.normcase(path) or \
                button is self.save_as_btn:

            if os.path.normcase(ROOT_PATH) not in os.path.normcase(path):
                directory = os.path.dirname(path)
            else:
                directory = QStandardPaths.writableLocation(QStandardPaths.DesktopLocation)

            path = QFileDialog.getSaveFileName(
                parent=self,
                caption="Save File",
                directory=directory,
                filter=" ".join([f"*.{extension}" for extension
                                 in template_path_settings['template_path'].file_extensions])
            )[0]

        if not path:
            return

        path = os.path.normcase(path)
        if os.path.normcase(ROOT_PATH) in path:
            error_dialog = QErrorMessage(self)
            error_dialog.setWindowTitle("Error")
            error_dialog.showMessage(f"Saving file in the installation folder is not allowed")
            error_dialog.raise_()
            return

        try:
            with open(path, "w+") as f:
                f.write(yaml.dump(template_dict))
        except Exception as e:
            error_dialog = QErrorMessage(self)
            error_dialog.setWindowTitle("Error")
            error_dialog.showMessage(f"Could not save your file. {e}")
            error_dialog.raise_()
            return

        try:
            template_path_settings.template_path = path
        except ValueError:
            os.remove(path)
            error_dialog = QErrorMessage(self)
            error_dialog.setWindowTitle("Error")
            error_dialog.showMessage(f"{path} has not the right file format.")
            error_dialog.raise_()
            return

        template_path_settings.save()

        self.accept()

    def exit(self):
        self.reject()

    def closeEvent(self, event):
        self.save_geometry()
        self.template_view.save_state()
        super().closeEvent(event)

    def save_geometry(self):
        gui.utils.widget_save_settings(self, save_state=False)

    def read_settings(self):
        self.resize(600, 500)
        gui.utils.widget_read_settings(self, save_state=False)
