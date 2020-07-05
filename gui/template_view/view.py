import logging

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from gui.template_view.info_view import FolderInfoView, GeneralInfoView, HistoryInfoView
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
        qApp.aboutToQuit.connect(self.save_state)

    def save_state(self):
        qsettings = QSettings("eth-document-fetcher", "eth-document-fetcher")
        qsettings.setValue("mainSplitter/geometry", self.saveGeometry())
        qsettings.setValue("mainSplitter/windowState", self.saveState())

    def read_settings(self):
        qsettings = QSettings("eth-document-fetcher", "eth-document-fetcher")
        if qsettings.value("mainSplitter/geometry") is not None:
            self.restoreGeometry(qsettings.value("mainSplitter/geometry"))
        if qsettings.value("mainSplitter/windowState") is not None:
            self.restoreState(qsettings.value("mainSplitter/windowState"))


class StackedWidgetView(QStackedWidget):
    def __init__(self, view_tree, controller):
        super().__init__()
        self.view_tree = view_tree
        self.old_selected_widget = None
        self.button_group = ButtonGroup()
        self.button_widget = QWidget()
        self.layout_button = QHBoxLayout()
        self.layout_button.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.layout_button.setContentsMargins(0, 0, 0, 0)
        self.button_widget.setLayout(self.layout_button)

        self.views = [
            GeneralInfoView(controller=controller),
            FolderInfoView(controller=controller),
            HistoryInfoView(controller=controller),
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

    def reset_widget(self):
        for view in self.views:
            view.reset_widget()

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
    def __init__(self, template_path, signals, controller, parent=None):
        super().__init__(parent=parent)
        self.template_view_tree = TemplateViewTree(template_path, signals, controller, self)

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 6, 0, 6)

        self.splitter = Splitter()
        self.state_widget = StackedWidgetView(self.template_view_tree, controller)

        self.splitter.addWidget(self.template_view_tree)
        self.splitter.addWidget(self.state_widget)
        self.splitter.read_settings()

        self.layout.addWidget(self.splitter)

        self.layout.addWidget(self.state_widget.button_widget)

        self.setLayout(self.layout)

    def reset(self, template_path):
        self.template_view_tree.init(template_path)
        self.state_widget.reset_widget()

    def get_path(self):
        return self.template_view_tree.template.path

    def set_check_state_to_all(self, state):
        self.template_view_tree.set_check_state_to_all(state)

    def get_checked(self):
        return self.template_view_tree.get_checked()

    def save_template_file(self):
        self.template_view_tree.save_template_file()

    def disconnect_connections(self):
        self.template_view_tree.disconnect_connections()
