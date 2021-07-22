"""List of classes used for settings window

A SettingsDialog is a collection of section ( SectionWidget ) 
which contains multiple page ( AbstractSettingsWidget ) to save and load settings thanks to QSettings.

* SettingsDialog: 
Main widget for settings window that instantiate all subsection widget

* SectionWidget: 
Handy class to group similar settings widgets in tabs (used by SettingsDialog).

* AbstractSettingsWidget:
Abstract class for build a page settings
    
    Subclasses:
        - TranslationSettingsWidget: Allow to choose a language for the interface
        - ProxySettingsWidget: Allow to configure proxy settings for widgets that require internet connection
        - StyleSettingsWidget
        - PluginsSettingsWidget
        - VariantSettingsWidget: Allow to add personal templates to search a variant in a third-party database

Exemples: 

    # Create sub-section  

    class MemorySettings(BaseSettings):
        def save():
            settings = self.create_settings()
            settings.setValue("value", 10)    

        def load():
            settings = self.create_settings()
            value = settings.value("value")
               

    class DiskSettings(BaseSettings):
        def save():
            settings = self.create_settings()
            settings.setValue("value", 10)    

        def load():
            settings = self.create_settings()
            value = settings.value("value")

    # create one section 
    performance_section = SectionWidget()
    performance_section.add_setting_widget(MemorySettings)
    performance_section.add_setting_widget(DiskSettings)

    # add section to the main settings widge 
    widget = SettingsWidget()
    widget.add_section(widget)

    widget.save_all()

"""
# Standard imports
import os
import glob
from abc import abstractmethod
from logging import DEBUG
import typing

import copy

# Qt imports
from PySide2.QtWidgets import *
from PySide2.QtCore import *  # QApplication.instance()
from PySide2.QtGui import *  # QIcon, QPalette
from cutevariant import config

# Custom imports
import cutevariant.commons as cm
from cutevariant.config import Config
from cutevariant.gui.ficon import FIcon
from cutevariant.gui import network, style, widgets

from cutevariant import LOGGER

DEFAULT_CONFIG_NAME = "Factory settings"


class AbstractSettingsWidget(QWidget):
    """Abstract class for settings widgets

    User must reimplement load(), save() and reset()

    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("base")
        self.setWindowIcon(FIcon(0xF5CA))
        self.section_widget = None

    @abstractmethod
    def save(self):
        """Save the current widget settings in QSettings"""
        raise NotImplementedError(self.__class__.__name__)

    @abstractmethod
    def load(self):
        """Load settings from QSettings"""
        raise NotImplementedError(self.__class__.__name__)

    @abstractmethod
    def reset(self, config_file: str):
        """Reset to default settings"""
        raise NotImplementedError(self.__class__.__name__)


class SectionWidget(QTabWidget):
    """Handy class to group similar settings page in tabs"""

    def __init__(self, parent=None):
        super().__init__(parent)

    def add_page(self, widget: AbstractSettingsWidget):
        widget.section_widget = self
        self.addTab(widget, widget.windowIcon(), widget.windowTitle())

    def save(self):
        """Call save() method of all widgets in the SectionWidget"""
        [self.widget(index).save() for index in range(self.count())]

    def load(self):
        """Call load() method of all widgets in the SectionWidget"""
        [self.widget(index).load() for index in range(self.count())]

    def reset(self, config_file: str):
        """Call reset() method of all widgets in the SectionWidget"""
        [self.widget(index).reset(config_file) for index in range(self.count())]


################################################################################
# class TranslationSettingsWidget(AbstractSettingsWidget):
#     """Allow to choose a language for the interface"""

#     def __init__(self):
#         super().__init__()
#         self.setWindowTitle(self.tr("Translation"))
#         self.setWindowIcon(FIcon(0xF05CA))
#         self.locales_combobox = QComboBox()
#         mainLayout = QFormLayout()
#         mainLayout.addRow(self.tr("&Choose a locale:"), self.locales_combobox)

#         self.setLayout(mainLayout)
#         # self.locales_combobox.currentTextChanged.connect(self.switchTranslator)

#     def save(self):
#         """Switch QApplication.instance() translator with the selected one and save it into config

#         .. note:: settings are stored in "ui" group
#         .. todo:: Handle the propagation the LanguageChange event
#             https://doc.qt.io/Qt-5/qcoreapplication.html#installTranslator
#             https://wiki.qt.io/How_to_create_a_multi_language_application
#         """

#         # Remove the old translator
#         # QApplication.instance().removeTranslator(translator)

#         # Load the new translator

#         # Save locale setting
#         locale_name = self.locales_combobox.currentText()

#         app_translator = QTranslator(QApplication.instance())
#         if app_translator.load(locale_name, cm.DIR_TRANSLATIONS):
#             QApplication.instance().installTranslator(app_translator)

#     def load(self):
#         """Setup widgets in TranslationSettingsWidget"""
#         self.locales_combobox.clear()
#         # Get names of locales based on available files
#         available_translations = {
#             os.path.basename(os.path.splitext(file)[0]): file
#             for file in glob.glob(cm.DIR_TRANSLATIONS + "*.qm")
#         }
#         # English is the default language
#         available_locales = list(available_translations.keys()) + ["en"]
#         self.locales_combobox.addItems(available_locales)

#         # Display current locale
#         settings = self.create_settings()
#         locale_name = settings.value("ui/locale", "en")

#         self.locales_combobox.setCurrentIndex(available_locales.index(locale_name))


class ProxySettingsWidget(AbstractSettingsWidget):
    """Allow to configure proxy settings for widgets that require internet connection"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(self.tr("Network"))
        self.setWindowIcon(FIcon(0xF0484))

        self.combo_box = QComboBox()
        self.host_edit = QLineEdit()
        self.port_edit = QSpinBox()
        self.user_edit = QLineEdit()
        self.pass_edit = QLineEdit()

        # Load proxy type
        for key in network.PROXY_TYPES:
            self.combo_box.addItem(key, network.PROXY_TYPES[key])

        # edit restriction
        self.pass_edit.setEchoMode(QLineEdit.PasswordEchoOnEdit)

        f_layout = QFormLayout()
        f_layout.addRow(self.tr("Type"), self.combo_box)
        f_layout.addRow(self.tr("Proxy host"), self.host_edit)
        f_layout.addRow(self.tr("Proxy Port"), self.port_edit)
        f_layout.addRow(self.tr("Username"), self.user_edit)
        f_layout.addRow(self.tr("Password"), self.pass_edit)

        self.combo_box.currentIndexChanged.connect(self.on_combo_changed)

        self.setLayout(f_layout)

    def save(self):
        """Save settings under "proxy" group"""
        config = Config("app")
        network = {}
        network["type"] = self.combo_box.currentIndex()
        network["host"] = self.host_edit.text()
        network["port"] = self.port_edit.value()
        network["username"] = self.user_edit.text()
        network["password"] = self.pass_edit.text()

        config["network"] = network
        config.save()

    def load(self):
        """Load "proxy" group settings"""

        config = Config("app")

        network = config.get("network", {})

        s_type = network.get("type", 0)
        if s_type:
            self.combo_box.setCurrentIndex(int(s_type))

        self.host_edit.setText(network.get("host", ""))

        s_port = network.get("port", 0)
        if s_port:
            self.port_edit.setValue(int(s_port))

        self.user_edit.setText(network.get("username", ""))
        self.pass_edit.setText(network.get("password", ""))

    def reset(self, config_file: str):
        config = Config("app", config_file)
        config.save()
        self.load()

    def on_combo_changed(self, index):
        """disable formular when No proxy"""
        if index == 0:
            self._disable_form(True)
        else:
            self._disable_form(False)

    def _disable_form(self, disabled=True):
        """Disabled formular"""
        self.host_edit.setDisabled(disabled)
        self.port_edit.setDisabled(disabled)
        self.user_edit.setDisabled(disabled)
        self.pass_edit.setDisabled(disabled)


class ConfigModel(QAbstractListModel):
    def __init__(self) -> None:
        super().__init__()
        self.config_list = []

    def add_config(
        self,
        name: str,
        file_path: str,
    ) -> bool:
        """Adds a config to the model.
        Configs are dictionnaries with:
            - name: How the user refers to the config
            - file_path: A string indicating the path to a config preset

        Args:
            name (str): The name of the config, as displayed to the user
            file_path (str): The path to the config preset

        Returns:
            bool: True on success
        """
        if any(conf["name"] == name for conf in self.config_list):
            # If there is already a link with the same name in the model, don't add it (avoid doubles)
            return False

        new_config = {"name": name, "file_path": file_path}

        # Add the new link to the model. Potentially affects current default link, so reset the whole model
        self.beginResetModel()

        self.config_list.append(new_config)

        self.endResetModel()
        return True

    def remove_configs(self, indexes: typing.List[QModelIndex]) -> bool:
        """Safely removes several configs from a list of their indexes

        Args:
            indexes (List[QModelIndex]): List of indexes to remove

        Returns:
            bool: True on success
        """
        rows = sorted([index.row() for index in indexes], reverse=True)
        for row in rows:
            self.beginRemoveRows(QModelIndex(), row, row)
            del self.config_list[row]
            self.endRemoveRows()
        return True

    def remove_config(self, index: QModelIndex):
        return self.remove_configs([index])

    def edit_config(
        self,
        index: QModelIndex,
        name: str,
        file_path: str,
    ):

        edited_config = {
            "name": name,
            "file_path": file_path,
        }

        # Add the new link to the model. Potentially affects current default link, so reset the whole model
        self.beginResetModel()
        self.config_list[index.row()] = edited_config
        self.endResetModel()
        return True

    def load(self, configs: typing.List[dict]):
        self.beginResetModel()
        self.config_list.clear()
        for i, conf in enumerate(configs):
            if not os.path.isfile(conf["file_path"]):
                self.config_list.append(copy.deepcopy(conf))
                self.config_list[i]["color"] = "#FF0000"
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self.config_list)

    def clear(self):
        self.beginResetModel()
        self.config_list.clear()
        self.endResetModel()

    def data(self, index: QModelIndex, role: int):
        if index.row() < 0 or index.row() >= self.rowCount():
            return

        if role == Qt.DisplayRole or role == Qt.EditRole:
            return self.config_list[index.row()]["name"]

        if role == Qt.ToolTipRole:
            return self.config_list[index.row()]["file_path"]

        if role == Qt.ForegroundRole:
            if "color" in self.config_list[index.row()]:
                return QColor(self.config_list[index.row()]["color"])

    def setData(self, index: QModelIndex, value: typing.Any, role: int) -> bool:
        if isinstance(value, str) and role == Qt.EditRole:
            self.config_list[index.row()]["name"] = value

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        return super().flags(index) | Qt.ItemIsEditable


class ConfigDialog(QDialog):
    def __init__(self, name="", file_path="", parent: QWidget = None) -> None:
        super().__init__(parent=parent)

        self.setWindowTitle(self.tr("Edit config"))

        self._layout = QVBoxLayout(self)

        self._button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self._button_box.accepted.connect(self.accept)
        self._button_box.rejected.connect(self.reject)

        self.form_layout = QFormLayout()
        self.name = QLineEdit(self)
        self.path_le = QLineEdit(self)

        self.name.setPlaceholderText(self.tr("Name"))
        self.path_le.setPlaceholderText(self.tr("File path"))
        self.edit_path_action = self.path_le.addAction(
            FIcon(0xF1080), QLineEdit.TrailingPosition
        )
        self.edit_path_action.triggered.connect(self.edit_path)

        # When we click, we change tag's color

        self.form_layout.addRow(self.tr("Name:"), self.name)
        self.form_layout.addRow(self.tr("File path:"), self.path_le)

        self._layout.addLayout(self.form_layout)
        self._layout.addWidget(self._button_box)

        self.set_conf(name, file_path)

    def set_conf(self, name: str = "", file_path: str = ""):
        self.name.setText(name)
        self.path_le.setText(file_path)

    def get_conf(self) -> dict:
        return {"name": self.name.text(), "file_path": self.path_le.text()}

    def edit_path(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, self.tr("Please choose a configuration file"), QDir.homePath()
        )
        if file_name:
            self.path_le.setText(file_name)

    def accept(self) -> None:
        if self.name.text() == DEFAULT_CONFIG_NAME:
            QMessageBox.warning(
                self,
                self.tr("Reserved name"),
                self.tr(
                    f"{DEFAULT_CONFIG_NAME} is a reserved name, you cannot use it as a config name"
                ),
            )
            # Return without accepting, form is considered invalid
            return
        if not os.path.isfile(self.path_le.text()):
            QMessageBox.warning(
                self,
                self.tr("File not found"),
                self.tr(f"File {self.path_le.text()} does not exist"),
            )
            # Return without accepting, form is considered invalid
            return

        # Use realpath so that even if one creates a symlink to default_config.yml, it is not used as a different config
        if os.path.realpath(self.path_le.text()) == Config().default_config_path:
            QMessageBox.warning(
                self,
                self.tr("Invalid file name"),
                self.tr(
                    f"File {self.path_le.text()} is a reserved file name. It corresponds to a Factory reset."
                ),
            )
            # Return without accepting, form is considered invalid
            return
        return super().accept()


class ConfigSettingsWidget(AbstractSettingsWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Edit configurations")
        self.label = QLabel(
            """
            Add/Edit/Remove configuration presets.
            These will be available in the 'Reset settings' popup menu.
            """
        )
        self.setWindowIcon(FIcon(0xF0493))
        self.view = QListView()
        self.model = ConfigModel()

        self.view.setModel(self.model)
        self.view.setSelectionMode(QAbstractItemView.SingleSelection)

        self.add_button = QPushButton(self.tr("Add"))
        self.rem_button = QPushButton(self.tr("Remove"))
        self.clear_button = QPushButton(self.tr("Clear"))
        self.edit_button = QPushButton(self.tr("Edit"))

        h_layout = QHBoxLayout(self)
        h_layout.addWidget(self.view)
        v_layout = QVBoxLayout()
        v_layout.addWidget(self.add_button)
        v_layout.addWidget(self.edit_button)
        v_layout.addWidget(self.rem_button)
        v_layout.addStretch()
        v_layout.addWidget(self.clear_button)
        h_layout.addLayout(v_layout)

        self.add_button.clicked.connect(self.on_add)
        self.rem_button.clicked.connect(self.on_remove)
        self.clear_button.clicked.connect(self.on_clear)
        self.edit_button.clicked.connect(self.on_edit)

    def save(self):
        config = Config("app")
        config["configs"] = self.model.config_list
        config.save()

    def load(self):
        config: Config = Config("app")
        _configs = config.get("configs", [])
        if isinstance(_configs, list):
            if all(isinstance(conf, dict) for conf in _configs):
                self.model.load(_configs)

    def reset(self, config_file: str):
        config = Config("app", config_file)
        config.save()
        self.load()

    def on_add(self):
        dialog = ConfigDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.model.add_config(**dialog.get_conf())

    def on_edit(self):
        index = self.view.currentIndex()
        name, file_path = index.data(Qt.DisplayRole), index.data(Qt.ToolTipRole)
        dialog = ConfigDialog(name, file_path)

        if dialog.exec_() == QDialog.Accepted:
            _conf = dialog.get_conf()
            self.model.edit_config(index, _conf["name"], _conf["file_path"])

    def on_remove(self):
        self.model.remove_configs(self.view.selectionModel().selectedRows())

    def on_clear(self):
        self.model.clear()


class StyleSettingsWidget(AbstractSettingsWidget):
    """Allow to choose a style for the interface"""

    def __init__(self):
        """Init StyleSettingsWidget

        Args:
            mainwindow (QMainWindow): Current main ui of cutevariant;
                Used to refresh the plugins
        """
        super().__init__()
        self.setWindowTitle(self.tr("Styles"))
        self.setWindowIcon(FIcon(0xF03D8))

        self.styles_combobox = QComboBox()
        mainLayout = QFormLayout()
        mainLayout.addRow(self.tr("&Choose a style:"), self.styles_combobox)

        self.setLayout(mainLayout)

    def save(self):
        """Save the selected style in config"""
        # Get previous style

        config = Config("app")
        style = config.get("style", {})

        old_style_name = style.get("theme", cm.BASIC_STYLE)

        # Save style setting
        style_name = self.styles_combobox.currentText()
        if old_style_name == style_name:
            return

        style["theme"] = style_name

        config["style"] = style
        config.save()

        QMessageBox.information(
            self, "restart", self.tr("Please restart application to apply theme")
        )

        # Clear pixmap cache
        QPixmapCache.clear()

    def load(self):
        """Setup widgets in StyleSettingsWidget"""
        self.styles_combobox.clear()

        # Get names of styles based on available files
        available_styles = {
            os.path.basename(os.path.splitext(file)[0]).title(): file
            for file in glob.glob(cm.DIR_STYLES + "*.qss")
            if "frameless" not in file
        }
        # Display available styles
        available_styles = list(available_styles.keys()) + [cm.BASIC_STYLE]
        self.styles_combobox.addItems(available_styles)

        print(available_styles)

        # Display current style
        # Dark is the default style
        config = Config("app")
        style = config.get("style", {})
        style_name = style.get("theme", cm.BASIC_STYLE)
        self.styles_combobox.setCurrentIndex(available_styles.index(style_name))

    def reset(self, config_file: str):
        config = Config("app", config_file)
        config.save()
        self.load()


class PluginsSettingsWidget(AbstractSettingsWidget):
    """Display a list of found plugin and their status (enabled/disabled)"""

    registerPlugin = Signal(dict)
    deregisterPlugin = Signal(dict)

    def __init__(self):
        super().__init__()
        self.setWindowTitle(self.tr("Plugins"))
        self.setWindowIcon(FIcon(0xF0431))
        self.view = QTreeWidget()
        self.view.setColumnCount(3)
        self.view.setHeaderLabels(["Name", "Description", "Version"])
        self.view.header().setSectionResizeMode(QHeaderView.ResizeToContents)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.view)
        self.setLayout(main_layout)

    def save(self):
        pass
        """Save the check status of enabled plugins in app settings and update UI

        Emit a `register_plugin` or `deregister_plugin` signal for the mainwindow.

        Notes:
            Called only if the user clicks on "save all" button.
        """
        # for iterator in QTreeWidgetItemIterator(
        #     self.view, QTreeWidgetItemIterator.Enabled
        # ):
        #     item = iterator.value()
        #     # Get extension and check state
        #     extension = item.data(0, Qt.UserRole)
        #     check_state = item.checkState(0) == Qt.Checked
        #     # Save status

        #     config = Config("app")

        #     plugin_conf = {}

        #     plugin_conf[""]
        #     settings.setValue(f"plugins/{extension['name']}/status", check_state)

        #     # Set the enable status of the extension
        #     for sub_extension_type in {
        #         "widget",
        #         "dialog",
        #         "setting",
        #     } & extension.keys():
        #         extension[sub_extension_type].ENABLE = check_state

        #     if check_state:
        #         # Register plugin in UI
        #         self.registerPlugin.emit(extension)
        #     else:
        #         # Deregister plugin in UI
        #         self.deregisterPlugin.emit(extension)

    def load(self):
        pass
        """Display the plugins and their status"""
        # self.view.clear()
        # from cutevariant.gui import plugin

        # settings = self.create_settings()

        # settings_keys = set(settings.allKeys())

        # for extension in plugin.find_plugins():
        #     displayed_title = (
        #         extension["name"]
        #         if LOGGER.getEffectiveLevel() == DEBUG
        #         else extension["title"]
        #     )
        #     item = QTreeWidgetItem()
        #     item.setText(0, displayed_title)
        #     item.setText(1, extension["description"])
        #     item.setText(2, extension["version"])

        #     # Is an extension enabled ?
        #     is_enabled = False

        #     # Get activation status
        #     # Only disabled extensions can be in settings
        #     key = f"plugins/{extension['name']}/status"
        #     activated_by_user = (
        #         settings.value(key) == "true" if key in settings_keys else None
        #     )

        #     for sub_extension_type in {
        #         "widget",
        #         "dialog",
        #         "setting",
        #     } & extension.keys():
        #         if activated_by_user is None and extension[sub_extension_type].ENABLE:
        #             is_enabled = True
        #             # Only disabled plugins can be reactivated by the user
        #             item.setDisabled(True)
        #             break
        #         if activated_by_user:
        #             is_enabled = True
        #             break

        #     item.setCheckState(0, Qt.Checked if is_enabled else Qt.Unchecked)
        #     # Attach the extension for its further activation/desactivation
        #     item.setData(0, Qt.UserRole, extension)

        #     self.view.addTopLevelItem(item)

    def reset(self, config_file: str):
        pass


# class PathSettingsWidget(AbstractSettingsWidget):
#     """ Path settings where to store shared data """

#     def __init__(self):
#         super().__init__()
#         self.setWindowTitle(self.tr("Global settings"))
#         self.setWindowIcon(FIcon(0xF1080))

#         self.edit = widgets.FileEdit()
#         self.edit.set_path_type("dir")
#         main_layout = QFormLayout()
#         main_layout.addRow("Preset path", self.edit)

#         self.setLayout(main_layout)

#     def save(self):
#         settings = QSettings()
#         if self.edit.exists():
#             settings.setValue("preset_path", self.edit.text())

#     def load(self):

#         settings = QSettings()
#         path = settings.value(
#             "preset_path",
#             QStandardPaths.writableLocation(QStandardPaths.GenericDataLocation),
#         )

#         self.edit.setText(path)


class SettingsDialog(QDialog):
    """Main widget for settings window

    Subwidgets are intantiated on panels; a SectionWidget groups similar widgets
    in tabs.

    Signals:
        uiSettingsChanged(Signal): Emitted when some settings of the GUI are
            modified and need a reload of all widgets to take effect.
    """

    uiSettingsChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Cutevariant - Settings"))
        self.setWindowIcon(QIcon(cm.DIR_ICONS + "app.png"))

        self.widgets = []

        self.list_widget = QListWidget()
        self.stack_widget = QStackedWidget()
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.SaveAll | QDialogButtonBox.Cancel | QDialogButtonBox.Reset
        )
        self.button_box.button(QDialogButtonBox.Cancel).clicked.connect(self.close)
        self.button_box.button(QDialogButtonBox.Reset).clicked.connect(self.reset_all)
        self.button_box.button(QDialogButtonBox.Reset).setMenu(
            self._create_reset_menu()
        )

        self.button_box.button(QDialogButtonBox.SaveAll).clicked.connect(self.save_all)

        self.list_widget.setFixedWidth(200)
        self.list_widget.setIconSize(QSize(32, 32))

        h_layout = QHBoxLayout()
        h_layout.addWidget(self.list_widget)
        h_layout.addWidget(self.stack_widget)

        v_layout = QVBoxLayout()
        v_layout.addLayout(h_layout)
        v_layout.addWidget(self.button_box)

        self.setLayout(v_layout)

        # Instantiate subwidgets on panels
        # Similar widgets for general configuration
        general_settings = SectionWidget()  #  Not a title !
        general_settings.setWindowTitle(self.tr("General"))
        general_settings.setWindowIcon(FIcon(0xF0614))

        # general_settings.add_page(PathSettingsWidget())

        # Cutevariant is  not yet translated ..
        # general_settings.add_page(TranslationSettingsWidget())

        general_settings.add_page(ProxySettingsWidget())
        general_settings.add_page(StyleSettingsWidget())
        general_settings.add_page(ConfigSettingsWidget())

        # Activation status of plugins
        plugin_settings = PluginsSettingsWidget()

        #  BOF...
        if parent:
            plugin_settings.registerPlugin.connect(parent.register_plugin)
            plugin_settings.deregisterPlugin.connect(parent.deregister_plugin)

        # Specialized widgets on panels
        self.add_section(general_settings)
        self.add_section(plugin_settings)
        self.load_plugins()

        self.resize(800, 400)

        # Connection events
        self.list_widget.currentRowChanged.connect(self.stack_widget.setCurrentIndex)

        # Load settings
        self.load_all()

        self.accepted.connect(self.close)

    def add_section(self, widget: SectionWidget):
        """Add a widget on the widow via a QStackedWidget; keep a reference on it
        for later connection/activation"""
        # Used to load/save all widgets on demand
        self.widgets.append(widget)
        # Used for ui positionning and connection events
        self.list_widget.addItem(
            QListWidgetItem(widget.windowIcon(), widget.windowTitle())
        )
        self.stack_widget.addWidget(widget)

    def save_all(self):
        """Call save() method of all widgets"""
        [widget.save() for widget in self.widgets]
        self.accept()

    def load_all(self):
        """Call reset() method of all widgets"""
        [widget.load() for widget in self.widgets]

    def _create_reset_menu(self):
        """Creates the dropdown menu to be popped up when the user presses reset.
        Each action in this menu will be connected to self's reset_all slot and should bring the file_name with them
        """
        menu = QMenu(self)
        config = Config("app")
        if "configs" in config:

            # Create 'Reset to factory settings' action
            reset_hard_act: QAction = menu.addAction(DEFAULT_CONFIG_NAME)
            reset_hard_act.setIcon(FIcon(0xF006E))
            reset_hard_act.triggered.connect(self.reset_all)

            # Record configs that do not contain valid file name. To avoid errors while loading file
            not_found_configs = []
            all_configs = config["configs"]
            for conf in all_configs:
                conf_name, conf_file = conf["name"], conf["file_path"]
                if not os.path.isfile(conf_file):
                    not_found_configs.append((conf_name, conf_file))
                    continue
                act: QAction = menu.addAction(conf_name)
                # Reset all will use file_path contained in action's data to reset settings
                act.setData(conf_file)
                # Useless, no tooltip in popup menus apparently
                act.setToolTip(conf_file)
                act.setIcon(FIcon(0xF0004))
                act.triggered.connect(self.reset_all)
            if not_found_configs:
                for not_found in not_found_configs:
                    LOGGER.debug(
                        "Could not find config named %s (%s does not name a file)",
                        not_found[0],
                        not_found[1],
                    )
        return menu

    def reset_all(self):
        """Called either from a QPushButton or from the reset drop-down menu"""
        if isinstance(self.sender(), QAction):
            config_file = None  # Exactly the same as Conf().default_config_path()
            reset_act: QAction = self.sender()
            if reset_act.data():
                config_file = reset_act.data()
        else:
            config_file = None  # Exactly the same as Conf().default_config_path()
        [widget.reset(config_file) for widget in self.widgets]

    def load_plugins(self):
        """Add plugins settings"""
        from cutevariant.gui import plugin

        for extension in plugin.find_plugins():

            if "setting" in extension:
                settings_widget_class = extension["setting"]
                if not settings_widget_class.ENABLE:
                    # Skip disabled plugins
                    continue

                widget = settings_widget_class()
                # Create rprefix settings ! For instance [VariantView]
                # widget.prefix_settings = widget.__class__.__name__.replace(
                #     "SettingsWidget", ""
                # )

                if not widget.windowTitle():
                    widget.setWindowTitle(extension["name"])

                if not widget.windowIcon():
                    widget.setWindowIcon(FIcon(0xF0431))

                self.add_section(widget)

    def reject(self) -> None:
        """Upon closing, or if the user presses cancel, ask for a confirmation before actually closing"""
        if (
            QMessageBox.question(
                self,
                self.tr("Closing"),
                self.tr(
                    "Your changes to the settings will not be saved. Close anyway?"
                ),
                QMessageBox.Yes | QMessageBox.No,
            )
            == QMessageBox.No
        ):
            # Will not close
            return
        # Will close (the base implementation)
        return super().reject()


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    d = SettingsDialog()
    d.show()

    app.exec_()
