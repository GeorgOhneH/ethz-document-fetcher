import logging

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from settings import global_settings
from settings.logger import QtHandler


class Logger(QWidget):
    def __init__(self, parent):
        super().__init__(parent=parent)
        self.setHidden(True)
        self.handler = QtHandler(self)
        self.handler.setLevel(global_settings.loglevel if global_settings.loglevel else logging.INFO)
        self.log_text_box = QPlainTextEdit(self)

        self.log_text_box.setReadOnly(True)
        self.log_text_box.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.log_text_box.setContentsMargins(0, 0, 0, 0)
        self.setContentsMargins(0, 0, 0, 0)

        logging.getLogger().addHandler(self.handler)
        self.handler.new_record.connect(self.log_text_box.appendHtml)

        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 5, 0, 0)
        self.layout.addWidget(self.log_text_box)
        self.setLayout(self.layout)
        self.read_settings()

        qApp.aboutToQuit.connect(self.save_state)

    def save_state(self):
        qsettings = QSettings("eth-document-fetcher", "eth-document-fetcher")
        qsettings.setValue("loggerWidget/windowState", self.isHidden())

    def read_settings(self):
        qsettings = QSettings("eth-document-fetcher", "eth-document-fetcher")
        if qsettings.value("loggerWidget/windowState") is not None:
            self.setHidden(False if qsettings.value("loggerWidget/windowState") == "false" else True)


class LoggerSplitter(QSplitter):
    def __init__(self, *__args):
        super().__init__(*__args)
        self.setChildrenCollapsible(False)
        self.setOrientation(Qt.Vertical)
        self.setHandleWidth(1)
        qApp.aboutToQuit.connect(self.save_state)

    def save_state(self):
        qsettings = QSettings("eth-document-fetcher", "eth-document-fetcher")
        qsettings.setValue("loggerSplitter/geometry", self.saveGeometry())
        qsettings.setValue("loggerSplitter/windowState", self.saveState())

    def read_settings(self):
        qsettings = QSettings("eth-document-fetcher", "eth-document-fetcher")
        if qsettings.value("loggerSplitter/geometry") is not None:
            self.restoreGeometry(qsettings.value("loggerSplitter/geometry"))
        if qsettings.value("loggerSplitter/windowState") is not None:
            self.restoreState(qsettings.value("loggerSplitter/windowState"))



