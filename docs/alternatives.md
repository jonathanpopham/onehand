# Alternatives and trade-offs

## Where should speech recognition run?

### A. On the phone (what onehand does)

Chrome on Android exposes the Web Speech API. Recognition happens via
Google's on-device/cloud recognizer, and onehand forwards only the final
text strings to the Mac, which types them into the focused app.

Pros:
- Zero audio plumbing; text is tiny over the WebSocket
- Excellent accuracy, free, continuous mode with interim feedback
- Works while the Mac is busy doing other things

Cons:
- Chrome may route audio through Google's recognizer (privacy trade-off)
- Requires HTTPS (hence the self-signed cert)
- iOS Safari support for continuous recognition is flaky

### B. Stream audio to the Mac, recognize there

Capture mic audio with `MediaRecorder` or `AudioWorklet` in the phone
browser, ship chunks over the WebSocket, and feed them to a recognizer on
the Mac (whisper.cpp, faster-whisper, or macOS's own dictation by playing
the audio into a virtual mic device like BlackHole).

Pros:
- Fully local if you use whisper.cpp; no third party hears anything
- Pick any model, any language, custom vocabulary

Cons:
- More moving parts: audio encoding, buffering, VAD/endpointing, model warm-up
- Latency is noticeably worse than the Web Speech API unless tuned
- whisper.cpp on an Intel Mac may struggle to keep up in real time

If you want this, the clean seam is the WebSocket protocol: add a binary
message type carrying 16 kHz PCM chunks and a server-side consumer that
runs VAD + whisper and calls `input_mac.type_text()` with the results. PRs
welcome.

### C. Android keyboard mic (zero-code fallback)

Open the ⌨️ panel in onehand and tap the mic button on Gboard. Gboard's
dictation fills the text box; Send pushes it to the Mac. Works even on
browsers without the Web Speech API.

## Why not VNC / Remote Desktop / KDE Connect?

- VNC mirrors the screen to the phone; you don't need that (the Mac is on a
  TV in front of you), and the mirroring costs latency and battery
- KDE Connect's Android app does offer remote input for desktops, but the
  macOS port's input support is immature
- Commercial apps (Remote Mouse, Unified Remote) work but are closed,
  ad-supported, and phone-app installs; this is ~600 lines you can read
