from PyQt5.QtCore import *
from PyQt5.QtWidgets import *


class ButtonContainer(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.left_layout = QHBoxLayout()
        self.left_layout.setContentsMargins(0, 0, 0, 0)
        self.left_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.right_layout = QHBoxLayout()
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        self.right_layout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        left_widget = QWidget()
        left_widget.setLayout(self.left_layout)

        right_widget = QWidget()
        right_widget.setLayout(self.right_layout)

        layout = QHBoxLayout()
        layout.addWidget(left_widget)
        layout.addWidget(right_widget)
        layout.setContentsMargins(0, 11, 0, 0)
        self.setLayout(layout)