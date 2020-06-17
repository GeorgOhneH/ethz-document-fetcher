from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtSvg import QSvgWidget

import os
import logging

from core.exceptions import ParseTemplateError
from core import template_parser
from settings import settings

logger = logging.getLogger(__name__)


class SVGWidget(QSvgWidget):
    def __init__(self, path, width, height, parent):
        super().__init__(parent=parent)
        self.load(path)
        self.setFixedSize(width, height)


class ImageLabel(QLabel):
    def __init__(self, path, width, height, parent=None):
        super().__init__(parent=parent)
        self.image = QPixmap(path)
        self.image = self.image.scaled(width, height)
        self.setFixedSize(width, height)
        self.setPixmap(self.image)


class MovieLabel(QLabel):
    def __init__(self, path, width, height, parent=None):
        super().__init__(parent=parent)

        self.movie = QMovie(path, QByteArray(), self)
        self.movie.setScaledSize(QSize(width, height))

        self.setFixedSize(width, height)

        self.movie.setCacheMode(QMovie.CacheAll)
        self.movie.setSpeed(200)
        self.setMovie(self.movie)
        self.movie.start()


class TreeWidgetItemName(QWidget):
    LOADING_GIF_PATH = "gui/images/loading.gif"
    IDLE_IMAGE_PATH = "gui/images/idle.png"
    WARNING_SVG_PATH = "gui/images/warning.svg"
    ERROR_SVG_PATH = "gui/images/error.svg"
    SUCCESS_SVG_PATH = "gui/images/success.svg"

    def __init__(self, text, parent=None):
        super().__init__(parent=parent)
        self.text = QLabel()
        self.text.setText(text)
        self.text.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        size = self.text.minimumSizeHint().height()

        self.stateWidget = QStackedWidget()
        self.stateWidget.setMaximumSize(size, size)

        main_layout = QHBoxLayout()
        main_layout.setAlignment(Qt.AlignLeft)
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.addWidget(self.text)
        main_layout.addWidget(self.stateWidget)

        self.setLayout(main_layout)

        self.loading_movie = MovieLabel(self.LOADING_GIF_PATH, size, size, self)
        self.idle_image = ImageLabel(self.IDLE_IMAGE_PATH, size, size, self)
        self.warning_svg = SVGWidget(self.WARNING_SVG_PATH, size, size, self)
        self.error_svg = SVGWidget(self.ERROR_SVG_PATH, size, size, self)
        self.success_svg = SVGWidget(self.SUCCESS_SVG_PATH, size, size, self)

        self.stateWidget.addWidget(self.loading_movie)
        self.stateWidget.addWidget(self.idle_image)
        self.stateWidget.addWidget(self.warning_svg)
        self.stateWidget.addWidget(self.error_svg)
        self.stateWidget.addWidget(self.success_svg)

        self.set_idle()

    def set_idle(self):
        self.stateWidget.hide()
        self.stateWidget.setCurrentWidget(self.idle_image)

    def set_loading(self, msg=None):
        if msg is not None:
            self.loading_movie.setToolTip(msg)
        self.stateWidget.show()
        self.stateWidget.setCurrentWidget(self.loading_movie)

    def set_error(self, msg=None):
        if msg is not None:
            self.error_svg.setToolTip(msg)
        self.stateWidget.show()
        self.stateWidget.setCurrentWidget(self.error_svg)

    def set_warning(self, msg=None):
        if msg is not None:
            self.warning_svg.setToolTip(msg)
        self.stateWidget.show()
        self.stateWidget.setCurrentWidget(self.warning_svg)

    def set_success(self, msg=None):
        if msg is not None:
            self.success_svg.setToolTip(msg)
        self.stateWidget.show()
        self.stateWidget.setCurrentWidget(self.success_svg)


class TreeWidgetItem(QTreeWidgetItem):
    STATE_IDLE = 0
    STATE_LOADING = 1
    STATE_ERROR = 2
    STATE_WARNING = 3
    STATE_SUCCESS = 4

    def __init__(self, template_node):
        super().__init__()
        self.name_widget = TreeWidgetItemName(template_node.gui_name())

        self.active_item_count = 0
        self.state = None
        self.template_node = template_node
        self.children = []
        self.custom_parent = None

    def init_widgets(self):
        self.treeWidget().setItemWidget(self, 0, self.name_widget)
        self.setExpanded(True)
        self._set_state(self.STATE_IDLE)

    def _set_state(self, state):
        self.state = state
        if self.state == self.STATE_IDLE:
            self.setText(1, "Idle")
        elif self.state == self.STATE_LOADING:
            self.setText(1, "Loading")
        elif self.state == self.STATE_SUCCESS:
            self.setText(1, "Finished")
        elif self.state == self.STATE_ERROR:
            self.setText(1, "Error")
        elif self.state == self.STATE_WARNING:
            self.setText(1, "Warning")

    def set_idle(self):
        self.active_item_count = 0
        self._set_state(self.STATE_IDLE)
        self.name_widget.set_idle()

    def set_loading(self, msg=None):
        self.active_item_count += 1
        self._set_state(self.STATE_LOADING)
        self.name_widget.set_loading(msg)

    def set_error(self, msg=None):
        self.active_item_count = 0
        self._set_state(self.STATE_ERROR)
        self.name_widget.set_error(msg)

    def set_warning(self, msg=None):
        self.active_item_count = 0
        self._set_state(self.STATE_WARNING)
        self.name_widget.set_warning(msg)

    def set_success(self, msg=None):
        self.active_item_count -= 1
        if self.active_item_count < 0:
            logger.warning("Active count is negative")
        if self.active_item_count == 0:
            self._set_state(self.STATE_SUCCESS)
            self.name_widget.set_success(msg)


class TemplateViewTree(QTreeWidget):
    folder_name_updated = pyqtSignal()
    base_path_updated = pyqtSignal()

    def __init__(self, signals, parent):
        super().__init__(parent=parent)
        self.widgets = {}
        self.setColumnCount(3)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.prepare_menu)
        self.template = template_parser.Template(settings.template_path)
        try:
            self.template.load()
        except Exception as e:
            error_dialog = QErrorMessage(self)
            error_dialog.showMessage(f"Error while loading the file. Error: {e}")
        self.init_view_tree()
        self.read_settings()

        self.setup_connections(signals)
        qApp.aboutToQuit.connect(self.save_state)

    def setup_connections(self, signals):
        signals.stopped.connect(self.stop_widgets)
        signals.finished.connect(self.quit_widgets)

        signals.update_folder_name.connect(self.update_folder_name)

        signals.update_base_path.connect(self.update_base_path)

        signals.site_started[str].connect(self.site_started)
        signals.site_started[str, str].connect(self.site_started)

        signals.site_finished_successful[str].connect(self.site_finished_successful)
        signals.site_finished_successful[str, str].connect(self.site_finished_successful)

        signals.site_quit_with_warning[str].connect(self.site_quit_with_warning)
        signals.site_quit_with_warning[str, str].connect(self.site_quit_with_warning)

        signals.site_quit_with_error[str].connect(self.site_quit_with_error)
        signals.site_quit_with_error[str, str].connect(self.site_quit_with_error)

    def save_state(self):
        qsettings = QSettings("eth-document-fetcher", "eth-document-fetcher")
        qsettings.setValue("templateViewTree/geometry", self.header().saveGeometry())
        qsettings.setValue("templateViewTree/windowState", self.header().saveState())

    def read_settings(self):
        qsettings = QSettings("eth-document-fetcher", "eth-document-fetcher")
        if qsettings.value("templateViewTree/geometry") is not None:
            self.header().restoreGeometry(qsettings.value("templateViewTree/geometry"))
        if qsettings.value("templateViewTree/windowState") is not None:
            self.header().restoreState(qsettings.value("templateViewTree/windowState"))

    @pyqtSlot(str, str)
    def update_folder_name(self, unique_key, folder_name):
        logger.debug(f"{unique_key} folder_name got updated to {folder_name}")
        self.widgets[unique_key].template_node.folder_name = folder_name
        self.folder_name_updated.emit()

    @pyqtSlot(str, str)
    def update_base_path(self, unique_key, base_path):
        logger.debug(f"{unique_key} base_path got updated to {base_path}")
        self.widgets[unique_key].template_node.base_path = base_path
        self.base_path_updated.emit()

    @pyqtSlot(str)
    @pyqtSlot(str, str)
    def site_started(self, unique_key, msg=None):
        self.widgets[unique_key].set_loading(msg)

    @pyqtSlot(str)
    @pyqtSlot(str, str)
    def site_finished_successful(self, unique_key, msg=None):
        widget = self.widgets[unique_key]
        widget.set_success(msg)

    @pyqtSlot(str)
    @pyqtSlot(str, str)
    def site_quit_with_warning(self, unique_key, msg=None):
        widget = self.widgets[unique_key]
        widget.set_warning(msg)

    @pyqtSlot(str)
    @pyqtSlot(str, str)
    def site_quit_with_error(self, unique_key, msg=None):
        widget = self.widgets[unique_key]
        widget.set_error(msg)

    @pyqtSlot()
    def reset_widgets(self):
        for key, widget in self.widgets.items():
            widget.set_idle()

    @pyqtSlot()
    def stop_widgets(self):
        for key, widget in self.widgets.items():
            if widget.state == widget.STATE_LOADING:
                widget.set_warning("Interrupted by user")

    @pyqtSlot()
    def quit_widgets(self):
        for key, widget in self.widgets.items():
            if widget.state == widget.STATE_LOADING:
                widget.set_error("Site did not give a finish Signal. (You should never see this message)")

    def add_item_widget(self, template_node, unique_key, widget_parent=None):
        widget = TreeWidgetItem(template_node)
        if widget_parent is None:
            self.addTopLevelItem(widget)
        else:
            widget_parent.addChild(widget)

        self.widgets[unique_key] = widget
        return widget

    def prepare_menu(self, point):
        widget = self.itemAt(point)
        if widget is None:
            return

        menu = QMenu(self)

        run_action = menu.addAction("Run recursive")
        run_action.setEnabled(not self.parent().thread.isRunning())
        if self.parent().thread.isRunning():
            self.parent().thread.finished.connect(lambda: run_action.setEnabled(True))
        run_action.triggered.connect(lambda: self.parent().start_thread(widget.template_node.unique_key, True))

        run_action = menu.addAction("Run")
        run_action.setEnabled(not self.parent().thread.isRunning())
        if self.parent().thread.isRunning():
            self.parent().thread.finished.connect(lambda: run_action.setEnabled(True))
        run_action.triggered.connect(lambda: self.parent().start_thread(widget.template_node.unique_key, False))

        menu.addSeparator()

        open_folder_action = menu.addAction("Open Folder")
        if widget.template_node.base_path is not None:
            base_path = os.path.join(settings.base_path, widget.template_node.base_path)
            if not os.path.exists(base_path):
                open_folder_action.setEnabled(False)
            url = QUrl.fromLocalFile(base_path)
            open_folder_action.triggered.connect(lambda: QDesktopServices.openUrl(url))
        else:
            open_folder_action.setEnabled(False)

        menu.exec_(self.mapToGlobal(point))

    def init_view_tree(self):
        if self.template.root.folder is not None:
            self.init_widgets(self.template.root.folder, parent=None)
        for site in self.template.root.sites:
            self.init_widgets(site, parent=None)

        for key, widget in self.widgets.items():
            widget.init_widgets()

    def init_widgets(self, node, parent):
        widget = self.add_item_widget(node, node.unique_key, parent)

        if node.folder is not None:
            self.init_widgets(node.folder, parent=widget)
        for site in node.sites:
            self.init_widgets(site, parent=widget)


class SubInfoView(object):
    def __init__(self, name):
        self.name = name
        self.button = QPushButton(name)
        self.button.setCheckable(True)

    def detect_change_selected(self, selected_widget):
        pass


class FolderView(QTreeView, SubInfoView):
    def __init__(self, parent=None):
        super().__init__(parent=parent, name="Folder")
        self.model = QFileSystemModel()
        self.setModel(self.model)

    def change_root(self, path):
        index = self.model.setRootPath(path)
        self.setRootIndex(index)

    def detect_change_selected(self, selected_widget):
        path = selected_widget.template_node.base_path
        absolute_path = os.path.join(settings.base_path, path)
        if path is not None:
            self.change_root(absolute_path)


class GeneralInformation(QLabel, SubInfoView):
    def __init__(self, parent=None):
        super().__init__(parent=parent, name="General")


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


class StackedWidgetView(QStackedWidget):
    def __init__(self, view_tree):
        super().__init__()
        self.view_tree = view_tree
        self.button_group = ButtonGroup()
        self.button_widget = QWidget()
        self.layout_button = QHBoxLayout()
        self.button_widget.setLayout(self.layout_button)

        self.views = [
            GeneralInformation(),
            FolderView(),
        ]

        self.init_views()

        self.button_group.buttonClicked.connect(self.change_state_widget)

        self.change_state_widget()

    def init_views(self):
        for view in self.views:
            self.addWidget(view)
            self.button_group.addButton(view.button)
            self.layout_button.addWidget(view.button)

            self.view_tree.itemSelectionChanged.connect(lambda: self.only_if_one_selected(view))

    def only_if_one_selected(self, view):
        selected_widgets = self.view_tree.selectedItems()
        if len(selected_widgets) != 1:
            return
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
    def __init__(self, signals, parent=None):
        super().__init__(parent=parent)
        self.template_view_tree = TemplateViewTree(signals, self)

        self.layout = QVBoxLayout()

        self.splitter = Splitter()
        self.state_widget = StackedWidgetView(self.template_view_tree)

        self.splitter.addWidget(self.template_view_tree)
        self.splitter.addWidget(self.state_widget)

        self.layout.addWidget(self.splitter)

        self.layout.addWidget(self.state_widget.button_widget)

        self.setLayout(self.layout)
