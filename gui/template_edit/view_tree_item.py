import logging
import time
import os

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import *

from core.storage import cache
from core.template_parser.nodes.base import TemplateNode
from gui.constants import ASSETS_PATH

logger = logging.getLogger(__name__)


class TreeEditWidgetItem(QTreeWidgetItem):
    def __init__(self, template_node: TemplateNode = None):
        super().__init__()
        self.template_node = template_node

    def init_widgets(self):
        self.setExpanded(True)
        print(type(self.template_node))
        self.setText(0, "kbfkdbs")
        if self.template_node is None:
            print("hew")
            self.init_edit()
        else:
            self.init_node()

    def init_node(self):
        self.setIcon(0, self.template_node.get_gui_icon())
        self.setText(0, str(self.template_node))

    def init_edit(self):
        self.setText(0, str("+"))
