import os

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from gui.application import Application
from gui.constants import DARK_THEMES


def path_to_dark_path(path):
    parts = path.split(".")
    parts[-2] += "-dark"
    return ".".join(parts)


class DynamicIcon(QIcon):
    def __init__(self, path):
        super().__init__(path)
        self.path = path
        self.path_dark = path_to_dark_path(path)

        self.set_icon()

        Application.instance().theme_changed.connect(self.set_icon)

    def _set_icon(self, path):
        self.swap(QIcon(path))

    def set_icon(self):
        gui_settings = Application.instance().gui_settings

        if gui_settings.theme in DARK_THEMES:
            if os.path.exists(self.path_dark):
                self._set_icon(self.path_dark)
                return

        self._set_icon(self.path)


class DynamicIconLabel(QLabel):
    def __init__(self, path, width, height, parent):
        super().__init__(parent=parent)
        self.path = path
        self.path_dark = path_to_dark_path(path)
        self.icon_width = width
        self.icon_height = height

        self.set_pixmap()

        Application.instance().theme_changed.connect(self.set_pixmap)

    def _set_pixmap(self, path):
        icon = QIcon(path)

        device_ratio = qApp.devicePixelRatio()
        pixmap = icon.pixmap(QSize(int(self.icon_width * device_ratio), int(self.icon_height * device_ratio)))

        pixmap_mask = icon.pixmap(QSize(int(self.icon_width), int(self.icon_height)))
        pixmap.setDevicePixelRatio(device_ratio)
        self.setPixmap(pixmap)
        self.setMask(pixmap_mask.mask())
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    def set_pixmap(self):
        gui_settings = Application.instance().gui_settings

        if gui_settings.theme in DARK_THEMES:
            if os.path.exists(self.path_dark):
                self._set_pixmap(self.path_dark)
                return

        self._set_pixmap(self.path)
