#!/usr/bin/env bash
# Actualización en el servidor tras un rsync (lo invoca deploy/deploy.sh).
set -euo pipefail
cd /var/www/inicialegal
venv/bin/pip install -q -r requirements.txt
bash deploy/backup_db.sh
venv/bin/python manage.py migrate --noinput
venv/bin/python manage.py collectstatic --noinput
venv/bin/python manage.py check --deploy --fail-level ERROR
# Refrescar nginx si cambió la configuración
bash deploy/install_nginx.sh
install -m 644 deploy/gunicorn-inicialegal.service /etc/systemd/system/
systemctl daemon-reload
systemctl restart gunicorn-inicialegal.service
systemctl --no-pager --lines=0 status gunicorn-inicialegal.service | head -3
