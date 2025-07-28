import sys
import os
import glob
import logging
import threading
from typing import Optional, Dict, Any
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QLineEdit,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QMessageBox,
    QFileDialog,
    QComboBox,
    QProgressBar,
    QTextEdit,
    QGroupBox,
    QCheckBox,
    QSpinBox,
    QSlider,
    QSplitter,
)
from PyQt5.QtCore import Qt, QPoint, QThread, pyqtSignal, QTimer, QSettings
from PyQt5.QtGui import QPixmap, QFont, QPalette, QColor
from src.assets.gif_optimizer import GifOptimizer, OptimizationConfig
from dotenv import load_dotenv
from src.uiitems.close_button import CloseButton

load_dotenv()


class OptimizationWorker(QThread):
    """Worker thread for GIF optimization to prevent UI freezing"""

    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    finished = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def __init__(self, optimizer: GifOptimizer):
        super().__init__()
        self.optimizer = optimizer

    def run(self):
        try:
            # Connect progress callback
            self.optimizer.progress_callback = self.progress_updated.emit

            # Process the folder
            stats = self.optimizer.process_folder()
            self.finished.emit(stats)

        except Exception as e:
            self.error_occurred.emit(str(e))


def find_resource_path(base_path, filename_pattern):
    """
    Robustly find a resource file by pattern, supporting multiple extensions and locations.

    Args:
        base_path (str): Base directory to search in
        filename_pattern (str): Filename pattern to search for (e.g., "cover", "logo")

    Returns:
        str: Full path to the found file, or None if not found
    """
    # Common image extensions to try
    extensions = [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".webp"]

    # First try exact match with different extensions
    for ext in extensions:
        exact_path = os.path.join(base_path, f"{filename_pattern}{ext}")
        if os.path.exists(exact_path):
            return exact_path

    # If exact match fails, try pattern matching
    try:
        # Search for files containing the pattern
        pattern = os.path.join(base_path, f"*{filename_pattern}*")
        matches = glob.glob(pattern)

        # Filter by valid image extensions
        for match in matches:
            if os.path.isfile(match):
                file_ext = os.path.splitext(match)[1].lower()
                if file_ext in extensions:
                    return match
    except Exception:
        pass

    return None


def get_resource_path(resource_type, filename_pattern):
    """
    Get a resource path with fallback locations.

    Args:
        resource_type (str): Type of resource (e.g., "images", "icons", "logos")
        filename_pattern (str): Filename pattern to search for

    Returns:
        str: Full path to the found file, or None if not found
    """
    app_root = get_application_root()

    # Common resource locations to search
    search_paths = [
        os.path.join(app_root, "static", resource_type),
        os.path.join(app_root, "assets", resource_type),
        os.path.join(app_root, "resources", resource_type),
        os.path.join(app_root, resource_type),
        os.path.join(app_root, "static"),  # Fallback for logo images
        # For PyInstaller packaged apps, resources are in the same directory as exe
        os.path.join(app_root, "static", resource_type),
        os.path.join(app_root, "static"),
    ]

    for search_path in search_paths:
        if os.path.exists(search_path):
            found_path = find_resource_path(search_path, filename_pattern)
            if found_path:
                return found_path

    return None


def get_application_root():
    """
    Get the application root directory, handling both development and packaged scenarios.

    Returns:
        str: Path to the application root directory
    """
    if getattr(sys, "frozen", False):
        # Running as compiled executable
        return sys._MEIPASS  # PyInstaller extracts to this temp folder
    else:
        # Running as script
        return os.path.dirname(os.path.abspath(__file__))


class GifOptimizerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("TinyGifApp", "GifOptimizer")
        self.init_ui()
        self.gif_folder_path = ""
        self.setMouseTracking(True)
        self.oldPos = self.pos()
        self.worker_thread = None
        self.load_settings()

    def init_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setObjectName("App")

        self.setStyleSheet(
            """
            QWidget {
                font-family: 'Arial';
                background-color: transparent; 
                border: 2px solid #CDEBF0; 
                border-radius: 20px;
            }
            QPushButton {
                background-color: #CDEBF0;
                color: black;
                font-weight: bold;
                border-radius: 8px;
                padding: 10px;
                margin: 10px;
            }
            QPushButton:hover {
                background-color: #BEE0E8;
            }
            QLineEdit {
                border: 2px solid #ccc;
                border-radius: 8px;
                padding: 8px;
                margin: 10px;
            }
        """
        )

        box_style = """
        font-size: 14px; 
        color:black; 
        background-color:transparent; 
        border-radius: 20px;
        """

        label_style = """
        font-size: 14px; 
        color:black; 
        background-color: #CDEBF0;
        border-radius: 20px;
        text-decoration:underline;
        padding:20px;
        """

        cooking_style = """
        font-size: 14px; 
        color: #CDEBF0; 
        background-color:black;
        border-radius: 20px;
        text-decoration:underline;
        padding:20px;
        """

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addLayout(self.create_title_bar(box_style))
        layout.addWidget(self.create_logo_label())

        # After setting up the layout
        self.resize(540, 880)
        self.setLayout(layout)

        # Size selector (1MB to 10MB in KB)
        self.size_combo = QComboBox(self)
        self.size_combo.addItems(
            [
                "1000",
                "2000",
                "3000",
                "4000",
                "5000",
                "6000",
                "7000",
                "8000",
                "9000",
                "10000",
            ]
        )
        self.size_combo.setStyleSheet(label_style)
        self.size_combo.setCurrentIndex(4)  # Default to 5000 KB (5MB)

        # Quality selector
        self.quality_combo = QComboBox(self)
        self.quality_combo.addItems(["High", "Medium", "Low"])
        self.quality_combo.setStyleSheet(label_style)
        self.quality_combo.setCurrentIndex(1)  # Default to Medium

        # Add progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(
            """
            QProgressBar {
                border: 2px solid #CDEBF0;
                border-radius: 8px;
                background: white;
                height: 20px;
            }
            QProgressBar::chunk {
                background: black;
                border-radius: 8px;
            }
            """
        )
        self.progress_bar.hide()

        self.gif_folder_button = self.create_button(
            "Select GIF Folder", self.select_gif_folder_path
        )

        layout.addWidget(self.size_combo)
        layout.addWidget(self.quality_combo)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.gif_folder_button)

        layout.addWidget(
            self.create_button(
                "Optimize GIFs for Web", self.toggle_optimization_section, cooking_style
            )
        )

    def create_line_edit(self, placeholder, style):
        line_edit = QLineEdit(self)
        line_edit.setPlaceholderText(placeholder)
        line_edit.setStyleSheet(style)
        return line_edit

    def create_button(self, text, slot, style=None):
        button = QPushButton(text, self)
        button.clicked.connect(slot)
        button.setStyleSheet(
            style
            if style
            else """
            QPushButton {
                background-color: #CDEBF0;
                color: black;
                font-weight: bold;
                border-radius: 8px;
                padding: 10px;
                margin: 10px;
            }
            QPushButton:hover {
                background-color: #BEE0E8;
            }
        """
        )
        return button

    def show_custom_message(self):
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Information)
        msg.setText(
            "GIF optimization completed successfully! Your GIFs are now optimized for web performance."
        )
        msg.setWindowTitle("Success")
        msg.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog | Qt.CustomizeWindowHint)
        msg.setStyleSheet(
            """
        QMessageBox {
            background-color: #BEE0E8;
            color: white;
            font-size: 16px;
        }
        QPushButton {
            color: white;
            border: 2px solid white;
            border-radius: 8px;
            color: white;
            background-color: #BEE0E8;
            padding: 6px;
            font-size: 24px;
            min-width: 70px;
            min-height: 30px;
        }
        QPushButton:hover {
            background-color:  #BEE0E8;
        }
    """
        )

        msg.exec_()

    def create_title_bar(self, top_end_text_style):
        title_bar = QHBoxLayout()
        close_button = CloseButton(self)
        title_bar.addWidget(close_button, alignment=Qt.AlignRight)
        return title_bar

    def create_logo_label(self):
        logo = QLabel(self)

        # Try to find the cover image with robust path handling
        logo_path = get_resource_path("", "cover")

        if logo_path and os.path.exists(logo_path):
            pixmap = QPixmap(logo_path).scaled(
                500, 800, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            logo.setPixmap(pixmap)
        else:
            # Fallback: create a placeholder or use a default image
            logo.setText("TinyGifApp")
            logo.setStyleSheet(
                """
                QLabel {
                    background-color: #CDEBF0;
                    color: black;
                    font-size: 24px;
                    font-weight: bold;
                    border-radius: 10px;
                    padding: 20px;
                }
            """
            )

        logo.setAlignment(Qt.AlignCenter)
        return logo

    def select_gif_folder_path(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select GIF Folder")
        if folder_path:
            self.gif_folder_path = folder_path

    def get_target_size_from_combo(self):
        """Extract target size from combo box selection"""
        return int(self.size_combo.currentText())

    def get_quality_from_combo(self):
        """Get quality setting from combo box"""
        quality_text = self.quality_combo.currentText()
        if quality_text == "High":
            return 95
        elif quality_text == "Medium":
            return 85
        elif quality_text == "Low":
            return 75
        else:
            return 85

    def toggle_optimization_section(self):
        if self.gif_folder_path:
            self.gif_target_size_kb = self.get_target_size_from_combo()
            self.run_optimization()
        else:
            QMessageBox.warning(
                self,
                "Input Error",
                "Please select a GIF folder before starting the optimization process.",
            )

    def run_optimization(self):
        if not self.gif_folder_path:
            QMessageBox.warning(self, "Error", "No GIF folder selected.")
            return

        self.progress_bar.setValue(0)
        self.progress_bar.show()

        def progress_callback(percent):
            self.progress_bar.setValue(percent)
            QApplication.processEvents()  # Ensure UI updates

        # Create optimization configuration
        config = OptimizationConfig(
            target_size_kb=self.get_target_size_from_combo(),
            quality=self.get_quality_from_combo(),
            preserve_animation=True,
            backup_original=True,
        )

        # Create optimizer
        optimizer = GifOptimizer(
            input_folder=self.gif_folder_path,
            target_size_kb=config.target_size_kb,
            config=config,
        )

        # Create and start worker thread
        self.worker_thread = OptimizationWorker(optimizer)
        self.worker_thread.progress_updated.connect(self.update_progress)
        self.worker_thread.finished.connect(self.optimization_finished)
        self.worker_thread.error_occurred.connect(self.optimization_error)

        # Update UI state
        self.gif_folder_button.setEnabled(False)
        self.worker_thread.start()

    def update_progress(self, percentage):
        """Update progress bar"""
        self.progress_bar.setValue(percentage)

    def optimization_finished(self, stats):
        """Handle optimization completion"""
        self.progress_bar.hide()
        self.gif_folder_button.setEnabled(True)
        self.show_custom_message()

    def optimization_error(self, error_message):
        """Handle optimization errors"""
        self.progress_bar.hide()
        self.gif_folder_button.setEnabled(True)

        QMessageBox.critical(
            self,
            "Optimization Error",
            f"An error occurred during optimization:\n\n{error_message}",
        )

    def load_settings(self):
        """Load application settings"""
        self.gif_folder_path = self.settings.value("gif_folder_path", "")
        self.size_combo.setCurrentIndex(
            self.settings.value("size_combo_index", 4, type=int)
        )
        self.quality_combo.setCurrentIndex(
            self.settings.value("quality_combo_index", 1, type=int)
        )

    def save_settings(self):
        """Save application settings"""
        self.settings.setValue("gif_folder_path", self.gif_folder_path)
        self.settings.setValue("size_combo_index", self.size_combo.currentIndex())
        self.settings.setValue("quality_combo_index", self.quality_combo.currentIndex())

    def closeEvent(self, event):
        """Handle application close event"""
        self.save_settings()
        event.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            delta = QPoint(event.globalPos() - self.oldPos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPos = event.globalPos()


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    # Set application properties
    app.setApplicationName("TinyGifApp")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("TinyGifApp")

    # Create and show main window
    window = GifOptimizerApp()
    window.show()

    sys.exit(app.exec_())
