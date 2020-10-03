import copy
import logging.config
import os
import time

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from gui.button_container import ButtonContainer
from gui.constants import ROOT_PATH
from gui.constants import TEMPLATE_PRESET_FILE_PATHS
from gui.logger import Logger, LoggerSplitter
from gui.settings import SettingsDialog
from gui.status_bar_widgets import DownloadSpeedWidget
from gui.template_edit import TemplateEditDialog
from gui.template_view import TemplateView
from gui.worker import Worker
from settings.config_objs.path import open_file_picker
from settings.settings import SiteSettings, TemplatePathSettings
from settings import gui_settings

logger = logging.getLogger(__name__)


class CentralWidget(QWidget):
    def __init__(self, actions, parent=None):
        super().__init__(parent=parent)

        self.actions = actions
        self.start_time = time.time()
        self.thread_finished_open_file_func = None
        self.template_path_settings = TemplatePathSettings()

        self.status_bar = self.parent().statusBar()
        self.download_speed_widget = DownloadSpeedWidget()
        self.status_bar.addPermanentWidget(self.download_speed_widget)

        self.site_settings = SiteSettings()

        self.thread = QThread()
        self.worker = Worker()
        self.worker.moveToThread(self.thread)
        self.worker.signals.finished.connect(self.quit_thread)
        self.thread.started.connect(self.worker.main)
        self.worker.signals.downloaded_content_length.connect(self.download_speed_widget.monitor_download)

        self.grid = QGridLayout()
        self.grid.setContentsMargins(17, 0, 17, 0)

        self.button_container = ButtonContainer()

        self.btn_run_all = QPushButton("Run All")
        actions.run.triggered.connect(lambda triggered: self.start_thread())
        self.btn_run_all.clicked.connect(lambda triggered: self.start_thread())

        self.btn_run_checked = QPushButton("Run Selected")
        actions.run_checked.triggered.connect(self.start_thread_checked)
        self.btn_run_checked.clicked.connect(self.start_thread_checked)

        self.btn_edit = QPushButton("Edit")
        self.btn_edit.setFocusPolicy(Qt.ClickFocus)
        actions.edit_file.triggered.connect(self.open_edit)
        self.btn_edit.clicked.connect(self.open_edit)

        self.btn_settings = QPushButton("Settings")
        self.btn_settings.setFocusPolicy(Qt.ClickFocus)
        actions.settings.triggered.connect(self.open_settings)
        self.btn_settings.clicked.connect(self.open_settings)

        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setEnabled(False)
        actions.stop.triggered.connect(self.stop_thread)
        actions.stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_thread)

        line = QFrame()
        line.setFrameShape(QFrame.VLine)
        line.setLineWidth(1)
        line.setStyleSheet("color: gray;")

        self.btn_check_all = QPushButton("Select All")
        self.btn_check_all.clicked.connect(self.check_all)
        self.btn_uncheck_all = QPushButton("Select None")
        self.btn_uncheck_all.clicked.connect(self.uncheck_all)

        self.button_container.left_layout.addWidget(self.btn_run_all)
        self.button_container.left_layout.addWidget(self.btn_run_checked)
        self.button_container.left_layout.addWidget(self.btn_stop)
        self.button_container.left_layout.addWidget(line)
        self.button_container.left_layout.addWidget(self.btn_check_all)
        self.button_container.left_layout.addWidget(self.btn_uncheck_all)

        self.button_container.right_layout.addWidget(self.btn_edit)
        self.button_container.right_layout.addWidget(self.btn_settings)

        actions.new_file.triggered.connect(lambda: self.open_edit(new=True))
        actions.open_file.triggered.connect(self.open_file)

        self.settings_dialog = SettingsDialog(parent=self, site_settings=self.site_settings)
        self.template_view = TemplateView(self.get_template_path(), self.worker.signals, self, parent=self)
        self.status_bar.showMessage(f"Opened file: {self.get_template_path()}")

        actions.info_position_group.triggered.connect(lambda action, inst=self:
                                                      inst.template_view.set_splitter_orientation(
                                                          Qt.Horizontal if action.text() == "Right" else Qt.Vertical)
                                                      )
        actions.info_position_bottom.setChecked(self.template_view.get_splitter_orientation() == Qt.Vertical)
        actions.info_position_right.setChecked(self.template_view.get_splitter_orientation() == Qt.Horizontal)

        self.logger_widget = Logger(parent=self)

        logger_splitter = LoggerSplitter()
        logger_splitter.addWidget(self.template_view)
        logger_splitter.addWidget(self.logger_widget)
        logger_splitter.read_settings()

        actions.logger.setChecked(not self.logger_widget.isHidden())
        actions.logger.triggered.connect(self.logger_widget.setVisible)

        self.grid.addWidget(self.button_container)
        self.grid.addWidget(logger_splitter)
        self.setLayout(self.grid)

    def clean_up(self):
        self.stop_thread()
        if self.template_view.get_path() not in TEMPLATE_PRESET_FILE_PATHS:
            self.template_view.save_template_file()

    def start_thread_checked(self):
        unique_keys = [widget.template_node.unique_key
                       for widget in self.template_view.get_checked()]

        self.start_thread(unique_keys=unique_keys, recursive=False)

    def start_thread(self, unique_keys=None, recursive=True):
        if unique_keys is None:
            unique_keys = ["root"]

        if not self.site_settings.check_if_valid():
            self.open_settings()
            return

        self.download_speed_widget.reset()

        self.start_time = time.time()
        self.btn_run_all.setText("Running...")
        self.btn_run_all.setEnabled(False)
        self.actions.run.setEnabled(False)

        self.btn_run_checked.setEnabled(False)
        self.actions.run_checked.setEnabled(False)

        self.btn_stop.setEnabled(True)
        self.actions.stop.setEnabled(True)

        self.template_view.reset_state()

        self.worker.unique_keys = unique_keys
        self.worker.recursive = recursive
        self.worker.site_settings = copy.deepcopy(self.site_settings)
        self.worker.template_path = self.get_template_path()
        self.thread.start()

    def stop_thread(self):
        self.worker.stop()

    def quit_thread(self):
        self.thread.quit()
        self.btn_run_all.setText("Run All")
        self.btn_run_all.setEnabled(True)
        self.actions.run.setEnabled(True)

        self.btn_run_checked.setEnabled(True)
        self.actions.run_checked.setEnabled(True)

        self.btn_stop.setEnabled(False)
        self.actions.stop.setEnabled(False)
        self.status_bar.showMessage(f"Finished in {time.time() - self.start_time:.2f} seconds")

    def open_settings(self):
        self.settings_dialog.open()
        self.btn_settings.clearFocus()

    def open_edit(self, *args, new=False, **kwargs):
        if new:
            template_path = None
        else:
            template_path = self.get_template_path()
        template_edit_dialog = TemplateEditDialog(parent=self,
                                                  template_path=template_path,
                                                  template_path_settings=self.template_path_settings)
        template_edit_dialog.accepted.connect(self.apply_edit)
        template_edit_dialog.show()
        self.btn_edit.clearFocus()

    def apply_edit(self):
        self.open_file(file_path=self.get_template_path(), file_changed=True)

    def open_file(self, *args, file_path=None, file_changed=False, **kwargs):
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
            error_dialog = QErrorMessage(self)
            error_dialog.setWindowTitle("Error")
            error_dialog.showMessage(f"{file_path} has not the right file format")
            error_dialog.raise_()
            return
        self.template_path_settings.save()

        if self.thread.isRunning():
            self.thread_finished_open_file_func = lambda: self._open_file(self.get_template_path(),
                                                                          file_changed=file_changed)
            self.thread.finished.connect(self.thread_finished_open_file_func)
            self.stop_thread()
            return

        self._open_file(self.get_template_path(), file_changed=file_changed)

    def _open_file(self, template_path, file_changed):
        if self.thread_finished_open_file_func is not None:
            try:
                self.thread.finished.disconnect(self.thread_finished_open_file_func)
            except TypeError:
                pass

        if template_path != self.template_view.get_path() or not file_changed:
            if self.template_view.get_path() not in TEMPLATE_PRESET_FILE_PATHS:
                self.template_view.save_template_file()

        self.template_view.reset(template_path)

        self.status_bar.showMessage(f"Opened file: {template_path}")

    def get_template_path(self):
        if os.path.isabs(self.template_path_settings.template_path):
            return self.template_path_settings.template_path

        return os.path.join(ROOT_PATH, self.template_path_settings.template_path)

    def check_all(self):
        self.template_view.set_check_state_to_all(Qt.Checked)

    def uncheck_all(self):
        self.template_view.set_check_state_to_all(Qt.Unchecked)
