#!/usr/bin/env bash
# Build onehand.app — a double-clickable macOS menu bar app bundle.
# The bundle wraps menubar.py using the project's venv.
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT="$(pwd)"
APP="$ROOT/dist/onehand.app"

rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"

cat > "$APP/Contents/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>CFBundleName</key><string>onehand</string>
  <key>CFBundleDisplayName</key><string>onehand</string>
  <key>CFBundleIdentifier</key><string>com.onehand.menubar</string>
  <key>CFBundleVersion</key><string>0.1.0</string>
  <key>CFBundleShortVersionString</key><string>0.1.0</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleExecutable</key><string>onehand</string>
  <key>LSUIElement</key><true/>
  <key>NSHighResolutionCapable</key><true/>
</dict></plist>
EOF

cat > "$APP/Contents/MacOS/onehand" <<EOF
#!/usr/bin/env bash
cd "$ROOT"
exec "$ROOT/.venv/bin/python" "$ROOT/menubar.py"
EOF
chmod +x "$APP/Contents/MacOS/onehand"

echo "built $APP"
echo "tip: drag it into /Applications or run: open '$APP'"
echo "grant Accessibility to 'onehand' in System Settings -> Privacy & Security."
