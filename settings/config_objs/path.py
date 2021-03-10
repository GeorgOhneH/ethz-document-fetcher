import logging
import os

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from core import utils
from gui.constants import ROOT_PATH
from settings.config_objs.string import ConfigString, LineEdit

logger = logging.getLogger(__name__)


def open_file_picker(only_folder=False, file_extensions=None, current_path=None):
    file_dialog = QFileDialog()
    if only_folder:
        file_dialog.setFileMode(QFileDialog.Directory)
        file_dialog.setOption(QFileDialog.ShowDirsOnly)
    elif file_extensions is not None:
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setNameFilter(" ".join([f"*.{extension}" for extension in file_extensions]))
    file_dialog.setViewMode(QFileDialog.Detail)

    if current_path is not None and\
            os.path.exists(current_path) and\
            os.path.normcase(ROOT_PATH) not in os.path.normcase(current_path):
        file_dialog.setDirectory(current_path)
    else:
        file_dialog.setDirectory(QStandardPaths.writableLocation(QStandardPaths.DesktopLocation))

    file_name = None
    if file_dialog.exec():
        file_names = file_dialog.selectedFiles()
        if file_names is not None:
            file_name = file_names[0]
    if file_name is not None:
        return QDir.toNativeSeparators(file_name)
    else:
        return None


class PathLineEdit(LineEdit):
    def __init__(self, config_obj, only_folder, file_extensions):
        super().__init__(config_obj)
        self.only_folder = only_folder
        self.file_extensions = file_extensions
        self.file_button = QPushButton()
        self.file_button.setIcon(QFileIconProvider().icon(QFileIconProvider.Folder))
        self.file_button.clicked.connect(self.open_file_picker)
        self.layout.addWidget(self.file_button)

    def open_file_picker(self):
        file_name = open_file_picker(self.only_folder, self.file_extensions, self.get_value())
        if file_name is not None:
            self.line_edit.setText(QDir.toNativeSeparators(file_name))
        self.file_button.clearFocus()


class ConfigPath(ConfigString):
    def __init__(self, only_folder=False, file_extensions=None, *args, **kwargs):
        self.file_extensions = file_extensions
        self.only_folder = only_folder
        super().__init__(*args, **kwargs)

    def init_widget(self):
        return PathLineEdit(self, self.only_folder, self.file_extensions)

    def _test(self, path, from_widget):
        if not os.path.isabs(path):
            raise ValueError("Not an absolute path")

        if not os.path.exists(path):
            raise ValueError("Path does not exist or is not valid")

        if self.only_folder and not os.path.isdir(path):
            raise ValueError("Must be a folder")

        if self.file_extensions is not None:
            if not os.path.isfile(path):
                raise ValueError("Path must be a file")

            if "." not in path:
                raise ValueError("File must have an extension")

            if utils.get_extension(path) not in self.file_extensions:
                raise ValueError(f"File extension must be one of these: ({', '.join(self.file_extensions)})")

