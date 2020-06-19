import logging.config
import time

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from gui.template_view import TemplateView
from gui.worker import Worker

logger = logging.getLogger(__name__)


class CentralWidget(QWidget):
    def __init__(self, actions, parent=None):
        super().__init__(parent=parent)
        self.actions = actions
        self.start_time = time.time()
        self.downloaded_bytes = 0
        self.one_second_timer = QTimer()
        self.one_second_timer.timeout.connect(self.monitor_download_show)
        self.status_bar = self.parent().statusBar()
        self.monitor_download_widget = QLabel()
        self.monitor_download_widget.setText(self.format_bytes(self.downloaded_bytes))
        self.status_bar.addPermanentWidget(self.monitor_download_widget)

        self.thread = QThread()
        self.worker = Worker()
        self.worker.moveToThread(self.thread)
        self.worker.signals.finished.connect(self.quit_thread)
        self.thread.started.connect(self.worker.main)
        self.worker.signals.downloaded_content_length.connect(self.monitor_download)

        grid = QGridLayout()

        self.btn_run = QPushButton("Run")
        actions.run.triggered.connect(self.start_thread)
        self.btn_run.pressed.connect(self.start_thread)

        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setEnabled(False)
        actions.stop.triggered.connect(self.stop_thread)
        actions.stop.setEnabled(False)
        self.btn_stop.pressed.connect(self.stop_thread)

        self.template_view = TemplateView(self.worker.signals, self, self)

        grid.addWidget(self.btn_run, 0, 0)
        grid.addWidget(self.btn_stop, 0, 1)
        grid.addWidget(self.template_view, 1, 0, 1, 2)
        self.setLayout(grid)

        self.one_second_timer.start(1000)

    def clean_up(self):
        self.stop_thread()

    def start_thread(self, unique_key="root", recursive=True):
        self.start_time = time.time()
        self.btn_run.setText("Running...")
        self.btn_run.setEnabled(False)
        self.actions.run.setEnabled(False)

        self.btn_stop.setEnabled(True)
        self.actions.stop.setEnabled(True)
        self.worker.unique_key = unique_key
        self.worker.recursive = recursive
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

    def monitor_download(self, size):
        self.downloaded_bytes += size

    @staticmethod
    def format_bytes(size):
        # 2**10 = 1024
        power = 2**10
        n = 0
        power_labels = {0 : '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
        while size > power:
            size /= power
            n += 1
        return f"{size:.1f} {power_labels[n]+'B/s'}"

    def monitor_download_show(self):
        self.monitor_download_widget.setText(self.format_bytes(self.downloaded_bytes))
        self.downloaded_bytes = 0
