import functools
import os
from pathlib import Path

from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QApplication

from core.constants import APP_NAME
from core.utils import get_app_data_path


@functools.lru_cache(maxsize=None)
def get_empty_folder_path():
    empty_folder_path = os.path.join(get_app_data_path(), "empty_folder")
    Path(empty_folder_path).mkdir(parents=True, exist_ok=True)
    return empty_folder_path


def format_bytes(size):
    power = 2 ** 10
    n = 0
    power_labels = {0: '', 1: 'Ki', 2: 'Mi', 3: 'Gi', 4: 'Ti', 5: "Pi"}
    while size > power:
        size /= power
        n += 1
    return f"{size:.1f} {power_labels[n] + 'B'}"


def _get_name_from_widget(widget, name):
    if name is None:
        name = ""
    monitor_size = QApplication.primaryScreen().availableVirtualSize()
    dimensions = f"{monitor_size.width()}x{monitor_size.height()}"
    name = widget.__class__.__module__ + widget.__class__.__name__ + dimensions + name

    return name


def widget_save_settings(widget, name=None, save_geometry=True, save_state=True):
    name = _get_name_from_widget(widget, name)
    qsettings = QSettings(APP_NAME, APP_NAME)
    if save_geometry:
        qsettings.setValue(name + "/geometry", widget.saveGeometry())
    if save_state:
        qsettings.setValue(name + "/windowState", widget.saveState())


def widget_read_settings(widget, name=None, save_geometry=True, save_state=True):
    name = _get_name_from_widget(widget, name)
    qsettings = QSettings(APP_NAME, APP_NAME)
    if save_geometry and qsettings.value(name + "/geometry") is not None:
        widget.restoreGeometry(qsettings.value(name + "/geometry"))
    if save_state and qsettings.value(name + "/windowState") is not None:
        widget.restoreState(qsettings.value(name + "/windowState"))


def widget_save_settings_func(widget, func, name=None):
    name = _get_name_from_widget(widget, name)
    qsettings = QSettings(APP_NAME, APP_NAME)
    qsettings.setValue(name, func())


def widget_read_settings_func(widget, name=None):
    name = _get_name_from_widget(widget, name)
    qsettings = QSettings(APP_NAME, APP_NAME)
    variant = qsettings.value(name)
    return variant
