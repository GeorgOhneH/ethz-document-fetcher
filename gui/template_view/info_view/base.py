import logging

from PyQt5.QtWidgets import *

logger = logging.getLogger(__name__)


class InfoView(object):
    def __init__(self, name, controller):
        self.controller = controller
        self.name = name
        self.button = QPushButton(name)
        self.button.setCheckable(True)

    def detect_change_selected(self, selected_widget, old_widget):
        selected_widget.signals.data_changed.connect(self.update_view)
        if old_widget is not None:
            old_widget.signals.data_changed.disconnect(self.update_view)
        self.update_view(selected_widget)

    def update_view(self, selected_widget):
        pass
