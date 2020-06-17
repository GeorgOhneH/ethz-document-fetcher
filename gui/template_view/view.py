from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

import os
import logging

from gui.template_view.info_view import InfoFolderView, InfoGeneralView
from gui.template_view.view_tree import TemplateViewTree

logger = logging.getLogger(__name__)


class ButtonGroup(QButtonGroup):
    def __init__(self):
        super().__init__()
        self.buttonClicked.connect(self.uncheck_button)
        self.last_button_clicked = None
        self.last_button_clicked_checked = None

    def uncheck_button(self, button: QAbstractButton):
        if button is self.last_button_clicked and self.last_button_clicked_checked:
            self.setExclusive(False)
            button.setChecked(False)
            self.setExclusive(True)
        self.last_button_clicked = button
        self.last_button_clicked_checked = button.isChecked()


class Splitter(QSplitter):
    def __init__(self):
        super().__init__()
        self.setChildrenCollapsible(False)
        self.setOrientation(Qt.Vertical)


class StackedWidgetView(QStackedWidget):
    def __init__(self, view_tree):
        super().__init__()
        self.view_tree = view_tree
        self.old_selected_widget = None
        self.button_group = ButtonGroup()
        self.button_widget = QWidget()
        self.layout_button = QHBoxLayout()
        self.button_widget.setLayout(self.layout_button)

        self.views = [
            InfoGeneralView(),
            InfoFolderView(),
        ]

        self.init_views()

        self.button_group.buttonClicked.connect(self.change_state_widget)
        self.view_tree.itemSelectionChanged.connect(self.only_if_one_selected)

        self.change_state_widget()

    def init_views(self):
        for view in self.views:
            self.addWidget(view)
            self.button_group.addButton(view.button)
            self.layout_button.addWidget(view.button)

    def only_if_one_selected(self):
        selected_widgets = self.view_tree.selectedItems()
        if len(selected_widgets) != 1:
            return

        for view in self.views:
            view.detect_change_selected(selected_widgets[0], self.old_selected_widget)
        self.old_selected_widget = selected_widgets[0]

    def change_state_widget(self, *args):
        button = self.button_group.checkedButton()
        if button is None:
            self.hide()
            return
        self.show()
        for view in self.views:
            if button is view.button:
                self.setCurrentWidget(view)
                break


class TemplateView(QWidget):
    def __init__(self, signals, parent=None):
        super().__init__(parent=parent)
        self.template_view_tree = TemplateViewTree(signals, self)

        self.layout = QVBoxLayout()

        self.splitter = Splitter()
        self.state_widget = StackedWidgetView(self.template_view_tree)

        self.splitter.addWidget(self.template_view_tree)
        self.splitter.addWidget(self.state_widget)

        self.layout.addWidget(self.splitter)

        self.layout.addWidget(self.state_widget.button_widget)

        self.setLayout(self.layout)
