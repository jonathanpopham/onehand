#!/usr/bin/env bash
# Build the Android APK. Requires Android cmdline-tools + JDK 17-21.
set -euo pipefail
cd "$(dirname "$0")/../android"

export ANDROID_HOME="${ANDROID_HOME:-/opt/homebrew/share/android-commandlinetools}"
# Android Gradle plugin needs JDK 17-21 (jlink breaks on newer JDKs)
if /usr/libexec/java_home -v 21 &>/dev/null; then
  export JAVA_HOME="$(/usr/libexec/java_home -v 21)"
elif /usr/libexec/java_home -v 17 &>/dev/null; then
  export JAVA_HOME="$(/usr/libexec/java_home -v 17)"
fi

gradle assembleRelease --no-daemon
mkdir -p ../dist
cp app/build/outputs/apk/release/app-release.apk ../dist/onehand.apk
echo "built dist/onehand.apk"
