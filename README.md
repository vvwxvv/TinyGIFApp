# TinyGifApp - Professional GIF Optimizer

A modern, stylish desktop application for batch GIF optimization and compression, built with PyQt5 and Pillow. **TinyGifApp** is designed to optimize GIF files for web use, making your animated images lighter and faster to load online while preserving animation quality.

## Features

- **Batch GIF Optimization:** Process multiple GIF files simultaneously with professional-grade compression
- **Smart Size Targeting:** Optimize GIFs to target file sizes from 1MB to 10MB with intelligent scaling
- **Animation Preservation:** Maintain GIF animations while reducing file size
- **Quality Control:** Choose between High, Medium, and Low quality settings
- **Progress Tracking:** Real-time progress bar with detailed optimization statistics
- **Production-Level Processing:** Advanced optimization algorithms with error handling and logging
- **Custom UI Elements:** Includes custom close button and frameless, translucent window
- **Modern Interface:** Clean, modern UI with transparent background and custom styling
- **Cross-Platform:** Designed for Windows, but can be adapted for other platforms
- **Settings Persistence:** Remembers your preferences between sessions

## Screenshots

> _Add screenshots of your app here (UI, before/after optimization, etc.)_

## Getting Started

### Prerequisites

- Python 3.12+
- [pip](https://pip.pypa.io/en/stable/installation/)

### Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/yourusername/TinyGifApp.git
   cd TinyGifApp
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Set up virtual environment (recommended):**

   ```bash
   python -m venv appenv
   appenv\Scripts\activate  # On Windows
   pip install -r requirements.txt
   ```

### Running the App

```bash
python main.py
```

The main window will appear, allowing you to:
- Select a GIF folder for processing
- Choose target file size (1MB to 10MB)
- Select quality level (High/Medium/Low)
- Start the optimization process

### Packaging as an EXE (Windows)

This project includes build scripts for easy packaging. To build a standalone executable:

**Using batch file:**
```bash
build.bat
```

**Using PowerShell:**
```powershell
.\build.ps1
```

**Manual build:**
```bash
pyinstaller build_exe.spec
```

The output will be in the `dist/` directory as `TinyGifApp.exe`.

## Project Structure

```
TinyGifApp/
│
├── main.py                # Main application entry point (PyQt5 GUI)
├── requirements.txt       # Python dependencies
├── build_exe.spec         # PyInstaller spec for Windows packaging
├── build.bat              # Windows batch build script
├── build.ps1              # PowerShell build script
├── main.spec              # Alternative PyInstaller spec
├── src/
│   ├── assets/            # GIF optimization and utility scripts
│   │   ├── gif_optimizer.py # Production-level GIF optimization engine
│   │   ├── reorder.py     # File reordering utilities
│   │   └── __init__.py    # Package initialization
│   ├── uiitems/           # Custom UI widgets
│   │   ├── close_button.py # Custom close button
│   │   ├── blink_button.py # Animated blinking button
│   │   ├── text_box.py    # Custom text input
│   │   ├── preview_box.py # Image preview component
│   │   ├── notification_bar.py # Notification display
│   │   ├── file_input.py  # File input component
│   │   ├── dash_line.py   # Decorative dash line
│   │   ├── custom_alert.py # Custom alert dialogs
│   │   ├── collapsible_box.py # Collapsible UI sections
│   │   └── __init__.py    # Package initialization
│   └── widgets/           # Main application widgets
│       ├── drag_drop.py   # Drag and drop functionality
│       ├── img_renamer.py # Image renaming widget
│       ├── initiation_files_input.py # File input widget
│       ├── select_initiation_csv.py # CSV selection widget
│       ├── login.py       # Login widget
│       └── __init__.py    # Package initialization
├── static/
│   ├── cover.png          # App cover image
│   ├── favicon.ico        # App icon
│   └── styles.css         # CSS styling (for documentation)
├── appenv/                # Virtual environment directory
└── README.md
```

## Dependencies

- **PyQt5** - GUI framework
- **Pillow (PIL)** - Image processing and GIF optimization
- **python-dotenv** - Environment variable management
- **pyinstaller** - For creating standalone executables

## Build Scripts

The project includes several build scripts for convenience:

- **build.bat** - Windows batch script for building executable
- **build.ps1** - PowerShell script for building executable
- **build_exe.spec** - Main PyInstaller specification file
- **main.spec** - Alternative PyInstaller specification file

## How It Works

### GIF Optimization Process

1. **File Analysis:** The app scans the selected folder for GIF files
2. **Size Calculation:** Determines optimal scaling based on target file size
3. **Frame Processing:** For animated GIFs, processes each frame individually
4. **Quality Optimization:** Applies compression while maintaining visual quality
5. **Output Generation:** Creates optimized GIFs in a new "optimized" subfolder

### Optimization Features

- **Intelligent Scaling:** Automatically calculates optimal dimensions based on target size
- **Animation Preservation:** Maintains frame timing and loop settings
- **Color Optimization:** Reduces color palette when beneficial
- **Error Handling:** Graceful handling of corrupted or unsupported files
- **Progress Tracking:** Real-time feedback with detailed statistics

## Customization

- **UI Styling:** Modify the stylesheet in `main.py` for custom colors and layout
- **Optimization Parameters:** Adjust settings in `src/assets/gif_optimizer.py`
- **UI Components:** Customize widgets in `src/uiitems/` and `src/widgets/` directories
- **Target Sizes:** Modify the size options in the combo box for different ranges

## Performance

The application uses:
- **Multi-threading** to prevent UI freezing during processing
- **Production-level algorithms** for optimal compression
- **Memory-efficient processing** for large GIF files
- **Comprehensive logging** for debugging and monitoring

## License

MIT License. See [LICENSE](LICENSE) for details.
