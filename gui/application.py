import copy
import logging
import os

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from core.constants import APP_NAME
from gui.actions import Actions
from gui.constants import ALL_THEMES, THEME_NATIVE, THEME_FUSION_DARK, THEME_FUSION_LIGHT
from gui.worker import WorkerThread
from settings import settings
from settings.config_objs.path import open_file_picker

logger = logging.getLogger(__name__)


class Application(QApplication):
    theme_changed = pyqtSignal()
    settings_saved = pyqtSignal()
    edit_opened = pyqtSignal()
    edit_saved = pyqtSignal()
    before_file_open = pyqtSignal()
    file_opened = pyqtSignal(str)

    def __init__(self, argv):
        super().__init__(argv)
        self.setApplicationName(APP_NAME)
        self.behavior_settings = settings.BehaviorSettings()
        self.gui_settings = settings.GUISettings()
        self.download_settings = settings.DownloadSettings()
        self.template_path_settings = settings.TemplatePathSettings()

        self.actions = Actions()

        self.actions.open_file.triggered.connect(lambda: self.open_file())
        self.edit_saved.connect(lambda: self._open_file())

        self.actions.run.triggered.connect(lambda: self.start_thread())
        self.actions.stop.triggered.connect(lambda: self.stop_worker())
        self.actions.stop.setEnabled(False)

        self.worker_thread = WorkerThread()

        self.worker_thread.started.connect(self._thread_started)
        self.worker_thread.finished.connect(self._thread_finished)

        self._current_theme = None
        self.default_palette = self.palette()
        self.default_style = self.style().objectName()

        self.dark_palette = _init_dark_pallet()
        self.light_palette = _init_light_palette()
        self.settings_saved.connect(self.set_current_setting_theme)

    def set_current_setting_theme(self):
        if self.gui_settings.theme:
            self.set_theme(self.gui_settings.theme)

    def start_thread(self, unique_keys=None, recursive=True):
        if unique_keys is None:
            unique_keys = ["root"]

        if not self.download_settings.check_if_valid():
            self.actions.settings.trigger()
            return

        with open(self.get_template_path()) as f:
            count = f.read().count("INSERT PASSWORD")
            if count:
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Warning)
                msg_box.setWindowTitle("Run Confirmation")
                msg_box.setText(f"In this preset template are specific passwords missing")
                msg_box.addButton("Edit Template", QMessageBox.AcceptRole)
                msg_box.addButton("Run Anyway", QMessageBox.NoRole)
                msg_box.setStandardButtons(QMessageBox.Cancel)
                ret = msg_box.exec()
                if ret == QMessageBox.Cancel:
                    return
                if ret == QMessageBox.AcceptRole:
                    self.open_edit()
                    return

        if self.download_settings.force_download:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setWindowTitle("Run Confirmation")
            msg_box.setText("Force Download is enabled.")
            msg_box.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            ret = msg_box.exec()
            if ret == QMessageBox.Cancel:
                return

        self.worker_thread.unique_keys = unique_keys
        self.worker_thread.recursive = recursive
        self.worker_thread.download_settings = copy.deepcopy(self.download_settings)
        self.worker_thread.template_path = self.get_template_path()
        self.worker_thread.start()

    def stop_worker(self):
        self.worker_thread.stop()

    def _thread_started(self):
        self.actions.run.setEnabled(False)
        self.actions.run_checked.setEnabled(False)
        self.actions.stop.setEnabled(True)

    def _thread_finished(self):
        self.actions.run.setEnabled(True)
        self.actions.run_checked.setEnabled(True)
        self.actions.stop.setEnabled(False)

    def open_file(self, file_path=None):
        if file_path is None:
            config_obj = self.template_path_settings.get_config_obj("template_path")
            current_template_path = self.get_template_path()
            file_path = open_file_picker(config_obj.only_folder,
                                         config_obj.file_extensions,
                                         os.path.dirname(current_template_path))
        if file_path is None:
            return

        try:
            self.template_path_settings.template_path = file_path
        except ValueError:
            error_dialog = QErrorMessage()
            error_dialog.setWindowTitle("Error")
            error_dialog.showMessage(f"{file_path} has not the right file format")
            error_dialog.raise_()
            return

        self.template_path_settings.save()
        self.before_file_open.emit()

        self._open_file()

    def _open_file(self):
        if self.worker_thread.isRunning():
            self.worker_thread.finished.connect(self._thread_finished_open_file)
            self.stop_worker()
            return

        self._emit_open_file()

    def _emit_open_file(self):
        try:
            self.worker_thread.finished.disconnect(self._thread_finished_open_file)
        except TypeError:
            pass
        self.file_opened.emit(self.get_template_path())

    def _thread_finished_open_file(self):
        self._emit_open_file()

    def get_template_path(self):
        return self.template_path_settings.template_path

    # IMPORTANT: Set style AFTER palette
    def _to_native(self):
        self.setPalette(self.default_palette)
        self.setStyle(self.default_style)

    def _to_fusion_dark(self):
        self.setPalette(self.dark_palette)
        self.setStyle("Fusion")

    def _to_fusion_light(self):
        self.setPalette(self.light_palette)
        self.setStyle("Fusion")

    def set_theme(self, theme):
        if self._current_theme == theme:
            return

        logger.debug(f"Set Theme: {theme}")

        if theme == THEME_NATIVE:
            self._to_native()
        elif theme == THEME_FUSION_DARK:
            self._to_fusion_dark()
        elif theme == THEME_FUSION_LIGHT:
            self._to_fusion_light()
        else:
            raise ValueError(f"theme must be one of these {ALL_THEMES}, not ({theme})")

        self._current_theme = theme
        self.theme_changed.emit()

    @staticmethod
    def instance() -> 'Application':
        return QApplication.instance()


def _init_dark_pallet():
    dark_palette = QPalette()

    # base
    dark_palette.setColor(QPalette.WindowText, QColor(180, 180, 180))
    dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.Light, QColor(180, 180, 180))
    dark_palette.setColor(QPalette.Midlight, QColor(90, 90, 90))
    dark_palette.setColor(QPalette.Dark, QColor(35, 35, 35))
    dark_palette.setColor(QPalette.Text, QColor(180, 180, 180))
    dark_palette.setColor(QPalette.BrightText, QColor(180, 180, 180))
    dark_palette.setColor(QPalette.ButtonText, QColor(180, 180, 180))
    dark_palette.setColor(QPalette.Base, QColor(42, 42, 42))
    dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.Shadow, QColor(20, 20, 20))
    dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.HighlightedText, QColor(180, 180, 180))
    dark_palette.setColor(QPalette.Link, QColor(56, 252, 196))
    dark_palette.setColor(QPalette.AlternateBase, QColor(66, 66, 66))
    dark_palette.setColor(QPalette.ToolTipBase, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ToolTipText, QColor(180, 180, 180))
    dark_palette.setColor(QPalette.PlaceholderText, QColor(180, 180, 180))

    # disabled
    dark_palette.setColor(QPalette.Disabled, QPalette.WindowText,
                          QColor(127, 127, 127))
    dark_palette.setColor(QPalette.Disabled, QPalette.Text,
                          QColor(127, 127, 127))
    dark_palette.setColor(QPalette.Disabled, QPalette.ButtonText,
                          QColor(127, 127, 127))
    dark_palette.setColor(QPalette.Disabled, QPalette.Highlight,
                          QColor(80, 80, 80))
    dark_palette.setColor(QPalette.Disabled, QPalette.HighlightedText,
                          QColor(127, 127, 127))

    return dark_palette


def _init_light_palette():
    light_palette = QPalette()

    # base
    light_palette.setColor(QPalette.WindowText, QColor(0, 0, 0))
    light_palette.setColor(QPalette.Button, QColor(240, 240, 240))
    light_palette.setColor(QPalette.Light, QColor(180, 180, 180))
    light_palette.setColor(QPalette.Midlight, QColor(200, 200, 200))
    light_palette.setColor(QPalette.Dark, QColor(225, 225, 225))
    light_palette.setColor(QPalette.Text, QColor(0, 0, 0))
    light_palette.setColor(QPalette.BrightText, QColor(0, 0, 0))
    light_palette.setColor(QPalette.ButtonText, QColor(0, 0, 0))
    light_palette.setColor(QPalette.Base, QColor(237, 237, 237))
    light_palette.setColor(QPalette.Window, QColor(240, 240, 240))
    light_palette.setColor(QPalette.Shadow, QColor(20, 20, 20))
    light_palette.setColor(QPalette.Highlight, QColor(76, 163, 224))
    light_palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
    light_palette.setColor(QPalette.Link, QColor(0, 162, 232))
    light_palette.setColor(QPalette.AlternateBase, QColor(225, 225, 225))
    light_palette.setColor(QPalette.ToolTipBase, QColor(240, 240, 240))
    light_palette.setColor(QPalette.ToolTipText, QColor(0, 0, 0))

    # disabled
    light_palette.setColor(QPalette.Disabled, QPalette.WindowText,
                           QColor(115, 115, 115))
    light_palette.setColor(QPalette.Disabled, QPalette.Text,
                           QColor(115, 115, 115))
    light_palette.setColor(QPalette.Disabled, QPalette.ButtonText,
                           QColor(115, 115, 115))
    light_palette.setColor(QPalette.Disabled, QPalette.Highlight,
                           QColor(190, 190, 190))
    light_palette.setColor(QPalette.Disabled, QPalette.HighlightedText,
                           QColor(115, 115, 115))

    return light_palette
