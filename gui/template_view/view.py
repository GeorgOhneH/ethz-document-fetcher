import logging

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

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
        qApp.aboutToQuit.connect(self.save_state)

    def save_state(self):
        widget_save_settings(self)

    def read_settings(self):
        widget_read_settings(self)


class StackedWidgetView(QStackedWidget):
    def __init__(self, view_tree, controller, parent):
        super().__init__(parent=parent)
        self.view_tree = view_tree
        self.button_group = ButtonGroup(parent=self)
        self.button_widget = QWidget()
        self.layout_button = QHBoxLayout()
        self.layout_button.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.layout_button.setContentsMargins(0, 0, 0, 0)
        self.button_widget.setLayout(self.layout_button)

        self.views = [
            GeneralInfoView(controller=controller, parent=self),
            FolderInfoView(controller=controller, parent=self),
            HistoryInfoView(controller=controller, parent=self),
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
    def __init__(self, template_path, signals, controller, parent=None):
        super().__init__(parent=parent)
        self.template_view_tree = TemplateViewTree(template_path, signals, controller, self)

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 6, 0, 0)

        self.splitter = Splitter()
        self.state_widget = StackedWidgetView(self.template_view_tree, controller, parent=self)

        self.splitter.addWidget(self.template_view_tree)
        self.splitter.addWidget(self.state_widget)
        self.splitter.read_settings()

        self.layout.addWidget(self.splitter)

        self.layout.addWidget(self.state_widget.button_widget)

        self.setLayout(self.layout)

    def reset(self, template_path):
        self.template_view_tree.init(template_path)
        self.state_widget.reset_widget()

    def reset_state(self):
        self.template_view_tree.reset_widgets()

    def get_path(self):
        return self.template_view_tree.template.path

    def get_splitter_orientation(self):
        return self.splitter.orientation()

    def set_splitter_orientation(self, orientation):
        self.splitter.setOrientation(orientation)

    def set_check_state_to_all(self, state):
        self.template_view_tree.set_check_state_to_all(state)

    def get_checked(self):
        return self.template_view_tree.get_checked()

    def save_template_file(self):
        self.template_view_tree.save_template_file()

    def disconnect_connections(self):
        self.template_view_tree.disconnect_connections()
