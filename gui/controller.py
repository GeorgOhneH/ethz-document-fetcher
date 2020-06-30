import logging.config
import time
import copy
import os

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from gui.template_view import TemplateView
from gui.template_edit import TemplateEditDialog
from gui.worker import Worker
from gui.settings import SettingsDialog
from gui.constants import ROOT_PATH
from gui.utils import format_bytes
from settings.settings import SiteSettings, TemplatePathSettings
from settings.config_objs.path import open_file_picker

logger = logging.getLogger(__name__)


class CentralWidget(QWidget):
    def __init__(self, actions, parent=None):
        super().__init__(parent=parent)
        self.actions = actions
        self.start_time = time.time()
        self.downloaded_bytes = 0
        self.template_path_settings = TemplatePathSettings()

        self.one_second_timer = QTimer()
        self.one_second_timer.timeout.connect(self.monitor_download_show)
        self.status_bar = self.parent().statusBar()
        self.monitor_download_widget = QLabel()
        self.monitor_download_widget.setText(format_bytes(self.downloaded_bytes) + "/s")
        self.status_bar.addPermanentWidget(self.monitor_download_widget)

        self.site_settings = SiteSettings()

        self.thread = QThread()
        self.worker = Worker()
        self.worker.moveToThread(self.thread)
        self.worker.signals.finished.connect(self.quit_thread)
        self.thread.started.connect(self.worker.main)
        self.worker.signals.downloaded_content_length.connect(self.monitor_download)

        self.grid = QGridLayout()
        self.grid.setContentsMargins(17, 0, 17, 0)

        self.button_container = QWidget()
        self.button_container.setLayout(QHBoxLayout())
        self.button_container.layout().setContentsMargins(0, 11, 0, 0)
        self.button_container.layout().setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.btn_run = QPushButton("Run")
        actions.run.triggered.connect(lambda: self.start_thread())
        self.btn_run.pressed.connect(self.start_thread)

        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setEnabled(False)
        actions.stop.triggered.connect(self.stop_thread)
        actions.stop.setEnabled(False)
        self.btn_stop.pressed.connect(self.stop_thread)

        self.button_container.layout().addWidget(self.btn_run)
        self.button_container.layout().addWidget(self.btn_stop)

        actions.settings.triggered.connect(self.open_settings)
        actions.edit_file.triggered.connect(self.open_edit)
        actions.open_file.triggered.connect(self.open_file)

        self.settings_dialog = SettingsDialog(parent=self, site_settings=self.site_settings)
        self.template_edit_dialog = None
        self.template_view = TemplateView(self.get_template_path(), self.worker.signals, self, self)
        self.status_bar.showMessage(f"Opened file: {self.get_template_path()}")

        self.grid.addWidget(self.button_container)
        self.grid.addWidget(self.template_view)
        self.setLayout(self.grid)

        self.one_second_timer.start(1000)

    def clean_up(self):
        self.stop_thread()

    def start_thread(self, unique_key="root", recursive=True):
        if not self.site_settings.check_if_valid():
            self.open_settings()
            return

        self.start_time = time.time()
        self.btn_run.setText("Running...")
        self.btn_run.setEnabled(False)
        self.actions.run.setEnabled(False)

        self.btn_stop.setEnabled(True)
        self.actions.stop.setEnabled(True)

        self.worker.unique_key = unique_key
        self.worker.recursive = recursive
        self.worker.site_settings = copy.deepcopy(self.site_settings)
        self.worker.template_path = self.get_template_path()
        self.thread.start()

    def stop_thread(self):
        self.worker.stop()

    def quit_thread(self):
        self.thread.quit()
        self.btn_run.setText("Run")
        self.btn_run.setEnabled(True)
        self.actions.run.setEnabled(True)

        self.btn_stop.setEnabled(False)
        self.actions.stop.setEnabled(False)
        self.status_bar.showMessage(f"Finished in {time.time() - self.start_time:.2f} seconds")

    def open_settings(self):
        self.settings_dialog.open()

    def open_edit(self):
        self.template_edit_dialog = TemplateEditDialog(parent=self,
                                                       template_path=self.get_template_path(),
                                                       template_path_settings=self.template_path_settings)
        self.template_edit_dialog.accepted.connect(self.apply_edit)
        self.template_edit_dialog.open()

    def apply_edit(self):
        self.open_file(file_path=self.get_template_path())

    def open_file(self, checked=None, file_path=None):
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
            return
        self.template_path_settings.save()

        self.template_view.disconnect_connections()
        new_template_view = TemplateView(self.get_template_path(), self.worker.signals, self, self)
        self.grid.replaceWidget(self.template_view, new_template_view)
        self.template_view = new_template_view

        self.status_bar.showMessage(f"Opened file: {self.get_template_path()}")

    def get_template_path(self):
        if os.path.isabs(self.template_path_settings.template_path):
            return self.template_path_settings.template_path

        return os.path.join(ROOT_PATH, self.template_path_settings.template_path)

    def monitor_download(self, size):
        self.downloaded_bytes += size

    def monitor_download_show(self):
        self.monitor_download_widget.setText(format_bytes(self.downloaded_bytes) + "/s")
        self.downloaded_bytes = 0
