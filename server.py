#!/usr/bin/env python3
"""onehand server.

Serves the phone-facing trackpad/dictation page over HTTPS and translates
WebSocket messages into macOS mouse/keyboard events via Quartz.

Usage:
    python server.py [--port 8741] [--pin 1234] [--http]

A random 4-digit PIN is generated each run unless --pin is given.
"""

import argparse
import json
import secrets
import socket
import ssl
import sys
from pathlib import Path

from aiohttp import web, WSMsgType

import input_mac as inp

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
CERT = ROOT / "certs" / "cert.pem"
KEY = ROOT / "certs" / "key.pem"


def lan_ip() -> str:
    """Best-effort LAN IP discovery (no traffic is actually sent)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


async def index(request: web.Request) -> web.FileResponse:
    return web.FileResponse(STATIC / "index.html")


async def health(request: web.Request) -> web.Response:
    return web.json_response({"ok": True})


async def ws_handler(request: web.Request) -> web.WebSocketResponse:
    pin = request.app["pin"]
    if request.query.get("pin") != pin:
        raise web.HTTPForbidden(text="bad pin")

    ws = web.WebSocketResponse(heartbeat=20)
    await ws.prepare(request)
    print(f"[onehand] client connected: {request.remote}")

    async for msg in ws:
        if msg.type != WSMsgType.TEXT:
            continue
        try:
            m = json.loads(msg.data)
            t = m.get("t")
            if t == "move":
                inp.move_relative(float(m["dx"]), float(m["dy"]))
            elif t == "scroll":
                inp.scroll(float(m.get("dx", 0)), float(m.get("dy", 0)))
            elif t == "click":
                inp.click(m.get("b", "left"))
            elif t == "down":
                inp.mouse_down()
            elif t == "up":
                inp.mouse_up()
            elif t == "text":
                inp.type_text(str(m.get("s", "")))
            elif t == "key":
                inp.press_key(str(m.get("k", "")))
        except Exception as e:  # keep the session alive on bad input
            print(f"[onehand] error handling {msg.data[:80]!r}: {e}")

    print("[onehand] client disconnected")
    return ws


def main() -> None:
    ap = argparse.ArgumentParser(description="Control this Mac from your phone.")
    ap.add_argument("--port", type=int, default=8741)
    ap.add_argument("--pin", default=None, help="session PIN (default: random)")
    ap.add_argument(
        "--http",
        action="store_true",
        help="serve plain HTTP (dictation needs HTTPS; mouse still works)",
    )
    args = ap.parse_args()

    if not inp.trusted():
        print(
            "\n[onehand] WARNING: this process is not trusted for Accessibility.\n"
            "  Events will be silently ignored by macOS.\n"
            "  Fix: System Settings -> Privacy & Security -> Accessibility ->\n"
            "  enable your terminal app (or the python binary), then rerun.\n"
        )

    pin = args.pin or f"{secrets.randbelow(10000):04d}"

    app = web.Application()
    app["pin"] = pin
    app.router.add_get("/", index)
    app.router.add_get("/health", health)
    app.router.add_get("/ws", ws_handler)
    app.router.add_static("/static", STATIC)

    ssl_ctx = None
    scheme = "http"
    if not args.http:
        if not (CERT.exists() and KEY.exists()):
            print(
                "[onehand] no TLS cert found. Run: ./scripts/make_certs.sh\n"
                "  (or use --http, but dictation requires HTTPS)"
            )
            sys.exit(1)
        ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_ctx.load_cert_chain(CERT, KEY)
        scheme = "https"

    ip = lan_ip()
    print(f"\n[onehand] open on your phone:  {scheme}://{ip}:{args.port}/?pin={pin}")
    print(f"[onehand] session PIN: {pin}\n")

    web.run_app(app, host="0.0.0.0", port=args.port, ssl_context=ssl_ctx, print=None)


if __name__ == "__main__":
    main()
