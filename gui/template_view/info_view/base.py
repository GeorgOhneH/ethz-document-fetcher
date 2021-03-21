import logging

from PyQt5.QtWidgets import *

logger = logging.getLogger(__name__)


class InfoView(object):
    def __init__(self, name):
        self.name = name
        self.selected_widget = None
        self.current_btn = None
        self.button = QPushButton(name)
        self.button.setCheckable(True)

    def init_connection(self, tree_view):
        tree_view.itemChanged.connect(self._update_view)

    def detect_change_selected(self, selected_widget):
        self.selected_widget = selected_widget
        self._update_view(selected_widget)

    def update_current_button(self, current_button):
        self.current_btn = current_button
        if self.selected_widget is not None:
            self._update_view(self.selected_widget)

    def _update_view(self, widget, column=None):
        if self.button is not self.current_btn:
            return
        if widget is not self.selected_widget:
            return
        self.update_view(widget)

    def update_view(self, selected_widget):
        pass

    def reset_widget(self):
        raise NotImplementedError
