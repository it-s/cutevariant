## ================= Settings widgets ===================
# Qt imports
from PySide2.QtCore import *
from PySide2.QtWidgets import *

# Custom imports
from cutevariant.gui.plugin import PluginSettingsWidget
from cutevariant.gui.settings import AbstractSettingsWidget
from cutevariant.gui import FIcon
import cutevariant.commons as cm

import typing


def open_link(url: str):
    if url == "#annotation-reference-database-guidelines":
        dialog = AnnotationsReferenceDatabaseGuidelines()
        dialog.show()


class AnnotationsReferenceDatabaseGuidelines(QDialog):
    def __init__(self, parent: typing.Optional[QWidget], f: Qt.WindowFlags) -> None:
        super().__init__(parent=parent, f=f)
        self.label = QLabel(
            self.tr(
                """<b>Annotation reference database guidelines</b>
Every file with a db extension in the annotations reference folder <b>must</b> comply with the following guidelines:
- Be a sqlite3 database file
- Contain at least one table named 'annotations'
- Follow this schema for the 'annotations' table:
CREATE TABLE annotations (
        id INTEGER PRIMARY KEY,
        transcript_name TEXT, 
        tx_start INTEGER, 
        tx_end INTEGER,
        cds_start INTEGER,
        cds_end INTEGER,
        exon_starts TEXT,
        exon_ends TEXT,
        gene TEXT
        )
"""
            ),
            self,
        )
        layout = QVBoxLayout(self)
        layout.addWidget(self.label)
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok, self)
        layout.addWidget(self.button_box)
        self.button_box.accepted.connect(self.accept)


class AnnotationReferenceDatabaseCreator(QDialog):
    """Dialog that ensures that the user creates a valid annotation reference database.
    This dialog should be called whenever the user clicks the 'Add' button in the AnnotationReferenceDatabase geneviewer setting.
    """

    def __init__(self, parent: typing.Optional[QWidget], f: Qt.WindowFlags) -> None:
        super().__init__(parent=parent, f=f)

        self.label_instructions = QLabel(
            self.tr(
                """You are about to add an annotations reference database to the gene viewer.
You can either generate it from a zipped text file, or you can choose to copy an existing db file into the selected directory.
Note, though, that every db file in the annotations reference database folder <b>must<b/> follow these <a href='#annotation-reference-database-guidelines'>guidelines</a>"""
            ),
            self,
        )
        self.label_instructions.linkActivated.connect(open_link)


class AnnotationReferenceDatabaseSettings(AbstractSettingsWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(self.tr("Annotation reference databases"))

        self._database_folder_path = QDir.homePath()
        self.line_edit_database_folder_path = QLineEdit(self)
        self.line_edit_database_folder_path.setPlaceholderText(
            self.tr("Annotation reference databases folder")
        )
        self.choose_db_folder_act = self.line_edit_database_folder_path.addAction(
            FIcon(0xF0770), QLineEdit.TrailingPosition
        )
        self.choose_db_folder_act.triggered.connect(
            self.on_select_annotation_reference_database
        )

        self.label_folder_description = QLabel(
            self.tr(
                """This is where cutevariant will look for annotation reference databases.
Every file in this folder with a .db extension must comply with the <a href='#annotation-reference-database-guidelines'>following guidelines</a>
"""
            ),
            self,
        )
        self.label_folder_description.linkActivated.connect(open_link)

        vboxlayout = QVBoxLayout(self)
        vboxlayout.addWidget(self.line_edit_database_folder_path)
        vboxlayout.addWidget(self.label_folder_description)

    def on_select_annotation_reference_database(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            self.tr("Please choose a folder with annotation reference databases"),
            self._database_folder_path,
        )
        if folder:
            self._database_folder_path = folder

    def save(self):
        """Override from PageWidget"""
        pass

    def load(self):
        """Override from PageWidget"""

        # Load view that lists all available annotation reference databases
        settings = self.create_settings()
        self._database_folder_path = settings.value(
            "database_folder_path", QDir.homePath()
        )
        self.line_edit_database_folder_path.setText(self._database_folder_path)


class GeneViewerSettingsWidget(PluginSettingsWidget):
    """Instantiated plugin in the settings panel of Cutevariant

    Allows users to choose the annotation database used by the geneviewer.
    It is the responsibility of the user to have a database with gene name entries that match gene names from the VCF they are analyzing.
    """

    ENABLE = True

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowIcon(FIcon(0xF0D01))
        self.setWindowTitle("Gene viewer")
        self.add_page(AnnotationReferenceDatabaseSettings())
