import logging
import os
import time

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from core.constants import VERSION
from gui.constants import ROOT_PATH, TUTORIAL_URL
from gui.controller import CentralWidget
from gui.application import Application
from gui.status_bar_widgets import DownloadSpeedWidget
from gui.utils import widget_read_settings, widget_save_settings, get_template_path

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        app = Application.instance()

        self.central_widget = CentralWidget(parent=self)

        status_bar = self.statusBar()

        status_bar.showMessage(f"Opened file: {get_template_path()}")
        status_bar.addPermanentWidget(DownloadSpeedWidget(parent=status_bar))
        app.file_opened.connect(lambda new_template_path:
                                status_bar.showMessage(f"Opened file: {get_template_path()}"))

        self.start_time = time.time()
        app.worker_thread.started.connect(lambda: self.set_start_time())
        app.worker_thread.finished.connect(lambda:
                                           self.statusBar().showMessage(
                                               f"Finished in {time.time() - self.start_time:.2f} seconds")
                                           )

        menu_bar = self.menuBar()
        actions = Application.instance().actions
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

        self.setWindowTitle(f"ethz-document-fetcher {VERSION}")
        self.setCentralWidget(self.central_widget)

        self.read_settings()

    def init_menu(self, menu, path):
        app = Application.instance()
        for file_name in os.listdir(path):
            sub_path = os.path.join(path, file_name)
            if not os.path.isfile(sub_path):
                sub_menu = menu.addMenu(file_name)
                self.init_menu(sub_menu, sub_path)
            elif ".yml" in file_name:
                action = menu.addAction(str(file_name))
                action.triggered.connect(lambda checked, file_path=sub_path:
                                         app.open_file(file_path=file_path))

    def closeEvent(self, event):
        widget_save_settings(self)
        app = Application.instance()
        app.stop_worker()
        app.worker_thread.finished.connect(app.quit)
        if not app.worker_thread.isRunning():
            event.accept()
        else:
            event.ignore()
            QTimer.singleShot(100, lambda: self._force_quit_prompt())

    def _force_quit_prompt(self):
        app = Application.instance()
        r = QMessageBox.question(self,
                                 "Are you sure?",
                                 "Force Quit",
                                 QMessageBox.Yes | QMessageBox.No)
        if r == QMessageBox.Yes:
            app.quit()
        else:
            app.worker_thread.finished.disconnect(app.quit)

    def read_settings(self):
        self.resize(900, 600)
        widget_read_settings(self)

    def set_start_time(self):
        self.start_time = time.time()
