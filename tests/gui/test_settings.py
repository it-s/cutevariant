from cutevariant import config
from tests import utils
import pytest
import tempfile

# Qt imports
from PySide2.QtWidgets import *
from PySide2.QtCore import *
from cutevariant.gui import settings
from cutevariant.config import Config
import os

# Standard imports
import pytest

# Qt imports

from tests import utils


class PageTest(settings.AbstractSettingsWidget):
    def __init__(self):
        super().__init__()
        self.value = None

    def save(self):
        config = Config("test")
        config["value"] = self.value
        config.save()

    def load(self):
        config = Config("test")
        # This resets in case the default value can't be found upon resetting
        self.value = config.get("value", 32)

    def reset(self, config_file: str):
        config = Config("test")
        config.reset()
        config.save()
        self.load()


def test_settings_dialog(qtbot):

    #  build a dialog
    dialog = settings.SettingsDialog()
    section = settings.SectionWidget()
    page = PageTest()
    section.add_page(page)
    dialog.add_section(section)

    # #  clear settings
    # page.create_settings().clear()
    # path = page.create_settings().fileName()

    qtbot.addWidget(dialog)
    dialog.show()

    page.value = 32

    #  Test Saving
    qtbot.mouseClick(dialog.button_box.button(QDialogButtonBox.SaveAll), Qt.LeftButton)

    ## is close ?
    assert not dialog.isVisible()

    ## is saved ?
    config = Config("test")

    assert config["value"] == 32

    # Test Loading

    # Didn't understand how to click on a popup menu action
    # page.value = None
    # dialog.show()
    # reset_button = dialog.button_box.button(QDialogButtonBox.Reset)
    # # Click it
    # qtbot.mouseClick(reset_button, Qt.LeftButton)
    # # And then, click on 'Factory settings'
    # qtbot.mouseClick(reset_button, Qt.LeftButton, pos=QPoint(15, 15))
    # assert page.value == 32
