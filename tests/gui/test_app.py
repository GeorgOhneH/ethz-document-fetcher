import pytest
import sys

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from gui import Application, CentralWidget


@pytest.fixture(scope="function")
def qapp(tmp_path):
    sys_argv = sys.argv
    sys.argv[:] = sys_argv + ["--app-data-path", str(tmp_path), "--username", "df"]
    yield Application([])
    sys.argv[:] = sys_argv


def test_hello(qtbot):
    main_window = CentralWidget()
    assert Application.instance().download_settings.username == "df"
    qtbot.addWidget(main_window)
    qtbot.mouseClick(main_window.btn_edit, Qt.LeftButton)
