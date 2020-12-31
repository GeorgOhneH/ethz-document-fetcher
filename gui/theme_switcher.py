import logging

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from gui.constants import POSSIBLE_THEMES, THEME_NATIVE, THEME_FUSION_DARK, THEME_FUSION_LIGHT
from settings import gui_settings

logger = logging.getLogger(__name__)


def _init_dark_pallet():
    dark_palette = QPalette()

    # base
    dark_palette.setColor(QPalette.WindowText, QColor(180, 180, 180))
    dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.Light, QColor(180, 180, 180))
    dark_palette.setColor(QPalette.Midlight, QColor(90, 90, 90))
    dark_palette.setColor(QPalette.Dark, QColor(35, 35, 35))
    dark_palette.setColor(QPalette.Text, QColor(180, 180, 180))
    dark_palette.setColor(QPalette.BrightText, QColor(180, 180, 180))
    dark_palette.setColor(QPalette.ButtonText, QColor(180, 180, 180))
    dark_palette.setColor(QPalette.Base, QColor(42, 42, 42))
    dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.Shadow, QColor(20, 20, 20))
    dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.HighlightedText, QColor(180, 180, 180))
    dark_palette.setColor(QPalette.Link, QColor(56, 252, 196))
    dark_palette.setColor(QPalette.AlternateBase, QColor(66, 66, 66))
    dark_palette.setColor(QPalette.ToolTipBase, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ToolTipText, QColor(180, 180, 180))

    # disabled
    dark_palette.setColor(QPalette.Disabled, QPalette.WindowText,
                          QColor(127, 127, 127))
    dark_palette.setColor(QPalette.Disabled, QPalette.Text,
                          QColor(127, 127, 127))
    dark_palette.setColor(QPalette.Disabled, QPalette.ButtonText,
                          QColor(127, 127, 127))
    dark_palette.setColor(QPalette.Disabled, QPalette.Highlight,
                          QColor(80, 80, 80))
    dark_palette.setColor(QPalette.Disabled, QPalette.HighlightedText,
                          QColor(127, 127, 127))

    return dark_palette


def _init_light_palette():
    light_palette = QPalette()

    # base
    light_palette.setColor(QPalette.WindowText, QColor(0, 0, 0))
    light_palette.setColor(QPalette.Button, QColor(240, 240, 240))
    light_palette.setColor(QPalette.Light, QColor(180, 180, 180))
    light_palette.setColor(QPalette.Midlight, QColor(200, 200, 200))
    light_palette.setColor(QPalette.Dark, QColor(225, 225, 225))
    light_palette.setColor(QPalette.Text, QColor(0, 0, 0))
    light_palette.setColor(QPalette.BrightText, QColor(0, 0, 0))
    light_palette.setColor(QPalette.ButtonText, QColor(0, 0, 0))
    light_palette.setColor(QPalette.Base, QColor(237, 237, 237))
    light_palette.setColor(QPalette.Window, QColor(240, 240, 240))
    light_palette.setColor(QPalette.Shadow, QColor(20, 20, 20))
    light_palette.setColor(QPalette.Highlight, QColor(76, 163, 224))
    light_palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
    light_palette.setColor(QPalette.Link, QColor(0, 162, 232))
    light_palette.setColor(QPalette.AlternateBase, QColor(225, 225, 225))
    light_palette.setColor(QPalette.ToolTipBase, QColor(240, 240, 240))
    light_palette.setColor(QPalette.ToolTipText, QColor(0, 0, 0))

    # disabled
    light_palette.setColor(QPalette.Disabled, QPalette.WindowText,
                           QColor(115, 115, 115))
    light_palette.setColor(QPalette.Disabled, QPalette.Text,
                           QColor(115, 115, 115))
    light_palette.setColor(QPalette.Disabled, QPalette.ButtonText,
                           QColor(115, 115, 115))
    light_palette.setColor(QPalette.Disabled, QPalette.Highlight,
                           QColor(190, 190, 190))
    light_palette.setColor(QPalette.Disabled, QPalette.HighlightedText,
                           QColor(115, 115, 115))

    return light_palette


class ThemeSwitcher(QObject):
    theme_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.current_theme = None
        self.default_palette = qApp.palette()
        self.default_style = qApp.style().objectName()

        self.dark_palette = _init_dark_pallet()
        self.light_palette = _init_light_palette()

        self.set_current_setting_theme()

    # IMPORTANT: Set style AFTER palette
    def _to_native(self):
        qApp.setPalette(self.default_palette)
        qApp.setStyle(self.default_style)

    def _to_fusion_dark(self):
        qApp.setPalette(self.dark_palette)
        qApp.setStyle("Fusion")

    def _to_fusion_light(self):
        qApp.setPalette(self.light_palette)
        qApp.setStyle("Fusion")

    def set_theme(self, theme):
        logger.debug(f"Setting Theme: {theme}")

        if self.current_theme == theme:
            return

        if theme == THEME_NATIVE:
            self._to_native()
        elif theme == THEME_FUSION_DARK:
            self._to_fusion_dark()
        elif theme == THEME_FUSION_LIGHT:
            self._to_fusion_light()
        else:
            raise ValueError(f"theme must be one of these {POSSIBLE_THEMES}, not ({theme})")

        self.current_theme = theme
        self.theme_changed.emit()

    def set_current_setting_theme(self):
        if gui_settings.theme:
            self.set_theme(gui_settings.theme)
