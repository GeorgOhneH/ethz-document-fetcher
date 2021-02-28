import os

from PyQt5.QtCore import *
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import *

from gui.constants import ASSETS_PATH
from gui.dynamic_widgets import DynamicIconLabel
from gui.utils import format_bytes


class DownloadSpeedWidget(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.downloaded_bytes = 0
        self.total_bytes = 0

        self.timer = QTimer()
        self.timer.start(1000)
        self.timer.timeout.connect(self.monitor_download_show)
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        self.text = QLabel()
        self.set_text()

        size = self.text.fontMetrics().height()

        self.icon = DynamicIconLabel(os.path.join(ASSETS_PATH, "speed_download.svg"), size * 0.7, size * 0.7, self)

        self.layout.addWidget(self.icon)
        self.layout.addWidget(self.text)

        app = QApplication.instance()
        app.worker_thread.downloaded_content_length.connect(self.monitor_download)
        app.worker_thread.started.connect(self.reset)

    def set_text(self):
        self.text.setText(f"{format_bytes(self.downloaded_bytes)}/s ({format_bytes(self.total_bytes)})")

    def reset(self):
        self.total_bytes = 0

    def monitor_download(self, size):
        self.downloaded_bytes += size
        self.total_bytes += size

    def monitor_download_show(self):
        self.set_text()
        self.downloaded_bytes = 0
