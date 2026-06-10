# onehand

Control your Mac from your Android phone with one hand, while the other arm
is busy holding a sleeping baby.

Your phone becomes a trackpad + dictation mic for the Mac plugged into the TV.
No app install, no account, no cloud relay. Open a web page on your phone,
and you're in.

```
phone (browser) --- Wi-Fi / WebSocket ---> Mac (Python server) ---> Quartz mouse/keyboard events
```

## Why

Feeding a baby can pin you to the couch for 2 hours at a time with exactly one
hand free. That hand has a phone in it. The Mac is across the room on the TV.
onehand bridges the gap with the two things you actually need:

1. A mouse (trackpad with tap, right-click, scroll, drag)
2. Dictation (speak into the phone, text appears on the Mac)
3. (Bonus) A keyboard, when you really need it

## Features

- Trackpad: 1-finger move, tap to click, 2-finger scroll, 2-finger tap right-click, double-tap-and-hold to drag
- Dictation: continuous speech recognition in the phone browser; final text is typed into whatever app has focus on the Mac
- Typing: a text box plus Enter / Backspace / Esc keys
- Security: LAN-only, per-session random PIN, self-signed TLS
- Zero phone install: any modern mobile browser (Chrome on Android recommended for dictation)

## Requirements

- macOS 12+ (uses Quartz CGEvents via pyobjc)
- Python 3.10+
- Phone and Mac on the same Wi-Fi network
- Android: Chrome (Web Speech API powers dictation)

## Quick start

```bash
git clone https://github.com/jonathanpopham/onehand.git
cd onehand
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# one-time: generate a self-signed cert (dictation requires HTTPS)
./scripts/make_certs.sh

python server.py
```

The server prints something like:

```
[onehand] open on your phone:  https://192.168.1.42:8741/?pin=7261
```

1. Open that URL on your phone (same Wi-Fi).
2. Accept the one-time self-signed-certificate warning (Advanced -> Proceed).
3. Grant microphone permission when you tap Dictate.

### macOS permissions (one-time)

macOS silently drops synthetic input events from untrusted processes. Grant
Accessibility access to the app you run the server from:

System Settings -> Privacy & Security -> Accessibility -> enable your
terminal app (Terminal, iTerm2, etc.), then restart the server.

The server warns at startup if it is not trusted.

## Usage

| Gesture | Action |
|---|---|
| 1-finger drag | move cursor |
| tap | left click |
| 2-finger tap | right click |
| 2-finger drag | scroll |
| double-tap, hold, drag | drag (text select, window move) |
| 🎤 Dictate | continuous dictation, tap again to stop |
| ⌨️ | show text box for typing |

Dictation flow: speech is recognized on the phone (Chrome's built-in speech
recognition) and only the final text is sent over the WebSocket, where it is
typed into the focused Mac app. Interim results are shown on the phone so you
can see it tracking.

Prefer to run recognition on the Mac instead (Whisper, macOS dictation,
anything that reads a mic)? See `docs/alternatives.md` for the
audio-streaming route and other trade-offs.

## Security model

- The server binds to your LAN. Anyone on your network with the URL still
  needs the 4-digit PIN, which rotates every time you restart the server.
- TLS is self-signed; the point is to satisfy the browser's secure-context
  requirement for mic access, not to defeat a hostile network.
- Don't run this on a network you don't trust. There is no rate limiting,
  no user accounts, and the PIN is 4 digits.
- Pass `--pin XXXX` to fix the PIN, `--http` to skip TLS (mouse-only).

## Project layout

```
server.py            aiohttp web + WebSocket server
input_mac.py         Quartz event synthesis (mouse, scroll, keys, unicode typing)
static/index.html    the entire phone UI (vanilla JS, no build step)
scripts/make_certs.sh  self-signed cert generator
```

## License

MIT. See [LICENSE](LICENSE).
