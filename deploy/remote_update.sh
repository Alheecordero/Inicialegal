#!/usr/bin/env bash
# Actualización en el servidor tras un rsync (lo invoca deploy/deploy.sh).
set -euo pipefail
cd /var/www/inicialegal
venv/bin/pip install -q -r requirements.txt
bash deploy/backup_db.sh
venv/bin/python manage.py migrate --noinput
venv/bin/python manage.py createcachetable
venv/bin/python manage.py sync_brochures
# refresh_commercial_copy ya no corre aquí: pisaba lo editado en el panel. Ejecutarlo a mano si se quiere.
venv/bin/python manage.py collectstatic --noinput
venv/bin/python manage.py check --deploy --fail-level ERROR
# Refrescar nginx si cambió la configuración
bash deploy/install_nginx.sh
# gunicorn corre como www-data: necesita leer .env y escribir en media/.
chown root:www-data .env && chmod 640 .env
mkdir -p media && chgrp -R www-data media && chmod -R g+rwX media
install -m 644 deploy/gunicorn-inicialegal.service /etc/systemd/system/
systemctl daemon-reload
systemctl restart gunicorn-inicialegal.service
systemctl --no-pager --lines=0 status gunicorn-inicialegal.service | head -3
