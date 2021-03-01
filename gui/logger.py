import logging

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from gui.application import Application
from gui.utils import widget_read_settings_func, widget_save_settings_func, widget_save_settings, widget_read_settings
from settings.logger import QtHandler


class Logger(QWidget):
    def __init__(self, parent):
        super().__init__(parent=parent)
        self.setHidden(True)
        behavior_settings = Application.instance().behavior_settings
        self.handler = QtHandler(self)
        self.handler.setLevel(behavior_settings.loglevel if behavior_settings.loglevel else logging.INFO)
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

        actions = Application.instance().actions
        actions.logger.setChecked(not self.isHidden())
        actions.logger.triggered.connect(lambda checked: self.setVisible(checked))

    def save_state(self):
        widget_save_settings_func(self, self.isHidden)

    def read_settings(self):
        value = widget_read_settings_func(self)
        if value is not None:
            self.setHidden(False if value == "false" else True)


class LoggerSplitter(QSplitter):
    def __init__(self, *__args):
        super().__init__(*__args)
        self.setChildrenCollapsible(False)
        self.setOrientation(Qt.Vertical)
        self.setHandleWidth(1)
        qApp.aboutToQuit.connect(lambda: widget_save_settings(self))
        widget_read_settings(self)
