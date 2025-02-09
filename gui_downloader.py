import sys
import os
import re
import requests
import urllib.parse
from urllib.parse import urljoin, unquote, urlparse
from bs4 import BeautifulSoup
from collections import deque

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QProgressBar,
    QLabel, QFileDialog, QCheckBox, QHeaderView, QMenu, QSpinBox
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal

# We only want audio links with these extensions
AUDIO_EXTENSIONS = [".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac"]

# If we see a link that ends in ".mp3download", etc., we rename to ".mp3", etc.
DOWNLOAD_SUFFIX_MAP = {
    ".mp3download":  ".mp3",
    ".flacdownload": ".flac",
    ".wavdownload":  ".wav",
    ".oggdownload":  ".ogg",
    ".m4adownload":  ".m4a",
    ".aacdownload":  ".aac",
}

def sanitize_title(title: str) -> str:
    """
    1) Remove forbidden file-name characters ( \ / * ? : " < > | ).
    2) Trim whitespace.
    3) Convert to Title Case (so each word starts with a capital letter).
    """
    # Remove forbidden characters
    title = re.sub(r'[\\/*?:"<>|]+', '', title)
    # Trim whitespace
    title = title.strip()
    # Title-case: "absolum - live @ fest" -> "Absolum - Live @ Fest"
    title = title.title()

    return title

class DownloadThread(QThread):
    progress_update = pyqtSignal(int, int)   # (row, progress%)
    status_update = pyqtSignal(int, str)     # (row, status)

    def __init__(self, row, url, save_path):
        super().__init__()
        self.row = row
        self.url = url
        self.save_path = save_path
        self.running = True

    def run(self):
        try:
            self.status_update.emit(self.row, "Downloading")
            resp = requests.get(self.url, stream=True)
            resp.raise_for_status()

            total_size = int(resp.headers.get("content-length", 0))
            downloaded_size = 0

            with open(self.save_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if not self.running:
                        self.status_update.emit(self.row, "Paused")
                        return
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        if total_size:
                            progress = int(downloaded_size / total_size * 100)
                        else:
                            progress = 0
                        self.progress_update.emit(self.row, progress)

            self.status_update.emit(self.row, "Completed")
        except Exception:
            self.status_update.emit(self.row, "Error")

    def stop(self):
        self.running = False

class DownloaderApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Archive Downloader - Title Case Filenames")
        self.setGeometry(100, 100, 950, 600)

        # Data
        self.save_directory = os.getcwd()
        self.known_links = set()

        # Concurrency
        self.download_threads = {}
        self.download_queue = deque()
        self.active_downloads = 0
        self.max_concurrent_downloads = 2

        # Keep Loading / Timed Refresh
        self.keep_loading = False
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.check_new_links)

        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()

        # -- Row 1: URL input & Fetch
        url_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter Archive.org URL...")
        url_layout.addWidget(self.url_input)

        fetch_button = QPushButton("Fetch Links")
        fetch_button.clicked.connect(self.fetch_links_once)
        url_layout.addWidget(fetch_button)
        main_layout.addLayout(url_layout)

        # -- Row 2: Folder label & folder selection
        self.folder_label = QLabel(f"Download Folder: {self.save_directory}")
        self.folder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.folder_label)

        folder_button = QPushButton("Select Download Folder")
        folder_button.clicked.connect(self.select_download_folder)
        main_layout.addWidget(folder_button)

        # -- Row 3: Keep Loading, interval, Start Timed
        keep_layout = QHBoxLayout()
        self.keep_loading_checkbox = QCheckBox("Keep Loading (re-check page)")
        self.keep_loading_checkbox.stateChanged.connect(self.on_keep_loading_changed)
        keep_layout.addWidget(self.keep_loading_checkbox)

        keep_layout.addWidget(QLabel("Interval (s):"))
        self.interval_input = QLineEdit("5")
        self.interval_input.setFixedWidth(50)
        keep_layout.addWidget(self.interval_input)

        self.start_timed_loading_button = QPushButton("Start Timed Loading")
        self.start_timed_loading_button.setEnabled(False)
        self.start_timed_loading_button.clicked.connect(self.start_timed_loading)
        keep_layout.addWidget(self.start_timed_loading_button)
        main_layout.addLayout(keep_layout)

        # -- Row 4: Max Concurrency & Start Download
        concurrency_layout = QHBoxLayout()
        concurrency_layout.addWidget(QLabel("Max Concurrency:"))

        self.concurrency_spin = QSpinBox()
        self.concurrency_spin.setRange(1, 50)
        self.concurrency_spin.setValue(self.max_concurrent_downloads)
        self.concurrency_spin.valueChanged.connect(self.on_concurrency_changed)
        concurrency_layout.addWidget(self.concurrency_spin)

        self.start_download_button = QPushButton("Start Download")
        self.start_download_button.setEnabled(False)
        self.start_download_button.clicked.connect(self.queue_downloads_from_top)
        concurrency_layout.addWidget(self.start_download_button)

        main_layout.addLayout(concurrency_layout)

        # -- Row 5: Table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["File Name", "Status", "Progress"])
        # Let user drag columns left/right
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        # Enable word wrap in table cells
        self.table.setWordWrap(True)

        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        main_layout.addWidget(self.table)

        self.setLayout(main_layout)

    # ------------------------------------------------
    # 1) Fetch links once, store them in the table
    # ------------------------------------------------
    def fetch_links_once(self):
        url = self.url_input.text().strip()
        if not url:
            self.folder_label.setText("⚠️ Please enter a valid URL.")
            return

        self.folder_label.setText("Fetching links...")
        QApplication.processEvents()

        new_links = self.scrape_audio_links(url)
        if not new_links:
            self.folder_label.setText("No audio links found.")
            return

        added_count = 0
        for (link, track_title) in new_links:
            if link not in self.known_links:
                self.known_links.add(link)
                self.add_link_to_table(link, track_title)
                added_count += 1

        self.folder_label.setText(
            f"Found: {len(new_links)} audio links. {added_count} new."
        )
        self.start_download_button.setEnabled(True)
        self.start_timed_loading_button.setEnabled(True)

    def scrape_audio_links(self, url):
        """
        Return a list of (absolute_url, final_title).
        final_title is the anchor text if available, else fallback to basename.
        Then we strip the trailing 'download' from .mp3download, .flacdownload, etc.
        And we pass the result through 'sanitize_title()' (which does Title Case).
        """
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
        except requests.exceptions.RequestException as e:
            self.folder_label.setText(f"Error fetching URL: {e}")
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        base_url = url.rsplit("/", 1)[0]

        found = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            absolute_url = urljoin(base_url, href)
            lower = absolute_url.lower()

            # Filter out only known audio
            # We'll consider either the normal .mp3 or the .mp3download etc.
            if any(
                lower.endswith(ext)
                or any(lower.endswith(dl) for dl in DOWNLOAD_SUFFIX_MAP.keys())
                for ext in AUDIO_EXTENSIONS
            ):
                anchor_text = a.get_text(strip=True)
                anchor_text = unquote(anchor_text)
                if anchor_text:
                    raw_title = anchor_text
                else:
                    raw_title = os.path.basename(urllib.parse.urlparse(absolute_url).path)
                    raw_title = unquote(raw_title)

                if not raw_title:
                    raw_title = "unnamed_file"

                # If the extension ends with .mp3download or .flacdownload, fix it:
                for dl_suffix, real_ext in DOWNLOAD_SUFFIX_MAP.items():
                    if raw_title.lower().endswith(dl_suffix):
                        raw_title = raw_title[: -len(dl_suffix)] + real_ext
                        break

                final_title = sanitize_title(raw_title)
                found.append((absolute_url, final_title))

        return found

    def add_link_to_table(self, link, track_title):
        row = self.table.rowCount()
        self.table.insertRow(row)

        name_item = QTableWidgetItem(track_title)
        self.table.setItem(row, 0, name_item)

        status_item = QTableWidgetItem("Pending")
        # store the link in user data
        status_item.setData(Qt.ItemDataRole.UserRole, link)
        self.table.setItem(row, 1, status_item)

        progress_bar = QProgressBar()
        progress_bar.setValue(0)
        self.table.setCellWidget(row, 2, progress_bar)

    # ------------------------------------------------
    # 2) Keep Loading / Timed Refresh
    # ------------------------------------------------
    def on_keep_loading_changed(self, state):
        self.keep_loading = (state == Qt.CheckState.Checked)
        if not self.keep_loading:
            self.refresh_timer.stop()

    def start_timed_loading(self):
        if not self.keep_loading:
            return

        try:
            seconds = float(self.interval_input.text())
            if seconds < 1:
                seconds = 1
        except ValueError:
            seconds = 5

        self.refresh_timer.stop()
        self.refresh_timer.setInterval(int(seconds * 1000))
        self.refresh_timer.start()
        self.folder_label.setText(f"Auto-refresh every {seconds} seconds...")

    def check_new_links(self):
        if not self.keep_loading:
            self.refresh_timer.stop()
            return

        url = self.url_input.text().strip()
        if not url:
            return

        new_pairs = self.scrape_audio_links(url)
        added_count = 0
        for (link, track_title) in new_pairs:
            if link not in self.known_links:
                self.known_links.add(link)
                self.add_link_to_table(link, track_title)
                added_count += 1

        if added_count > 0:
            self.folder_label.setText(f"Added {added_count} new links.")
        else:
            self.folder_label.setText("No new audio links found.")

    # ------------------------------------------------
    # 3) Concurrency & Download Queue
    # ------------------------------------------------
    def on_concurrency_changed(self, value):
        self.max_concurrent_downloads = value

    def queue_downloads_from_top(self):
        self.download_queue.clear()
        for row in range(self.table.rowCount()):
            status_item = self.table.item(row, 1)
            if status_item and status_item.text() == "Pending":
                status_item.setText("Queued")
                self.download_queue.append(row)
        self.check_download_queue()

    def check_download_queue(self):
        while self.active_downloads < self.max_concurrent_downloads and self.download_queue:
            row = self.download_queue.popleft()
            self.start_download(row)

    def start_download(self, row):
        if row in self.download_threads:
            return

        status_item = self.table.item(row, 1)
        if not status_item:
            return

        link = status_item.data(Qt.ItemDataRole.UserRole)
        if not link:
            return

        filename = self.table.item(row, 0).text()
        save_path = os.path.join(self.save_directory, filename)

        thread = DownloadThread(row, link, save_path)
        thread.progress_update.connect(self.update_progress)
        thread.status_update.connect(self.handle_status_update)
        self.download_threads[row] = thread

        self.active_downloads += 1
        thread.start()

    def update_progress(self, row, progress):
        progress_bar = self.table.cellWidget(row, 2)
        if progress_bar:
            progress_bar.setValue(progress)

    def handle_status_update(self, row, status):
        self.table.setItem(row, 1, QTableWidgetItem(status))
        if status in ("Completed", "Error", "Cancelled"):
            self.active_downloads -= 1
            if row in self.download_threads:
                del self.download_threads[row]
            self.check_download_queue()

    # ------------------------------------------------
    # 4) Folder selection
    # ------------------------------------------------
    def select_download_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Download Folder")
        if folder:
            self.save_directory = folder
            self.folder_label.setText(f"Download Folder: {self.save_directory}")

    # ------------------------------------------------
    # 5) Right-click menu (Download, Pause, Cancel)
    # ------------------------------------------------
    def show_context_menu(self, position):
        row = self.table.indexAt(position).row()
        if row < 0:
            return

        menu = QMenu(self)
        download_action = menu.addAction("Download")
        pause_action = menu.addAction("Pause")
        cancel_action = menu.addAction("Cancel")

        action = menu.exec(self.table.viewport().mapToGlobal(position))
        if action == download_action:
            status_item = self.table.item(row, 1)
            if status_item and status_item.text() in ("Pending", "Queued", "Error"):
                status_item.setText("Queued")
                if row not in self.download_queue:
                    self.download_queue.appendleft(row)
                self.check_download_queue()
            else:
                self.start_download(row)
        elif action == pause_action:
            self.pause_download(row)
        elif action == cancel_action:
            self.cancel_download(row)

    # ------------------------------------------------
    # 6) Pause / Cancel
    # ------------------------------------------------
    def pause_download(self, row):
        thread = self.download_threads.get(row)
        if thread:
            thread.stop()
            self.table.setItem(row, 1, QTableWidgetItem("Paused"))
            self.active_downloads -= 1
            del self.download_threads[row]
            self.check_download_queue()

    def cancel_download(self, row):
        thread = self.download_threads.get(row)
        if thread:
            thread.stop()
            file_name = self.table.item(row, 0).text()
            save_path = os.path.join(self.save_directory, file_name)
            if os.path.exists(save_path):
                try:
                    os.remove(save_path)
                except Exception as e:
                    print("Error removing file:", e)
            self.table.setItem(row, 1, QTableWidgetItem("Cancelled"))
            self.active_downloads -= 1
            del self.download_threads[row]
            self.check_download_queue()
        else:
            if row in self.download_queue:
                self.download_queue.remove(row)
            self.table.setItem(row, 1, QTableWidgetItem("Cancelled"))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DownloaderApp()
    window.show()
    sys.exit(app.exec())
