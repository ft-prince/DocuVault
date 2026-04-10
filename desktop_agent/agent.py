"""
DocuVault Desktop Agent
========================
Watches local folders and automatically syncs changes to DocuVault.
Runs silently in the system tray. No user interaction required after setup.

Usage:
    python agent.py                  # Run normally (tray icon)
    python agent.py --no-tray        # Run headless (server / CI)
    python agent.py --setup          # Interactive first-time setup wizard

Requirements:
    pip install -r requirements.txt
"""

import os
import sys
import json
import time
import logging
import logging.handlers
import threading
import mimetypes
import argparse
from pathlib import Path
from datetime import datetime

import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# PyInstaller: required on Windows for frozen multiprocessing-based libraries
import multiprocessing
multiprocessing.freeze_support()

# ─── Optional tray support (skip gracefully on headless systems) ───────────────
try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False


# ──────────────────────────────────────────────────────────────
# Frozen-exe path fix: PyInstaller extracts files to _MEIPASS;
# make sure that directory is importable so setup_wizard works.
# ──────────────────────────────────────────────────────────────
if getattr(sys, 'frozen', False):
    _base = sys._MEIPASS  # type: ignore[attr-defined]
    if _base not in sys.path:
        sys.path.insert(0, _base)

# ──────────────────────────────────────────────────────────────
# Configuration  — stored in %APPDATA%\DocuVaultAgent\ so each
# Windows user has their own settings and the exe can live in
# Program Files (read-only for normal users).
# ──────────────────────────────────────────────────────────────

AGENT_DIR   = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).parent
APPDATA_DIR = Path(os.environ.get('APPDATA', Path.home())) / 'DocuVaultAgent'
CONFIG_PATH = APPDATA_DIR / 'config.json'

DEFAULT_CONFIG = {
    'server_url': 'http://localhost:8000',
    'username': '',
    'password': '',
    'watch_folders': [],
    'sync': {
        'debounce_seconds': 3,
        'heartbeat_interval_seconds': 60,
        'retry_on_failure': True,
        'max_retries': 5,
    },
    'startup': {
        'run_on_login': False,
        'minimize_to_tray': True,
        'show_notifications': True,
    },
    'log': {
        'level': 'INFO',
        'file': str(APPDATA_DIR / 'desktop_agent.log'),
        'max_size_mb': 10,
    },
}


def load_config():
    # Priority 1: user's AppData config (set via the setup wizard / client install)
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
        cfg.pop('_comment', None)
        return cfg
    # Priority 2: config.json next to agent.py (set via the Django web UI)
    script_config = AGENT_DIR / 'config.json'
    if script_config.exists():
        with open(script_config, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
        cfg.pop('_comment', None)
        return cfg
    return dict(DEFAULT_CONFIG)


def save_config(cfg):
    APPDATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, indent=2)


def _needs_setup(cfg):
    """True when the agent has never been configured."""
    return not cfg.get('username') or not cfg.get('password')


# ──────────────────────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────────────────────

def setup_logging(cfg):
    log_cfg = cfg.get('log', {})
    level = getattr(logging, log_cfg.get('level', 'INFO').upper(), logging.INFO)
    log_file = log_cfg.get('file', str(AGENT_DIR / 'desktop_agent.log'))
    # Resolve relative paths against AGENT_DIR so detached processes write to
    # the correct location regardless of the process's working directory.
    if not os.path.isabs(log_file):
        log_file = str(AGENT_DIR / log_file)
    max_bytes = int(log_cfg.get('max_size_mb', 10)) * 1024 * 1024

    logger = logging.getLogger('docuvault_agent')
    logger.setLevel(level)

    fmt = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    # Rotating file handler
    fh = logging.handlers.RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=3, encoding='utf-8')
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    return logger


# ──────────────────────────────────────────────────────────────
# DocuVault API Client
# ──────────────────────────────────────────────────────────────

class DocuVaultClient:
    def __init__(self, server_url, logger):
        self.server_url = server_url.rstrip('/')
        self.token = None
        self.logger = logger
        self.session = requests.Session()
        self.session.headers['User-Agent'] = 'DocuVault-DesktopAgent/1.0'

    def _url(self, path):
        return f"{self.server_url}/{path.lstrip('/')}"

    def authenticate(self, username, password, max_retries=5):
        """Obtain API token. Retries with backoff until server is reachable."""
        for attempt in range(1, max_retries + 1):
            try:
                resp = self.session.post(
                    self._url('/agent/auth/'),
                    json={'username': username, 'password': password},
                    timeout=10
                )
                if resp.status_code == 200:
                    data = resp.json()
                    self.token = data['token']
                    self.session.headers['Authorization'] = f'Token {self.token}'
                    self.logger.info(f"Authenticated as {data['username']}")
                    return True
                else:
                    self.logger.error(f"Auth failed ({resp.status_code}): {resp.text[:200]}")
                    return False
            except requests.exceptions.ConnectionError:
                self.logger.warning(f"Server not reachable (attempt {attempt}/{max_retries}). Retrying in 10s…")
                time.sleep(10)
        return False

    def upload(self, file_path, watch_path, category='', change_note='', folder_id=None):
        """Upload or update a file in DocuVault."""
        if not os.path.exists(file_path):
            return None

        file_name = os.path.basename(file_path)
        title = os.path.splitext(file_name)[0]
        mime_type = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'

        data = {
            'title':       title,
            'file_path':   file_path,   # full path — unique dedup key per file
            'watch_path':  watch_path,  # folder path — kept for reference
            'change_note': change_note or 'Updated via Desktop Agent',
            'category':    category,
        }
        if folder_id:
            data['folder_id'] = str(folder_id)

        try:
            with open(file_path, 'rb') as f:
                resp = self.session.post(
                    self._url('/agent/upload/'),
                    files={'file': (file_name, f, mime_type)},
                    data=data,
                    timeout=60
                )
            if resp.status_code in (200, 201):
                return resp.json()
            else:
                self.logger.error(f"Upload failed ({resp.status_code}): {resp.text[:200]}")
                return None
        except Exception as exc:
            self.logger.error(f"Upload error for {file_path}: {exc}")
            return None

    def heartbeat(self):
        """Send heartbeat to server."""
        try:
            resp = self.session.post(self._url('/agent/heartbeat/'), timeout=5)
            return resp.status_code == 200
        except Exception:
            return False

    def get_events(self, since=None):
        """Fetch recent version events."""
        try:
            params = {}
            if since:
                params['since'] = since.isoformat() if isinstance(since, datetime) else since
            resp = self.session.get(self._url('/agent/events/'), params=params, timeout=10)
            if resp.status_code == 200:
                return resp.json().get('events', [])
        except Exception:
            pass
        return []


# ──────────────────────────────────────────────────────────────
# File System Watcher
# ──────────────────────────────────────────────────────────────

class DocuVaultSyncHandler(FileSystemEventHandler):
    def __init__(self, watch_config, client, logger):
        super().__init__()
        self.watch_path = watch_config['path']
        self.recursive  = watch_config.get('recursive', True)
        self.category   = watch_config.get('category', '')
        self.folder_id  = watch_config.get('folder_id')   # workspace folder to sync into
        self.extensions = [e.lower() for e in watch_config.get('extensions', [])]
        self.client = client
        self.logger = logger

        # Debounce: avoid uploading the same file multiple times during a save
        self._pending = {}   # path → scheduled time
        self._lock = threading.Lock()
        self._debounce_secs = 3

    def _should_sync(self, path):
        if not os.path.isfile(path):
            return False
        # Skip temp/lock files (Word creates ~$file.docx)
        name = os.path.basename(path)
        if name.startswith('~$') or name.startswith('.'):
            return False
        if self.extensions:
            ext = os.path.splitext(name)[1].lower()
            return ext in self.extensions
        return True

    def _schedule(self, src_path):
        """Schedule an upload with debounce to handle rapid save events."""
        with self._lock:
            self._pending[src_path] = time.time() + self._debounce_secs

    def _flush_pending(self):
        """Called by a background thread to upload due files."""
        now = time.time()
        due = []
        with self._lock:
            for path, due_at in list(self._pending.items()):
                if now >= due_at:
                    due.append(path)
                    del self._pending[path]

        for path in due:
            if self._should_sync(path):
                self.logger.info(f"Syncing: {path}")
                result = self.client.upload(
                    file_path=path,
                    watch_path=self.watch_path,
                    category=self.category,
                    folder_id=self.folder_id,
                    change_note=f'Auto-synced: {os.path.basename(path)}',
                )
                if result:
                    action = result.get('action', 'synced')
                    version = result.get('version', '?')
                    title = result.get('title', '')
                    self.logger.info(
                        f"  ✓ {action}: '{title}' → v{version} (id={result.get('document_id')})"
                    )
                else:
                    self.logger.warning(f"  ✗ Failed to sync: {path}")

    def on_created(self, event):
        if not event.is_directory:
            self._schedule(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self._schedule(event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            self._schedule(event.dest_path)


# ──────────────────────────────────────────────────────────────
# System Tray Icon
# ──────────────────────────────────────────────────────────────

def _make_tray_icon_image():
    """Draw a simple blue circle as the tray icon (no external image needed)."""
    size = 64
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([4, 4, size - 4, size - 4], fill='#1565c0')
    draw.text((16, 18), 'DV', fill='white')
    return img


def run_tray(agent_state, stop_event):
    """Run pystray icon in a blocking call (must be on main thread on Windows)."""
    icon_image = _make_tray_icon_image()

    def on_quit(icon, _):
        icon.stop()
        stop_event.set()

    def on_open_dashboard(icon, _):
        import webbrowser
        webbrowser.open(agent_state['server_url'])

    menu = pystray.Menu(
        pystray.MenuItem('DocuVault Agent', lambda *_: None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem('Open Dashboard', on_open_dashboard),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem('Quit', on_quit),
    )

    icon = pystray.Icon('DocuVaultAgent', icon_image, 'DocuVault Agent', menu)
    icon.run()


# ──────────────────────────────────────────────────────────────
# Main Agent Loop
# ──────────────────────────────────────────────────────────────

class DocuVaultAgent:
    def __init__(self, cfg, logger):
        self.cfg = cfg
        self.logger = logger
        self.client = DocuVaultClient(cfg['server_url'], logger)
        self.observers = []
        self.handlers = []
        self.stop_event = threading.Event()

    def start(self):
        sync_cfg = self.cfg.get('sync', {})

        # Authenticate
        authenticated = self.client.authenticate(
            self.cfg['username'],
            self.cfg['password'],
            max_retries=sync_cfg.get('max_retries', 5) if sync_cfg.get('retry_on_failure', True) else 1
        )
        if not authenticated:
            self.logger.error("Authentication failed. Agent will not start.")
            return False

        # Start folder watchers
        for folder_cfg in self.cfg.get('watch_folders', []):
            folder_path = folder_cfg.get('path', '')
            if not folder_path or not os.path.isdir(folder_path):
                self.logger.warning(f"Watch folder does not exist, skipping: {folder_path}")
                continue

            handler = DocuVaultSyncHandler(folder_cfg, self.client, self.logger)
            observer = Observer()
            observer.schedule(handler, folder_path, recursive=folder_cfg.get('recursive', True))
            observer.start()
            self.observers.append(observer)
            self.handlers.append(handler)
            self.logger.info(f"Watching: {folder_path}")

        if not self.observers:
            self.logger.warning("No valid watch folders configured.")

        # Background threads
        threading.Thread(target=self._debounce_loop, daemon=True).start()
        threading.Thread(target=self._heartbeat_loop, daemon=True).start()

        self.logger.info("DocuVault Desktop Agent is running.")
        return True

    def _debounce_loop(self):
        """Flush pending uploads every second."""
        while not self.stop_event.is_set():
            for handler in self.handlers:
                handler._flush_pending()
            time.sleep(1)

    def _heartbeat_loop(self):
        """Send periodic heartbeat to keep token active."""
        interval = self.cfg.get('sync', {}).get('heartbeat_interval_seconds', 60)
        while not self.stop_event.is_set():
            ok = self.client.heartbeat()
            if not ok:
                self.logger.warning("Heartbeat failed — server may be offline.")
            time.sleep(interval)

    def stop(self):
        self.stop_event.set()
        for obs in self.observers:
            obs.stop()
            obs.join(timeout=5)
        self.logger.info("Agent stopped.")


# ──────────────────────────────────────────────────────────────
# Setup Wizard (GUI — auto-launched on first run)
# ──────────────────────────────────────────────────────────────

def run_setup():
    """Launch the tkinter setup wizard. Blocks until the wizard closes."""
    try:
        from setup_wizard import run_wizard
        run_wizard()
    except ImportError:
        # Fallback: plain terminal wizard if tkinter / wizard file unavailable
        print("\n=== DocuVault Desktop Agent Setup ===\n")
        cfg = load_config()
        cfg['server_url'] = input(f"Server URL [{cfg.get('server_url','http://localhost:8000')}]: ").strip() \
                            or cfg.get('server_url', 'http://localhost:8000')
        cfg['username'] = input("Username: ").strip()
        import getpass
        cfg['password'] = getpass.getpass("Password: ")
        folder = input("Folder to watch: ").strip()
        if folder:
            cfg['watch_folders'] = [{'path': folder, 'recursive': True,
                'category': 'General',
                'extensions': ['.docx','.pdf','.xlsx','.pptx','.txt','.csv']}]
        save_config(cfg)
        print(f"Config saved to {CONFIG_PATH}")


# ──────────────────────────────────────────────────────────────
# Entry Point
# ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='DocuVault Desktop Agent')
    parser.add_argument('--setup',    action='store_true', help='Force the setup wizard')
    parser.add_argument('--no-tray',  action='store_true', help='Run headless (no tray icon)')
    args = parser.parse_args()

    cfg = load_config()

    # ── Headless mode: skip all GUI ────────────────────────────
    if args.no_tray:
        if _needs_setup(cfg):
            print("No config found. Run agent.py without --no-tray to set up.")
            sys.exit(1)
        logger = setup_logging(cfg)
        logger.info("Starting DocuVault Desktop Agent (headless)…")
        agent = DocuVaultAgent(cfg, logger)
        if not agent.start():
            sys.exit(1)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            agent.stop()
        return

    # ── GUI mode (double-click / normal launch) ────────────────
    if args.setup or _needs_setup(cfg):
        # First run: show setup wizard
        run_setup()
        cfg = load_config()
        if _needs_setup(cfg):
            sys.exit(0)   # user closed wizard without finishing

    # ── GUI mode: show status popup; user clicks Start to begin ──
    # The popup itself launches the agent via --no-tray when Start is clicked.
    # This way the exe acts as a control panel, not an auto-starter.
    try:
        from setup_wizard import run_status
        run_status(cfg)
    except Exception as _e:
        import traceback
        _crash_log = APPDATA_DIR / 'popup_error.log'
        try:
            APPDATA_DIR.mkdir(parents=True, exist_ok=True)
            _crash_log.write_text(traceback.format_exc(), encoding='utf-8')
        except Exception:
            pass
        try:
            import tkinter as _tk, tkinter.messagebox as _mb
            _r = _tk.Tk(); _r.withdraw()
            _mb.showerror('DocuVault Agent',
                          f'Could not open the status window.\n\n{str(_e)[:400]}\n\nSee: {_crash_log}')
            _r.destroy()
        except Exception:
            pass
    return

if __name__ == '__main__':
    main()
