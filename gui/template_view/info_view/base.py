import logging

from PyQt5.QtWidgets import *

logger = logging.getLogger(__name__)


class InfoView(object):
    def __init__(self, name):
        self.name = name
        self.selected_widget = None
        self.button = QPushButton(name)
        self.button.setCheckable(True)

    def init_connection(self, tree_view):
        tree_view.itemChanged.connect(self._update_view)

    def detect_change_selected(self, selected_widget):
        self.selected_widget = selected_widget
        self.update_view(selected_widget)

    def _update_view(self, widget, column):
        if widget is not self.selected_widget:
            return
        self.update_view(widget)

    def update_view(self, selected_widget):
        pass

    def reset_widget(self):
        raise NotImplementedError
