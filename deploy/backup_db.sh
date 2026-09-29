#!/usr/bin/env bash
# Copia de seguridad PostgreSQL antes de migrar (servidor).
set -euo pipefail
cd /var/www/inicialegal
BACKUP_DIR=/var/backups/inicialegal
mkdir -p "$BACKUP_DIR"
STAMP=$(date +%Y%m%d-%H%M%S)
FILE="$BACKUP_DIR/db-$STAMP.sql.gz"
set -a
# shellcheck disable=SC1091
source .env
set +a
pg_dump "$DATABASE_URL" | gzip -9 > "$FILE"
ls -t "$BACKUP_DIR"/db-*.sql.gz 2>/dev/null | tail -n +8 | xargs -r rm --
echo "Backup: $FILE"
