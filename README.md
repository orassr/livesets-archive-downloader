Lazy Archive Downloader

A PyQt6 application to fetch and download audio files from Archive.org pages.
Supports concurrency (max downloads at once), “keep loading” (auto-re-check pages for new links), and sanitizes file names so each word is capitalized. Easily packageable as a Windows .exe using PyInstaller.

Created by orassr.
Open to all contributions—fork and improve!
Table of Contents

    Features
    Screenshots
    Requirements
    Installation
    Usage
    Building an Executable
    Contributing
    License

Features

    Audio-Only Filtering: Finds .mp3, .flac, .wav, .m4a, etc.
    Concurrent Downloads: Limit how many downloads run at once.
    Keep Loading: Re-check the same page for new uploads every X seconds.
    Dynamic UI:
        Drag columns to resize.
        Word-wrapping for long file names.
        Right-click for “Download,” “Pause,” or “Cancel” each row.
    Clean Filenames: Removes “.mp3download” suffixes, strips illegal characters, capitalizes each word.

Screenshots (Optional)

(If you have images or GIFs demonstrating the UI, add them here.)
Requirements

    Python 3.8+ (tested on 3.10 or higher)
    PyQt6
    requests
    beautifulsoup4

Installation

    Clone this repository:

git clone https://github.com/YourUsername/archive-downloader.git
cd archive-downloader

(Optional) Create a virtual environment:

python -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate

Install dependencies:

pip install -r requirements.txt

Run:

    python gui_downloader.py

You should see the GUI window appear.
Usage

    Enter an Archive.org URL (for example:
    https://archive.org/details/goa.-psy-trance.-livesets) into the text field.
    Click “Fetch Links.” The app scans for audio files, listing them in the table.
    Keep Loading (optional):
        Check “Keep Loading (re-check page)”
        Enter an Interval (e.g., 5 seconds)
        Press “Start Timed Loading.” The app re-scrapes the page every 5 s, auto-adding new files.
    Max Concurrency: Choose how many downloads can happen in parallel.
    Start Download: Begins downloading all “Pending” items from top to bottom. Right-click a single row to manage individually.

Building an Executable

For Windows users wanting a standalone .exe:

    Install PyInstaller:

pip install pyinstaller

Ensure you don’t have the obsolete pathlib backport installed. If PyInstaller complains, remove it:

pip uninstall pathlib

Build:

    pyinstaller --onefile --noconsole gui_downloader.py

        --onefile: All in one EXE.
        --noconsole: No console window (omit if you want to see debug logs).

    Look in the dist folder for gui_downloader.exe. You can copy that .exe onto another Windows machine without needing Python installed.

Contributing

Contributions are welcome!
Please fork this repo, make your changes, and open a pull request.
Feel free to report any bugs or improvement ideas by creating an issue.

    Fork the project
    Create your feature branch: git checkout -b feature/AmazingIdea
    Commit your changes: git commit -m 'Add some amazing idea'
    Push to the branch: git push origin feature/AmazingIdea
    Open a Pull Request

License

This project is licensed under the MIT License.

MIT License

Copyright (c) 2025 orassr

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software...

[The rest of the standard MIT License text here]

Happy Downloading!
