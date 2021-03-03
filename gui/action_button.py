from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *


class ActionButton(QPushButton):
    def __init__(self, *__args):
        super().__init__(*__args)
        self.action_owner = None

    def set_action(self, action):
        if self.action_owner and self.action_owner != action:
            self.action_owner.changed.disconnect(self.updateButtonStatusFromAction)
            self.clicked.disconnect(self.action_owner.trigger)
        self.action_owner = action
        if not self.text():
            self.setText(self.action_owner.text())
        self.update_button_status_from_action()

        self.action_owner.changed.connect(self.update_button_status_from_action)
        self.clicked.connect(self.action_owner.trigger)

    def update_button_status_from_action(self):
        if self.action_owner is None:
            return

        self.setStatusTip(self.action_owner.statusTip())
        self.setIcon(self.action_owner.icon())
        self.setEnabled(self.action_owner.isEnabled())
        self.setCheckable(self.action_owner.isCheckable())
        self.setChecked(self.action_owner.isChecked())
