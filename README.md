# Lazy Archive Downloader

A **PyQt6** application to fetch and download audio files from [Archive.org](https://archive.org/) pages.  
Supports concurrency (max downloads at once), “keep loading” (auto-re-check pages for new links), and sanitizes file names so each word is capitalized. Easily packageable as a Windows `.exe` using PyInstaller.

**Created by [orassr](https://github.com/orassr).**  
Open to all contributions—fork and improve!

---

## Table of Contents

1. [Features](#features)  
2. [Screenshots (Optional)](#screenshots-optional)  
3. [Requirements](#requirements)  
4. [Installation](#installation)  
5. [Usage](#usage)  
6. [Building an Executable](#building-an-executable)  
7. [Contributing](#contributing)  
8. [License](#license)

---

## Features

- **Audio-Only Filtering**  
  Finds `.mp3`, `.flac`, `.wav`, `.m4a`, and similar extensions.  
- **Concurrent Downloads**  
  Limit how many downloads run at once.  
- **Keep Loading**  
  Re-check the same page for new uploads every X seconds.  
- **Dynamic UI**  
  - Drag columns to resize  
  - Word-wrapping for long file names  
  - Right-click for “Download,” “Pause,” or “Cancel” each row  
- **Clean Filenames**  
  Automatically removes “`.mp3download`” suffixes, strips illegal characters, capitalizes each word.

---

## Screenshots
![screem](https://github.com/user-attachments/assets/1e5598d2-6a21-4f67-b359-bbd27370fa7f)

## Requirements

 **Python 3.8+ (tested on 3.10 or higher)**
- **PyQt6**
- **requests**
- **beautifulsoup4**

---

## Installation

1. **Clone this repository**:
   ```bash

    git clone https://github.com/orassr/archive-downloader.git
    cd archive-downloader

(Optional) Create a virtual environment:
   
    python -m venv venv

# On Windows:
    venv\Scripts\activate
# On Mac/Linux:
    source venv/bin/activate

Install dependencies:
    
    pip install -r requirements.txt

Run:

    python gui_downloader.py

You should see the GUI window appear.

## Usage

    Enter an Archive.org URL (for example:
    https://archive.org/details/goa.-psy-trance.-livesets) in the top text box.
    Click Fetch Links. The app scans for audio files and lists them in the table.
    (Optional) Keep Loading:
        Check “Keep Loading (re-check page)”
        Enter an Interval (s) (e.g. 5)
        Click Start Timed Loading. The app re-scrapes the page every 5 seconds, automatically adding new files.
    Set the Max Concurrency spinbox (e.g. 2 means 2 downloads at once).
    Click Start Download to begin downloading all “Pending” items (from top to bottom).
        Right-click a single row to Download, Pause, or Cancel individually.

## Building an Executable

If you want a single .exe you can run on Windows without installing Python:
    Install PyInstaller:
    
    pip install pyinstaller

Ensure you don’t have obsolete backports like pathlib installed. If PyInstaller complains, do:
    
    pip uninstall pathlib

Build:

    pyinstaller --onefile --noconsole gui_downloader.py

        --onefile: Bundles everything into one EXE.
        --noconsole: Hides the console window (omit if you want to see console output).

    Look inside dist/ for gui_downloader.exe. Copy that file to another Windows machine and run it directly—no Python required.

## Contributing

Contributions are welcome! Please fork this repository, make your changes, and create a pull request.

Steps:

Fork the project
Create your feature branch:
    
    git checkout -b feature/MyAwesomeFeature

Commit your changes:

    git commit -m "Add my awesome feature"

Push to GitHub:

    git push origin feature/MyAwesomeFeature

Open a Pull Request describing your changes.

## License

This project is licensed under the MIT License:

MIT License

2025 orassr

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction...

(Include the full MIT license text if you prefer, or store it in a LICENSE file.)

Happy downloading!



If you have screenshots or GIFs demonstrating the UI, place them in a `docs/` folder or similar, and show them here:

```md
