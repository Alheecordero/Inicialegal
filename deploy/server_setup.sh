#!/usr/bin/env bash
# Instalación inicial en Hserver3 (ejecutar como root, UNA vez, después del primer rsync).
#   bash /var/www/inicialegal/deploy/server_setup.sh
# Idempotente en lo razonable: no sobreescribe .env ni la clave de la BD si ya existen.
set -euo pipefail

APP_DIR=/var/www/inicialegal
DOMAIN=inicialegal.cl
DB_NAME=inicialegal
DB_USER=inicialegal
CERT_EMAIL=contacto@inicialegal.cl

cd "$APP_DIR"
mkdir -p public media staticfiles
chgrp -R www-data media && chmod -R g+rwX media

# ---------- PostgreSQL ----------
if ! sudo -u postgres psql -Atc "select 1 from pg_roles where rolname='$DB_USER'" | grep -q 1; then
  DB_PASS=$(openssl rand -hex 24)
  sudo -u postgres psql -c "CREATE ROLE $DB_USER LOGIN PASSWORD '$DB_PASS';"
  echo "DB_PASS_GENERATED=$DB_PASS" > /root/.inicialegal-db-pass
  chmod 600 /root/.inicialegal-db-pass
else
  DB_PASS=$(sed -n 's/^DB_PASS_GENERATED=//p' /root/.inicialegal-db-pass 2>/dev/null || true)
fi
if ! sudo -u postgres psql -Atc "select 1 from pg_database where datname='$DB_NAME'" | grep -q 1; then
  sudo -u postgres psql -c "CREATE DATABASE $DB_NAME OWNER $DB_USER ENCODING 'UTF8' TEMPLATE template0 LC_COLLATE 'C.UTF-8' LC_CTYPE 'C.UTF-8';"
fi

# ---------- .env ----------
if [ ! -f .env ]; then
  [ -n "${DB_PASS:-}" ] || { echo "No se conoce la clave de la BD; crea .env manualmente"; exit 1; }
  cat > .env <<EOF
DEBUG=False
SECRET_KEY=$(openssl rand -base64 60 | tr -d '\n/+=')
ALLOWED_HOSTS=$DOMAIN,www.$DOMAIN,65.109.54.17,localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=https://$DOMAIN,https://www.$DOMAIN
SITE_URL=https://$DOMAIN
SITE_INDEXING=False
DATABASE_URL=postgres://$DB_USER:$DB_PASS@127.0.0.1:5432/$DB_NAME
EMAIL_URL=consolemail://
DEFAULT_FROM_EMAIL="Inicia Legal <no-reply@$DOMAIN>"
CONTACT_NOTIFY_EMAIL=contacto@$DOMAIN
EOF
  chmod 600 .env
fi

# ---------- Python ----------
if [ ! -x venv/bin/python ]; then
  python3 -m venv venv
fi
venv/bin/pip install -q --upgrade pip
venv/bin/pip install -q -r requirements.txt
# (django-environ lee .env por sí mismo; no hace falta `source`)
venv/bin/python manage.py migrate --noinput
venv/bin/python manage.py collectstatic --noinput
venv/bin/python manage.py seed

# ---------- systemd ----------
install -m 644 deploy/gunicorn-inicialegal.socket /etc/systemd/system/
install -m 644 deploy/gunicorn-inicialegal.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now gunicorn-inicialegal.socket
systemctl restart gunicorn-inicialegal.service || true

# ---------- nginx + certificado ----------
install -m 644 deploy/nginx-inicialegal-proxy.conf /etc/nginx/snippets/inicialegal-proxy.conf
install -m 644 deploy/nginx-inicialegal-bots.conf /etc/nginx/conf.d/inicialegal-bots.conf
if [ ! -d /etc/letsencrypt/live/$DOMAIN ]; then
  install -m 644 deploy/nginx-inicialegal-bootstrap.conf /etc/nginx/sites-available/inicialegal
  ln -sf /etc/nginx/sites-available/inicialegal /etc/nginx/sites-enabled/inicialegal
  nginx -t && systemctl reload nginx
  certbot certonly --webroot -w "$APP_DIR/public" -d "$DOMAIN" -d "www.$DOMAIN" \
    --non-interactive --agree-tos -m "$CERT_EMAIL" --keep-until-expiring || true
fi
# Instala la configuración final; si aún no hay certificado Let's Encrypt usa uno autofirmado temporal
bash "$APP_DIR/deploy/install_nginx.sh"

systemctl --no-pager --lines=0 status gunicorn-inicialegal.service | head -3
echo "OK: https://$DOMAIN"
