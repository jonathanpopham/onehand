"""End-to-end smoke test: drives the live server over wss and verifies
the macOS cursor actually moves and text events post without error."""

import asyncio
import json
import ssl

import aiohttp
import Quartz


def cursor():
    loc = Quartz.CGEventGetLocation(Quartz.CGEventCreate(None))
    return loc.x, loc.y


async def main():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    async with aiohttp.ClientSession() as s:
        # bad pin must be rejected
        try:
            await s.ws_connect("wss://127.0.0.1:8741/ws?pin=0000", ssl=ctx)
            print("FAIL: bad pin accepted")
            return
        except aiohttp.WSServerHandshakeError as e:
            assert e.status == 403
            print("PASS: bad pin rejected (403)")

        ws = await s.ws_connect("wss://127.0.0.1:8741/ws?pin=1234", ssl=ctx)
        print("PASS: websocket connected with good pin")

        x0, y0 = cursor()
        for _ in range(10):
            await ws.send_str(json.dumps({"t": "move", "dx": 15, "dy": 8}))
            await asyncio.sleep(0.02)
        await asyncio.sleep(0.3)
        x1, y1 = cursor()
        moved = abs(x1 - x0) + abs(y1 - y0)
        print(f"cursor moved {moved:.0f}px ({x0:.0f},{y0:.0f} -> {x1:.0f},{y1:.0f})")
        assert moved > 50, "cursor did not move"
        print("PASS: cursor moves")

        # move back
        for _ in range(10):
            await ws.send_str(json.dumps({"t": "move", "dx": -15, "dy": -8}))
            await asyncio.sleep(0.02)

        # scroll + text + key: just verify the server stays healthy
        await ws.send_str(json.dumps({"t": "scroll", "dx": 0, "dy": 30}))
        await ws.send_str(json.dumps({"t": "text", "s": ""}))
        await ws.send_str(json.dumps({"t": "key", "k": "esc"}))
        await ws.send_str("not json at all")  # must not kill the session
        await asyncio.sleep(0.3)

        async with s.get("https://127.0.0.1:8741/health", ssl=ctx) as r:
            assert (await r.json())["ok"]
        print("PASS: scroll/text/key/garbage handled, server healthy")

        await ws.close()
        print("ALL TESTS PASSED")


asyncio.run(main())
