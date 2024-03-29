import logging.config

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

import gui

logger = logging.getLogger(__name__)


class CentralWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        app = gui.Application.instance()
        actions = app.actions

        self.grid = QGridLayout()
        self.grid.setContentsMargins(17, 0, 17, 0)

        self.button_container = gui.ButtonContainer()

        self.btn_run_all = gui.ActionButton("Run All")
        self.btn_run_all.set_action(actions.run)

        self.btn_run_checked = gui.ActionButton("Run Selected")
        self.btn_run_checked.set_action(actions.run_checked)

        self.btn_edit = gui.ActionButton("Edit")
        self.btn_edit.setFocusPolicy(Qt.ClickFocus)
        self.btn_edit.set_action(actions.edit_file)

        self.btn_settings = gui.ActionButton("Settings")
        self.btn_settings.setFocusPolicy(Qt.ClickFocus)
        self.btn_settings.set_action(actions.settings)

        self.btn_stop = gui.ActionButton("Stop")
        self.btn_stop.set_action(actions.stop)

        line = QFrame()
        line.setFrameShape(QFrame.VLine)
        line.setLineWidth(1)
        line.setStyleSheet("color: gray;")

        self.btn_check_all = gui.action_button.ActionButton("Select All")
        self.btn_check_all.set_action(actions.select_all)
        self.btn_check_none = gui.action_button.ActionButton("Select None")
        self.btn_check_none.set_action(actions.select_none)

        self.button_container.left_layout.addWidget(self.btn_run_all)
        self.button_container.left_layout.addWidget(self.btn_run_checked)
        self.button_container.left_layout.addWidget(self.btn_stop)
        self.button_container.left_layout.addWidget(line)
        self.button_container.left_layout.addWidget(self.btn_check_all)
        self.button_container.left_layout.addWidget(self.btn_check_none)

        self.button_container.right_layout.addWidget(self.btn_edit)
        self.button_container.right_layout.addWidget(self.btn_settings)

        self.template_view = gui.TemplateView(app.get_template_path(), parent=self)

        self.logger_widget = gui.Logger(parent=self)

        logger_splitter = gui.LoggerSplitter()
        logger_splitter.addWidget(self.template_view)
        logger_splitter.addWidget(self.logger_widget)

        self.grid.addWidget(self.button_container)
        self.grid.addWidget(logger_splitter)
        self.setLayout(self.grid)

        app.worker_thread.started.connect(self.thread_started)
        app.worker_thread.finished.connect(self.thread_finished)

    def thread_started(self):
        self.btn_run_all.setText("Running...")

    def thread_finished(self):
        self.btn_run_all.setText("Run All")
