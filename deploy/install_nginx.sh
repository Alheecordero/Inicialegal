#!/usr/bin/env bash
# Instala la configuración nginx de inicialegal.cl.
# Si existe certificado Let's Encrypt lo usa; si no, genera uno autofirmado temporal
# (Cloudflare en modo "Full" lo acepta; "Full (strict)" requiere el de Let's Encrypt).
set -euo pipefail
APP_DIR=/var/www/inicialegal
DOMAIN=inicialegal.cl
SRC="$APP_DIR/deploy/nginx-inicialegal.conf"
DST=/etc/nginx/sites-available/inicialegal

install -m 644 "$APP_DIR/deploy/nginx-inicialegal-proxy.conf" /etc/nginx/snippets/inicialegal-proxy.conf
install -m 644 "$APP_DIR/deploy/nginx-inicialegal-bots.conf" /etc/nginx/conf.d/inicialegal-bots.conf

if [ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
  install -m 644 "$SRC" "$DST"
  echo "nginx: usando certificado Let's Encrypt"
else
  TMP=/etc/ssl/inicialegal-temp
  if [ ! -f "$TMP/fullchain.pem" ]; then
    mkdir -p "$TMP"
    openssl req -x509 -nodes -newkey rsa:2048 -days 365 \
      -keyout "$TMP/privkey.pem" -out "$TMP/fullchain.pem" \
      -subj "/CN=$DOMAIN" -addext "subjectAltName=DNS:$DOMAIN,DNS:www.$DOMAIN" >/dev/null 2>&1
    chmod 600 "$TMP/privkey.pem"
  fi
  sed "s#/etc/letsencrypt/live/$DOMAIN/#$TMP/#g" "$SRC" > "$DST"
  echo "nginx: usando certificado AUTOFIRMADO temporal (ejecutar deploy/issue_cert.sh cuando el DNS esté corregido)"
fi
ln -sf "$DST" /etc/nginx/sites-enabled/inicialegal
nginx -t && systemctl reload nginx
