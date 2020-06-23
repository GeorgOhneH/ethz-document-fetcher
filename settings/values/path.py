import base64
import logging
import os
import time

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from settings.constants import ROOT_PATH
from settings.values.string import ConfigString, LineEdit

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

    if current_path is not None and os.path.exists(current_path):
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
        self.file_button.pressed.connect(self.open_file_picker)
        self.layout.addWidget(self.file_button)

    def open_file_picker(self):
        file_name = open_file_picker(self.only_folder, self.file_extensions, self.get_value())
        if file_name is not None:
            self.line_edit.setText(QDir.toNativeSeparators(file_name))


class ConfigPath(ConfigString):
    def __init__(self, absolute=True, ony_folder=False, file_extensions=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.absolute = absolute
        self.file_extensions = file_extensions
        self.only_folder = ony_folder

    def init_widget(self):
        return PathLineEdit(self, self.only_folder, self.file_extensions)

    def _test(self, value):
        if self.absolute or os.path.isabs(value):
            if not os.path.isabs(value):
                self.msg = "Not an absolute path"
                return False
            path = value
        else:
            path = os.path.join(ROOT_PATH, value)

        if not os.path.exists(path):
            self.msg = "Path does not exist or is not valid"
            return False
        if self.only_folder and not os.path.isdir(path):
            self.msg = "Must be a folder"
            return False
        if self.file_extensions is not None:
            if not os.path.isfile(path):
                self.msg = "Path must be a file"
                return False
            if "." not in path:
                self.msg = "File must have a extension"
                return False
            if path.split(".")[-1] not in self.file_extensions:
                self.msg = f"File extension must be one of these: ({' '.join(self.file_extensions)})"
                return False

        return True
