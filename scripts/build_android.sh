#!/usr/bin/env bash
# Build the Android APK (sideload) and AAB (Play Store).
# Requires Android cmdline-tools + JDK 17-21.
#
# Release signing (Play Store): expects
#   ~/.onehand/release.keystore       keystore with alias "onehand"
#   ~/.onehand/keystore_pass.txt      store/key password
# Without those, builds are debug-signed (fine for sideloading).
set -euo pipefail
cd "$(dirname "$0")/../android"

export ANDROID_HOME="${ANDROID_HOME:-/opt/homebrew/share/android-commandlinetools}"
# Android Gradle plugin needs JDK 17-21 (jlink breaks on newer JDKs)
if /usr/libexec/java_home -v 21 &>/dev/null; then
  export JAVA_HOME="$(/usr/libexec/java_home -v 21)"
elif /usr/libexec/java_home -v 17 &>/dev/null; then
  export JAVA_HOME="$(/usr/libexec/java_home -v 17)"
fi

if [ -f "$HOME/.onehand/release.keystore" ] && [ -f "$HOME/.onehand/keystore_pass.txt" ]; then
  export ONEHAND_KEYSTORE="$HOME/.onehand/release.keystore"
  export ONEHAND_KEYSTORE_PASS="$(cat "$HOME/.onehand/keystore_pass.txt")"
  echo "release signing: ON"
else
  echo "release signing: OFF (debug key)"
fi

gradle assembleRelease bundleRelease --no-daemon
mkdir -p ../dist
cp app/build/outputs/apk/release/app-release.apk ../dist/onehand.apk
cp app/build/outputs/bundle/release/app-release.aab ../dist/onehand.aab
echo "built dist/onehand.apk (sideload) and dist/onehand.aab (Play Store upload)"
