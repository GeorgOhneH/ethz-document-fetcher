import logging
import os
import time

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

import gui
from core.constants import VERSION, APP_NAME
from gui.constants import ROOT_PATH, TUTORIAL_URL, SITES_URL
from gui.utils import widget_read_settings, widget_save_settings

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        app = gui.Application.instance()

        self.central_widget = gui.CentralWidget(parent=self)

        status_bar = self.statusBar()

        status_bar.showMessage(f"Opened file: {app.get_template_path()}")
        status_bar.addPermanentWidget(gui.DownloadSpeedWidget(parent=status_bar))
        app.file_opened.connect(lambda new_template_path:
                                status_bar.showMessage(f"Opened file: {app.get_template_path()}"))

        self.start_time = time.time()
        app.worker_thread.started.connect(lambda: self.set_start_time())
        app.worker_thread.finished.connect(lambda:
                                           self.statusBar().showMessage(
                                               f"Finished in {time.time() - self.start_time:.2f} seconds")
                                           )

        menu_bar = self.menuBar()
        actions = gui.Application.instance().actions
        file_menu = menu_bar.addMenu("&File")

        file_menu.addAction(actions.new_file)

        file_menu.addAction(actions.edit_file)

        file_menu.addAction(actions.open_file)

        open_presets = file_menu.addMenu("Open &Presets")

        self.init_menu(open_presets, os.path.join(ROOT_PATH, "templates"))

        file_menu.addSeparator()
        file_menu.addAction(actions.settings)
        file_menu.addSeparator()
        file_menu.addAction(actions.exit_app)
        run_menu = menu_bar.addMenu("&Run")
        run_menu.addAction(actions.run)
        run_menu.addAction(actions.run_checked)
        run_menu.addAction(actions.stop)

        view_menu = menu_bar.addMenu("&View")
        info_position_menu = view_menu.addMenu("Info Tab Position")
        info_position_menu.addAction(actions.info_position_bottom)
        info_position_menu.addAction(actions.info_position_right)

        view_menu.addAction(actions.logger)

        help_menu = menu_bar.addMenu("&Help")
        getting_started_action = help_menu.addAction("Getting Started")
        getting_started_action.triggered.connect(lambda: QDesktopServices.openUrl(QUrl(TUTORIAL_URL)))
        site_action = help_menu.addAction("Site Documentation")
        site_action.triggered.connect(lambda: QDesktopServices.openUrl(QUrl(SITES_URL)))

        view_menu.addAction(actions.logger)

        self.settings_dialog = gui.SettingsDialog(download_settings=app.download_settings, parent=self)
        actions.settings.triggered.connect(lambda: self.settings_dialog.open())

        self.template_edit_dialog = gui.TemplateEditDialog(parent=self, template_path=None)
        actions.new_file.triggered.connect(lambda: self.open_edit(template_path=None))
        actions.edit_file.triggered.connect(lambda: self.open_edit(template_path=app.get_template_path()))

        self.setWindowTitle(f"{APP_NAME} {VERSION}")
        self.setCentralWidget(self.central_widget)

        self.read_settings()

        app.aboutToQuit.connect(self.save_state)

    def open_edit(self, template_path=None):
        app = gui.Application.instance()
        app.edit_opened.emit()
        self.template_edit_dialog.reset_template(template_path=template_path)
        self.template_edit_dialog.open()

    def init_menu(self, menu, path):
        app = gui.Application.instance()
        for file_name in os.listdir(path):
            sub_path = os.path.join(path, file_name)
            if not os.path.isfile(sub_path):
                sub_menu = menu.addMenu(file_name)
                self.init_menu(sub_menu, sub_path)
            elif ".yml" in file_name:
                action = menu.addAction(str(file_name))
                action.triggered.connect(lambda checked, file_path=sub_path:
                                         app.open_file(file_path=file_path))

    def showEvent(self, event):
        super().showEvent(event)
        app = gui.Application.instance()
        if not event.spontaneous() and\
                os.path.normcase(os.path.join("templates", "example.yml")) in os.path.normcase(app.get_template_path()):
            QTimer().singleShot(200, self.show_help)

    def show_help(self):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Getting Started")
        msg_box.setText(f"Are you unsure how to use this program?<br>"
                        f"Have a look at this quick guide.<br>"
                        f"(This will open a website in your browser)")
        msg_box.setStandardButtons(QMessageBox.Open | QMessageBox.Close)
        ret = msg_box.exec()
        if ret == QMessageBox.Open:
            QDesktopServices.openUrl(QUrl(TUTORIAL_URL))

    def closeEvent(self, event):
        app = gui.Application.instance()
        app.actions.exit_app.trigger()
        event.ignore()

    def save_state(self):
        widget_save_settings(self)

    def read_settings(self):
        self.resize(900, 600)
        widget_read_settings(self)

    def set_start_time(self):
        self.start_time = time.time()
