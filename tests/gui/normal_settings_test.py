import pytest
import sys
import os

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from core.constants import ROOT_PATH
from gui import Application, MainWindow


@pytest.fixture(scope="function")
def qapp(tmp_path):
    sys_argv = sys.argv
    sys.argv[:] = sys_argv + ["--app-data-path", str(tmp_path),
                              "--username", os.getenv("ETHZ_USERNAME"),
                              "--password", os.getenv("ETHZ_PASSWORD"),
                              "--save-path", str(tmp_path),
                              "--template-path", os.path.join(ROOT_PATH, "templates", "HS2020", "D-ITET", "semester3.yml")]
    yield Application([])
    sys.argv[:] = sys_argv


@pytest.mark.skipif(os.getenv("ETHZ_PASSWORD") is None, reason="requires username and password")
def test_full(qtbot):
    main_window = MainWindow()
    main_window.show()
    qtbot.addWidget(main_window)
    app = Application.instance()
    app.actions.run.trigger()
    qtbot.wait(1000)
    app.actions.exit_app.trigger()
    qtbot.wait(1000)
