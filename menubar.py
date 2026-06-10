#!/usr/bin/env python3
"""onehand menu bar app for macOS.

Lives in the menu bar, manages the onehand server, and shows a QR code
your phone can scan to pair.
"""

import json
import secrets
import socket
import subprocess
import sys
import tempfile
from pathlib import Path

import rumps

ROOT = Path(__file__).resolve().parent
CONFIG_DIR = Path.home() / ".onehand"
CONFIG = CONFIG_DIR / "config.json"
PLIST = Path.home() / "Library/LaunchAgents/com.onehand.menubar.plist"
PORT = 8741


def load_config() -> dict:
    if CONFIG.exists():
        return json.loads(CONFIG.read_text())
    cfg = {"pin": f"{secrets.randbelow(10000):04d}", "port": PORT}
    CONFIG_DIR.mkdir(exist_ok=True)
    CONFIG.write_text(json.dumps(cfg))
    return cfg


def lan_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


class OneHand(rumps.App):
    def __init__(self):
        super().__init__("✋", quit_button=None)
        self.cfg = load_config()
        self.proc = None
        self.url_item = rumps.MenuItem("", callback=None)
        self.toggle_item = rumps.MenuItem("Start server", callback=self.toggle)
        self.menu = [
            self.url_item,
            None,
            self.toggle_item,
            rumps.MenuItem("Copy link", callback=self.copy_link),
            rumps.MenuItem("Show QR code", callback=self.show_qr),
            None,
            rumps.MenuItem("Start at login", callback=self.toggle_login),
            None,
            rumps.MenuItem("Quit", callback=self.quit),
        ]
        if PLIST.exists():
            self.menu["Start at login"].state = 1
        self.start_server()
        rumps.Timer(self.check_server, 5).start()

    # ---------- server lifecycle ----------

    @property
    def url(self) -> str:
        return f"https://{lan_ip()}:{self.cfg['port']}/?pin={self.cfg['pin']}"

    def start_server(self):
        if self.proc and self.proc.poll() is None:
            return
        certs = ROOT / "certs" / "cert.pem"
        if not certs.exists():
            subprocess.run(["bash", str(ROOT / "scripts" / "make_certs.sh")], cwd=ROOT)
        py = ROOT / ".venv" / "bin" / "python"
        self.proc = subprocess.Popen(
            [str(py if py.exists() else sys.executable), str(ROOT / "server.py"),
             "--pin", self.cfg["pin"], "--port", str(self.cfg["port"])],
            cwd=ROOT,
        )
        self.title = "✋"
        self.toggle_item.title = "Stop server"
        self.url_item.title = self.url

    def stop_server(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        self.proc = None
        self.title = "✊"
        self.toggle_item.title = "Start server"
        self.url_item.title = "server stopped"

    def toggle(self, _):
        if self.proc and self.proc.poll() is None:
            self.stop_server()
        else:
            self.start_server()

    def check_server(self, _):
        running = self.proc is not None and self.proc.poll() is None
        self.title = "✋" if running else "✊"
        if running:
            self.url_item.title = self.url
            self.toggle_item.title = "Stop server"
        else:
            self.toggle_item.title = "Start server"

    # ---------- pairing ----------

    def copy_link(self, _):
        subprocess.run("pbcopy", text=True, input=self.url)
        rumps.notification("onehand", "", "Link copied. Open it on your phone.")

    def show_qr(self, _):
        import qrcode

        img = qrcode.make(self.url)
        path = Path(tempfile.gettempdir()) / "onehand_qr.png"
        img.save(path)
        subprocess.run(["open", str(path)])

    # ---------- login item ----------

    def toggle_login(self, sender):
        if PLIST.exists():
            subprocess.run(["launchctl", "unload", str(PLIST)], capture_output=True)
            PLIST.unlink()
            sender.state = 0
            rumps.notification("onehand", "", "Removed from login items.")
        else:
            py = ROOT / ".venv" / "bin" / "python"
            plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.onehand.menubar</string>
  <key>ProgramArguments</key><array>
    <string>{py if py.exists() else sys.executable}</string>
    <string>{ROOT / 'menubar.py'}</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>WorkingDirectory</key><string>{ROOT}</string>
</dict></plist>
"""
            PLIST.parent.mkdir(parents=True, exist_ok=True)
            PLIST.write_text(plist)
            subprocess.run(["launchctl", "load", str(PLIST)], capture_output=True)
            sender.state = 1
            rumps.notification("onehand", "", "Will start at login.")

    def quit(self, _):
        self.stop_server()
        rumps.quit_application()


if __name__ == "__main__":
    OneHand().run()
