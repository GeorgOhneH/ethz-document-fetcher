import logging
import os
import traceback

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from gui.template_edit.view_tree import TemplateEditViewTree

logger = logging.getLogger(__name__)


class TemplateEditDialog(QDialog):
    def __init__(self, parent, template_path):
        super().__init__(parent=parent)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setModal(True)
        self.setWindowTitle("Edit")
        self.finished.connect(self.save_geometry)

        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

        self.template_view = TemplateEditViewTree(template_path=template_path, parent=self)

        self.layout.addWidget(self.template_view)

    def open(self):
        self.read_settings()
        super(TemplateEditDialog, self).open()

    def closeEvent(self, event):
        self.save_geometry()
        super(QDialog, self).closeEvent(event)

    def save_geometry(self):
        qsettings = QSettings("eth-document-fetcher", "eth-document-fetcher")
        qsettings.setValue("templateEditDialog/geometry", self.saveGeometry())

    def read_settings(self):
        qsettings = QSettings("eth-document-fetcher", "eth-document-fetcher")
        if qsettings.value("templateEditDialog/geometry") is not None:
            self.restoreGeometry(qsettings.value("templateEditDialog/geometry"))
