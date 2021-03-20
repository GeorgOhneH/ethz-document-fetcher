import pytest
import sys

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from gui import Application, CentralWidget


@pytest.fixture(scope="function")
def qapp():
    print("BEFORE")
    sys.argv = sys.argv + ["--username", "df"]
    yield Application([])
    print("AFTER")


def test_hello(qtbot):
    main_window = CentralWidget()
    assert Application.instance().download_settings.username == "df"
    qtbot.addWidget(main_window)
    qtbot.mouseClick(main_window.btn_edit, Qt.LeftButton)
