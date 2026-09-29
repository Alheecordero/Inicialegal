#!/usr/bin/env bash
# Despliegue desde la máquina local hacia Hserver3.
#   ./deploy/deploy.sh            # sincroniza y actualiza
#   ./deploy/deploy.sh --setup    # primera instalación (crea BD, .env, systemd, nginx, certificado)
set -euo pipefail
HOST=${HOST:-Hserver3}
DEST=/var/www/inicialegal
cd "$(dirname "$0")/.."

rsync -az --delete \
  --exclude '.venv/' --exclude 'venv/' --exclude '__pycache__/' --exclude '*.pyc' \
  --exclude '.git/' --exclude '.env' --exclude 'db.sqlite3' \
  --exclude 'media/' --exclude 'staticfiles/' --exclude 'public/' \
  ./ "$HOST:$DEST/"

if [ "${1:-}" = "--setup" ]; then
  ssh "$HOST" "bash $DEST/deploy/server_setup.sh"
else
  ssh "$HOST" "bash $DEST/deploy/remote_update.sh"
fi
