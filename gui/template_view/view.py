import logging

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from gui.application import Application
from gui.template_view.info_view import FolderInfoView, GeneralInfoView, HistoryInfoView
from gui.template_view.view_tree import TemplateViewTree
from gui.utils import widget_read_settings_func, widget_save_settings_func, widget_read_settings, widget_save_settings

logger = logging.getLogger(__name__)


class ButtonGroup(QButtonGroup):
    def __init__(self, parent):
        super().__init__(parent=parent)
        self.setExclusive(False)
        self.last_active_button = None
        self.buttonClicked.connect(self.uncheck_button)
        qApp.aboutToQuit.connect(self.save_state)

    def uncheck_button(self, clicked_btn: QAbstractButton):
        if clicked_btn is self.last_active_button:
            return
        if self.last_active_button is not None:
            self.last_active_button.setChecked(False)
        self.last_active_button = clicked_btn
        # A weird bug in pyinstaller. We 'refresh' the buttons so that they get updated
        for btn in self.buttons():
            btn.hide()
            btn.show()

    def save_state(self):
        widget_save_settings_func(self, self.checkedId, name="buttonGroupView/id")

    def read_settings(self):
        button_id = widget_read_settings_func(self, name="buttonGroupView/id")
        if button_id is None:
            return
        button = self.button(button_id)
        if button is not None:
            self.last_active_button = button
            button.setChecked(True)


class Splitter(QSplitter):
    def __init__(self):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setChildrenCollapsible(False)
        self.setOrientation(Qt.Vertical)
        widget_read_settings(self)
        qApp.aboutToQuit.connect(lambda: widget_save_settings(self))

        actions = Application.instance().actions

        actions.info_position_group.triggered.connect(
            lambda action: self.setOrientation(Qt.Horizontal if action.text() == "Right" else Qt.Vertical))
        actions.info_position_bottom.setChecked(self.orientation() == Qt.Vertical)
        actions.info_position_right.setChecked(self.orientation() == Qt.Horizontal)


class StackedWidgetView(QStackedWidget):
    def __init__(self, view_tree, parent):
        super().__init__(parent=parent)
        self.view_tree = view_tree
        self.button_group = ButtonGroup(parent=self)
        self.button_widget = QWidget()
        self.layout_button = QHBoxLayout()
        self.layout_button.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.layout_button.setContentsMargins(0, 0, 0, 0)
        self.button_widget.setLayout(self.layout_button)

        self.views = [
            GeneralInfoView(parent=self),
            FolderInfoView(parent=self),
            HistoryInfoView(parent=self),
        ]

        self.init_views()

        self.button_group.buttonClicked.connect(self.change_state_widget)
        self.view_tree.itemSelectionChanged.connect(self.only_if_one_selected)

        self.change_state_widget()

        app = Application.instance()
        app.file_opened.connect(lambda new_template_path: self.reset_widget())

    def init_views(self):
        for view in self.views:
            self.addWidget(view)
            self.button_group.addButton(view.button)
            self.layout_button.addWidget(view.button)
            view.init_connection(self.view_tree)
        self.button_group.read_settings()

    def reset_widget(self):
        for view in self.views:
            view.reset_widget()

    def only_if_one_selected(self):
        selected_widgets = self.view_tree.selectedItems()

        if len(selected_widgets) == 0:
            self.reset_widget()
            return
        if len(selected_widgets) != 1:
            return

        for view in self.views:
            view.detect_change_selected(selected_widgets[0])

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
    def __init__(self, template_path, parent=None):
        super().__init__(parent=parent)
        self.template_view_tree = TemplateViewTree(template_path, self)

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 6, 0, 0)

        self.splitter = Splitter()
        self.state_widget = StackedWidgetView(self.template_view_tree, parent=self)

        self.splitter.addWidget(self.template_view_tree)
        self.splitter.addWidget(self.state_widget)

        self.layout.addWidget(self.splitter)

        self.layout.addWidget(self.state_widget.button_widget)

        self.setLayout(self.layout)
