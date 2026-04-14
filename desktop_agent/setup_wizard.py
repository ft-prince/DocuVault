"""
DocuVault Desktop Agent — Compact Setup Popup
==============================================
A small floating popup (380 × auto) that walks the user through 3 steps.
No full-screen window. Feels like a system tray notification.
"""

import os
import sys
import json
import threading
import subprocess
import winreg
from pathlib import Path
from tkinter import *
from tkinter import filedialog

APPDATA_DIR  = Path(os.environ.get('APPDATA', Path.home())) / 'DocuVaultAgent'
CONFIG_PATH  = APPDATA_DIR / 'config.json'
AGENT_SCRIPT = Path(__file__).parent / 'agent.py'

# ── Palette ────────────────────────────────────────────────────
BLUE   = '#2563eb'
BLUE_H = '#1d4ed8'
BG     = '#ffffff'
PANEL  = '#f8fafc'
BORDER = '#e5e7eb'
DARK   = '#111827'
GREY   = '#6b7280'
GREEN  = '#16a34a'
RED    = '#dc2626'
AMBER  = '#d97706'
PW     = 370        # popup width (W is reserved by tkinter)


# ── Helpers ────────────────────────────────────────────────────

def _save_config(cfg):
    APPDATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, indent=2)


def _add_to_startup():
    try:
        if getattr(sys, 'frozen', False):
            # Run headless on login — no GUI popup every boot
            cmd = f'"{sys.executable}" --no-tray'
        else:
            cmd = f'"{sys.executable}" "{AGENT_SCRIPT}" --no-tray'
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r'Software\Microsoft\Windows\CurrentVersion\Run',
                             0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, 'DocuVaultAgent', 0, winreg.REG_SZ, cmd)
        winreg.CloseKey(key)
    except Exception:
        pass


def _test_connection(url, user, pwd):
    try:
        import requests as _r
        r = _r.post(url.rstrip('/') + '/agent/auth/',
                    json={'username': user, 'password': pwd}, timeout=8)
        if r.status_code == 200:
            return True, r.json().get('username', user)
        if r.status_code == 401:
            return False, 'Wrong username or password'
        return False, f'Server error {r.status_code}'
    except Exception as e:
        return False, f'Cannot reach server'


# ── Reusable widget helpers ─────────────────────────────────────

def _label(parent, text, size=9, weight='normal', color=DARK, **kw):
    return Label(parent, text=text, font=('Segoe UI', size, weight),
                 fg=color, bg=BG, **kw)


def _entry(parent, show=None, **kw):
    e = Entry(parent, show=show, font=('Segoe UI', 10),
              relief=SOLID, bd=1, highlightthickness=1,
              highlightcolor=BLUE, highlightbackground=BORDER,
              bg='#fff', fg=DARK, **kw)
    return e


def _btn(parent, text, cmd, primary=False, small=False, **kw):
    size = 9 if small else 10
    bg   = BLUE if primary else PANEL
    fg   = '#fff' if primary else DARK
    b = Button(parent, text=text, command=cmd,
               font=('Segoe UI', size, 'bold' if primary else 'normal'),
               bg=bg, fg=fg, activebackground=BLUE_H if primary else BORDER,
               activeforeground='#fff' if primary else DARK,
               relief=FLAT, cursor='hand2',
               padx=10 if small else 14, pady=4 if small else 6, **kw)
    return b


def _divider(parent):
    Frame(parent, bg=BORDER, height=1).pack(fill=X, pady=8)


# ══════════════════════════════════════════════════════════════
# Main popup window
# ══════════════════════════════════════════════════════════════

class AgentPopup(Tk):

    def __init__(self):
        super().__init__()
        self.title('DocuVault Agent')
        self.configure(bg=BG)
        self.resizable(False, False)
        self.attributes('-topmost', True)       # float above other windows
        self.protocol('WM_DELETE_WINDOW', self.destroy)

        # Remove maximize/minimize buttons — keep only close
        self.attributes('-toolwindow', True)    # slim titlebar on Windows

        self._creds   = {}
        self._folders = []
        self._startup = BooleanVar(value=True)
        self._step    = 0

        self._render()
        self._reposition()         # bottom-right corner like a notification

    # ── Position bottom-right ──────────────────────────────────

    def _reposition(self):
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        w  = self.winfo_width()
        h  = self.winfo_height()
        self.geometry(f'+{sw - w - 24}+{sh - h - 60}')

    # ── Top strip ─────────────────────────────────────────────

    def _header(self, step_n, title, subtitle):
        strip = Frame(self, bg=BLUE, width=PW)
        strip.pack(fill=X)
        inner = Frame(strip, bg=BLUE, padx=16, pady=12)
        inner.pack(fill=X)

        Label(inner, text='DocuVault Agent  ·  Setup',
              font=('Segoe UI', 8), fg='#bfdbfe', bg=BLUE).pack(anchor=W)
        Label(inner, text=title,
              font=('Segoe UI', 13, 'bold'), fg='#fff', bg=BLUE).pack(anchor=W, pady=(2, 0))
        Label(inner, text=subtitle,
              font=('Segoe UI', 8), fg='#93c5fd', bg=BLUE).pack(anchor=W)

        # Step dots
        dots = Frame(inner, bg=BLUE)
        dots.pack(anchor=E, pady=(4, 0))
        for i in range(3):
            c = '#fff' if i == step_n else '#93c5fd'
            Label(dots, text='●', font=('Segoe UI', 7), fg=c, bg=BLUE).pack(side=LEFT, padx=1)

    # ── Body frame ────────────────────────────────────────────

    def _body(self):
        f = Frame(self, bg=BG, padx=18, pady=14, width=PW)
        f.pack(fill=BOTH)
        return f

    # ── Footer with buttons ───────────────────────────────────

    def _footer(self, back_cmd=None, next_text='Next →', next_cmd=None):
        ftr = Frame(self, bg=PANEL, padx=16, pady=10)
        ftr.pack(fill=X)

        if back_cmd:
            _btn(ftr, '← Back', back_cmd, small=True).pack(side=LEFT)

        nb = _btn(ftr, next_text, next_cmd or (lambda: None), primary=True)
        nb.pack(side=RIGHT)
        return nb  # caller may keep ref to disable it

    def _clear(self):
        for w in self.winfo_children():
            w.destroy()

    # ══════════════════════════════════════════════════════════
    # Step 1 — Connect
    # ══════════════════════════════════════════════════════════

    def _render(self):
        self._show_connect()

    def _show_connect(self):
        self._clear()
        self._header(0, 'Connect', 'Enter your server and login details')

        body = self._body()

        # Server URL
        _label(body, 'Server URL', weight='bold').pack(anchor=W)
        self._e_url = _entry(body, width=36)
        self._e_url.pack(fill=X, pady=(3, 10), ipady=4)
        self._e_url.insert(0, 'http://192.168.1.10:8000')
        _label(body, 'e.g.  http://192.168.1.50:8000  (ask your admin)',
               color=GREY).pack(anchor=W, pady=(0, 8))

        # Username
        _label(body, 'Username', weight='bold').pack(anchor=W)
        self._e_user = _entry(body, width=36)
        self._e_user.pack(fill=X, pady=(3, 10), ipady=4)

        # Password
        _label(body, 'Password', weight='bold').pack(anchor=W)
        self._e_pass = _entry(body, show='•', width=36)
        self._e_pass.pack(fill=X, pady=(3, 2), ipady=4)

        # Status
        self._conn_lbl = _label(body, '', color=GREY, size=8)
        self._conn_lbl.pack(anchor=W, pady=(4, 0))

        self._e_url.focus()
        nb = self._footer(next_text='Connect →', next_cmd=self._do_connect)
        self._nb_connect = nb

        self._reposition()

    def _do_connect(self):
        url  = self._e_url.get().strip()
        user = self._e_user.get().strip()
        pwd  = self._e_pass.get()
        if not url or not user or not pwd:
            self._conn_lbl.config(text='Please fill in all fields.', fg=RED)
            return
        self._conn_lbl.config(text='Connecting…', fg=GREY)
        self._nb_connect.config(state=DISABLED)

        def _work():
            ok, msg = _test_connection(url, user, pwd)
            self.after(0, lambda: self._after_connect(ok, msg, url, user, pwd))

        threading.Thread(target=_work, daemon=True).start()

    def _after_connect(self, ok, msg, url, user, pwd):
        self._nb_connect.config(state=NORMAL)
        if ok:
            self._creds = {'server_url': url, 'username': user, 'password': pwd}
            self._conn_lbl.config(text=f'✓  Connected as {msg}', fg=GREEN)
            self.after(400, self._show_folders)
        else:
            self._conn_lbl.config(text=f'✗  {msg}', fg=RED)

    # ══════════════════════════════════════════════════════════
    # Step 2 — Watch folders
    # ══════════════════════════════════════════════════════════

    def _show_folders(self):
        self._clear()
        self._header(1, 'Watch folders', 'Files here sync to DocuVault automatically')

        body = self._body()

        # Folder list frame
        self._fl = Frame(body, bg=BG)
        self._fl.pack(fill=X)
        self._refresh_folders()

        # Add folder button
        add_row = Frame(body, bg=BG)
        add_row.pack(fill=X, pady=(6, 0))
        _btn(add_row, '＋  Add folder', self._add_folder, small=True).pack(side=LEFT)

        _divider(body)

        # Auto-start checkbox
        ck = Checkbutton(body,
            text='Start Desktop Agent Synchronizer automatically when Windows starts',
            variable=self._startup,
            font=('Segoe UI', 8), bg=BG, fg=DARK,
            activebackground=BG, cursor='hand2',
            selectcolor='#eff6ff')
        ck.pack(anchor=W)

        self._footer(back_cmd=self._show_connect,
                     next_text='Finish →', next_cmd=self._do_finish)
        self._reposition()

    def _refresh_folders(self):
        for w in self._fl.winfo_children():
            w.destroy()
        if not self._folders:
            _label(self._fl, 'No folders yet. Click + Add folder.',
                   color=GREY).pack(anchor=W, pady=6)
            return
        for i, path in enumerate(self._folders):
            row = Frame(self._fl, bg=PANEL, highlightthickness=1,
                        highlightbackground=BORDER)
            row.pack(fill=X, pady=2)
            Label(row, text='📂', font=('Segoe UI', 10), bg=PANEL).pack(side=LEFT, padx=(8, 4), pady=4)
            Label(row, text=path, font=('Segoe UI', 8), fg=DARK, bg=PANEL,
                  anchor=W, width=28, wraplength=260).pack(side=LEFT, fill=X, expand=True)
            idx = i
            Button(row, text='✕', bg=PANEL, fg=GREY, relief=FLAT,
                   font=('Segoe UI', 8), cursor='hand2',
                   command=lambda i=idx: self._remove_folder(i)).pack(side=RIGHT, padx=6)

    def _add_folder(self):
        p = filedialog.askdirectory(title='Choose folder to monitor')
        if p and p not in self._folders:
            self._folders.append(p)
            self._refresh_folders()
            self._reposition()

    def _remove_folder(self, i):
        del self._folders[i]
        self._refresh_folders()
        self._reposition()

    # ══════════════════════════════════════════════════════════
    # Step 3 — Done
    # ══════════════════════════════════════════════════════════

    def _do_finish(self):
        cfg = {
            **self._creds,
            'watch_folders': [
                {'path': p, 'recursive': True, 'category': 'General',
                 'extensions': ['.docx', '.pdf', '.xlsx', '.pptx', '.txt', '.csv']}
                for p in self._folders
            ],
            'sync':    {'debounce_seconds': 3, 'heartbeat_interval_seconds': 60,
                        'retry_on_failure': True, 'max_retries': 5},
            'startup': {'run_on_login': self._startup.get(),
                        'minimize_to_tray': True, 'show_notifications': True},
            'log':     {'level': 'INFO',
                        'file': str(APPDATA_DIR / 'desktop_agent.log'),
                        'max_size_mb': 10},
        }
        _save_config(cfg)
        if self._startup.get():
            _add_to_startup()
        self._show_done()

    def _show_done(self):
        self._clear()
        self._header(2, 'All set!', 'Desktop Agent Synchronizer is configured and ready')

        body = self._body()

        # Big tick
        Label(body, text='✓', font=('Segoe UI', 36, 'bold'),
              fg=GREEN, bg=BG).pack(pady=(8, 4))

        _label(body, 'Monitoring is active', weight='bold', size=11).pack()
        _label(body, 'Your folders will sync automatically.\nYou can close this window.',
               color=GREY, justify=CENTER).pack(pady=(4, 12))

        # Summary pill
        summary = '\n'.join([
            f'  Server  {self._creds.get("server_url","")}',
            f'  User    {self._creds.get("username","")}',
        ] + [f'  📂 {p}' for p in self._folders])
        Label(body, text=summary, font=('Courier New', 7),
              fg='#166534', bg='#f0fdf4',
              justify=LEFT, relief=FLAT, padx=10, pady=6,
              bd=0, highlightthickness=1,
              highlightbackground='#bbf7d0').pack(fill=X, pady=(0, 6))

        ftr = Frame(self, bg=PANEL, padx=16, pady=10)
        ftr.pack(fill=X)
        _btn(ftr, 'Launch Desktop Agent Synchronizer', self._launch, primary=True).pack(side=RIGHT)
        _btn(ftr, 'Close', self._close_and_launch, small=True).pack(side=RIGHT, padx=(0, 6))

        self._reposition()

    def _close_and_launch(self):
        """Close button on the Done screen — launches agent silently then closes."""
        self._launch(silent=True)

    def _launch(self, silent=False):
        try:
            if getattr(sys, 'frozen', False):
                proc = subprocess.Popen(
                    [sys.executable, '--no-tray'],
                    creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
                )
            else:
                proc = subprocess.Popen(
                    [sys.executable, str(AGENT_SCRIPT), '--no-tray'],
                    creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
                    cwd=str(AGENT_SCRIPT.parent),
                )
            # Write PID so StatusPopup can find the process next time
            APPDATA_DIR.mkdir(parents=True, exist_ok=True)
            (APPDATA_DIR / 'agent.pid').write_text(str(proc.pid))
        except Exception as e:
            if not silent:
                _label(self, f'Error: {e}', color=RED).pack()
            return
        self.destroy()


# ══════════════════════════════════════════════════════════════
# Status popup — shown every launch when config already exists
# ══════════════════════════════════════════════════════════════

PID_PATH = APPDATA_DIR / 'agent.pid'


def _read_pid():
    try:
        pid = int(PID_PATH.read_text().strip())
        os.kill(pid, 0)   # signal 0 = check existence only
        return pid
    except (Exception, SystemError):
        return None


def _write_pid(pid):
    APPDATA_DIR.mkdir(parents=True, exist_ok=True)
    PID_PATH.write_text(str(pid))


def _clear_pid():
    try:
        PID_PATH.unlink()
    except Exception:
        pass


class StatusPopup(Tk):
    """Larger, non-blocking status window shown on every launch."""

    PW = 480      # popup width

    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        self._running = False
        self._pid     = None

        self.title(' Desktop Agent Synchronizer')
        self.configure(bg=BG)
        self.resizable(False, False)
        self.attributes('-topmost', True)
        self.attributes('-toolwindow', True)
        self.protocol('WM_DELETE_WINDOW', self._close_to_bg)  # X button → keep agent running

        self._build()
        self._reposition()
        # Non-blocking first poll — after window is drawn
        self.after(200, self._poll_async)

    # ── Position ──────────────────────────────────────────────
    def _reposition(self):
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f'+{sw - self.winfo_width() - 24}+{sh - self.winfo_height() - 60}')

    # ── Build UI ──────────────────────────────────────────────
    def _build(self):
        # Header
        hdr = Frame(self, bg=BLUE)
        hdr.pack(fill=X)
        hi = Frame(hdr, bg=BLUE, padx=18, pady=14)
        hi.pack(fill=X)
        Label(hi, text='Desktop Agent Synchronizer',
              font=('Segoe UI', 14, 'bold'), fg='#fff', bg=BLUE).pack(anchor=W)
        Label(hi, text=self.cfg.get('server_url', 'Not configured'),
              font=('Segoe UI', 9), fg='#93c5fd', bg=BLUE).pack(anchor=W)

        # Status row
        body = Frame(self, bg=BG, padx=20, pady=16)
        body.pack(fill=BOTH)

        sr = Frame(body, bg=BG)
        sr.pack(fill=X, pady=(0, 12))

        self._dot = Label(sr, text='●', font=('Segoe UI', 16), fg=GREY, bg=BG)
        self._dot.pack(side=LEFT, padx=(0, 10))

        inf = Frame(sr, bg=BG)
        inf.pack(side=LEFT, fill=X, expand=True)
        self._status_lbl = Label(inf, text='Checking…',
                                 font=('Segoe UI', 11, 'bold'), fg=DARK, bg=BG, anchor=W)
        self._status_lbl.pack(anchor=W)
        self._sub_lbl = Label(inf, text='',
                              font=('Segoe UI', 9), fg=GREY, bg=BG, anchor=W)
        self._sub_lbl.pack(anchor=W)

        # Info table
        Frame(body, bg=BORDER, height=1).pack(fill=X, pady=(0, 10))

        tbl = Frame(body, bg=BG)
        tbl.pack(fill=X)
        rows = [
            ('User',   self.cfg.get('username', '—')),
            ('Server', self.cfg.get('server_url', '—')),
        ]
        for lbl, val in rows:
            r = Frame(tbl, bg=BG)
            r.pack(fill=X, pady=2)
            Label(r, text=lbl, font=('Segoe UI', 8, 'bold'), fg=GREY,
                  bg=BG, width=8, anchor=W).pack(side=LEFT)
            Label(r, text=val, font=('Segoe UI', 8), fg=DARK, bg=BG,
                  anchor=W, wraplength=360).pack(side=LEFT, fill=X, expand=True)

        # Watch folders
        folders = self.cfg.get('watch_folders', [])
        if folders:
            Frame(body, bg=BORDER, height=1).pack(fill=X, pady=(10, 8))
            Label(body, text=f'Watching {len(folders)} folder{"s" if len(folders)!=1 else ""}',
                  font=('Segoe UI', 8, 'bold'), fg=GREY, bg=BG).pack(anchor=W, pady=(0, 5))
            for wf in folders[:5]:
                p = wf.get('path', wf) if isinstance(wf, dict) else wf
                fr = Frame(body, bg=PANEL, highlightthickness=1, highlightbackground=BORDER)
                fr.pack(fill=X, pady=2)
                Label(fr, text='📂', font=('Segoe UI', 9), bg=PANEL).pack(side=LEFT, padx=(8, 4), pady=4)
                Label(fr, text=p, font=('Segoe UI', 8), fg=DARK, bg=PANEL,
                      anchor=W, wraplength=380).pack(side=LEFT, pady=4)
            if len(folders) > 5:
                Label(body, text=f'  + {len(folders)-5} more…',
                      font=('Segoe UI', 8), fg=GREY, bg=BG).pack(anchor=W)

        # Footer buttons
        ftr = Frame(self, bg=PANEL, padx=16, pady=12)
        ftr.pack(fill=X)

        self._start_btn = Button(ftr, text='▶  Start Monitoring',
            command=self._start,
            font=('Segoe UI', 9, 'bold'), bg=GREEN, fg='#fff',
            activebackground='#15803d', activeforeground='#fff',
            relief=FLAT, cursor='hand2', padx=14, pady=6)
        self._start_btn.pack(side=LEFT, padx=(0, 6))

        self._stop_btn = Button(ftr, text='■  Stop',
            command=self._stop,
            font=('Segoe UI', 9, 'bold'), bg=RED, fg='#fff',
            activebackground='#b91c1c', activeforeground='#fff',
            relief=FLAT, cursor='hand2', padx=14, pady=6)
        self._stop_btn.pack(side=LEFT, padx=(0, 6))

        Button(ftr, text='⚙  Settings', command=self._open_settings,
               font=('Segoe UI', 9), bg='#f3f4f6', fg=DARK,
               activebackground=BORDER, relief=FLAT,
               cursor='hand2', padx=12, pady=6).pack(side=LEFT)

        Button(ftr, text='✕  Close window', command=self._close_to_bg,
               font=('Segoe UI', 9), bg=PANEL, fg=GREY,
               activebackground=BORDER, relief=FLAT,
               cursor='hand2', padx=10, pady=6).pack(side=RIGHT)

    # ── Non-blocking poll ──────────────────────────────────────
    def _poll_async(self):
        """Run check in background thread, update UI on completion."""
        def _check():
            pid = _read_pid()
            running = pid is not None
            self.after(0, lambda: self._apply_status(running, pid))

        threading.Thread(target=_check, daemon=True).start()
        self.after(15000, self._poll_async)   # repeat every 15 s

    def _apply_status(self, running, pid):
        self._running = running
        self._pid     = pid
        if running:
            self._dot.config(fg=GREEN)
            self._status_lbl.config(text='● Desktop Agent Synchronizer is running', fg=GREEN)
            pid_str = f'  PID {pid}' if pid else ''
            self._sub_lbl.config(text=f'Monitoring active{pid_str} — syncing to DocuVault')
            self._start_btn.config(state=DISABLED, bg='#d1fae5', fg='#166534')
            self._stop_btn.config(state=NORMAL,   bg=RED,      fg='#fff')
        else:
            self._dot.config(fg=GREY)
            self._status_lbl.config(text='● Desktop Agent Synchronizer is stopped', fg='#6b7280')
            self._sub_lbl.config(text='Click ▶ Start Monitoring to begin  •  Closing will auto-start')
            self._start_btn.config(state=NORMAL,  bg=GREEN, fg='#fff')
            self._stop_btn.config(state=DISABLED, bg='#fca5a5', fg='#fff')

    # ── Start ──────────────────────────────────────────────────
    def _start(self):
        self._status_lbl.config(text='Starting…', fg=AMBER)
        self._start_btn.config(state=DISABLED)
        self._sub_lbl.config(text='Launching background process…')

        def _launch():
            try:
                if getattr(sys, 'frozen', False):
                    cmd = [sys.executable, '--no-tray']
                    cwd = str(Path(sys.executable).parent)
                else:
                    cmd = [sys.executable, str(AGENT_SCRIPT), '--no-tray']
                    cwd = str(AGENT_SCRIPT.parent)
                proc = subprocess.Popen(
                    cmd, cwd=cwd,
                    creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
                )
                _write_pid(proc.pid)
                self.after(2500, self._poll_async)
            except Exception as e:
                err = str(e)
                self.after(0, lambda: (
                    self._status_lbl.config(text='Failed to start', fg=RED),
                    self._sub_lbl.config(text=err),
                    self._start_btn.config(state=NORMAL),
                ))

        threading.Thread(target=_launch, daemon=True).start()

    # ── Stop ───────────────────────────────────────────────────
    def _stop(self):
        pid = _read_pid()
        if sys.platform == 'win32':
            # Kill by PID (with /T = entire process tree)
            if pid:
                subprocess.call(['taskkill', '/F', '/T', '/PID', str(pid)],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            # Fallback: kill by exe name in case process was started elsewhere
            subprocess.call(['taskkill', '/F', '/IM', 'DocuVaultAgent.exe'],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            if pid:
                try:
                    os.kill(pid, 15)   # SIGTERM
                except Exception:
                    pass
        _clear_pid()
        self.after(800, self._poll_async)

    def _close_to_bg(self):
        """Close the popup window. If agent is running it stays running.
        If agent is NOT running, auto-start it before closing so the user
        never accidentally leaves monitoring disabled."""
        if not self._running:
            # Start silently then close
            self._status_lbl.config(text='Starting in background…', fg=AMBER)
            self.update()

            def _launch_and_close():
                try:
                    if getattr(sys, 'frozen', False):
                        cmd = [sys.executable, '--no-tray']
                        cwd = str(Path(sys.executable).parent)
                    else:
                        cmd = [sys.executable, str(AGENT_SCRIPT), '--no-tray']
                        cwd = str(AGENT_SCRIPT.parent)
                    proc = subprocess.Popen(
                        cmd, cwd=cwd,
                        creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
                    )
                    _write_pid(proc.pid)
                except Exception:
                    pass
                self.after(0, self.destroy)

            threading.Thread(target=_launch_and_close, daemon=True).start()
        else:
            # Already running — just close the window, agent keeps going
            self.destroy()

    def _open_settings(self):
        self.destroy()
        AgentPopup().mainloop()


# ── Entry ───────────────────────────────────────────────────────

def run_wizard():
    app = AgentPopup()
    app.mainloop()


def run_status(cfg):
    """Show the status popup (used when config already exists)."""
    app = StatusPopup(cfg)
    app.mainloop()


if __name__ == '__main__':
    run_wizard()