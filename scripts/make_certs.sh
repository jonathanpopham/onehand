#!/usr/bin/env bash
# Generate a self-signed TLS certificate for onehand.
# HTTPS is required for the browser to allow microphone access on the phone.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p certs

IP="$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo 127.0.0.1)"

openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout certs/key.pem -out certs/cert.pem \
  -days 3650 \
  -subj "/CN=onehand" \
  -addext "subjectAltName=IP:${IP},IP:127.0.0.1,DNS:localhost"

echo "wrote certs/cert.pem and certs/key.pem (SAN includes ${IP})"
echo "note: your phone will show a one-time 'connection not private' warning; tap Advanced -> Proceed."
