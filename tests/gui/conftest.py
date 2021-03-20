import pytest
import sys

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from gui import Application, CentralWidget


@pytest.fixture(scope="session")
def qapp():
    print("BEFORE")
    sys.argv = sys.argv + ["--username", "ddf"]
    yield Application([])
    print("AFTER")
