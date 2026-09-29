#!/usr/bin/env bash
# Emite el certificado Let's Encrypt para inicialegal.cl y activa la configuración definitiva.
# Requisito: en Cloudflare, inicialegal.cl y www deben apuntar SOLO a 65.109.54.17 (sin registros
# A/AAAA adicionales al hosting anterior), de lo contrario la validación HTTP-01 falla.
#   ssh Hserver3 bash /var/www/inicialegal/deploy/issue_cert.sh
set -euo pipefail
APP_DIR=/var/www/inicialegal
DOMAIN=inicialegal.cl

echo "Comprobando que el desafío HTTP llega a este servidor a través de Cloudflare..."
mkdir -p "$APP_DIR/public/.well-known/acme-challenge"
echo ok > "$APP_DIR/public/.well-known/acme-challenge/precheck"
for host in "$DOMAIN" "www.$DOMAIN"; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "http://$host/.well-known/acme-challenge/precheck?n=$RANDOM")
  echo "  $host -> $code"
  if [ "$code" != "200" ]; then
    echo "ERROR: Cloudflare no está enviando el tráfico de $host a este servidor. Revisa los registros DNS." >&2
    exit 1
  fi
done
rm -f "$APP_DIR/public/.well-known/acme-challenge/precheck"

certbot certonly --webroot -w "$APP_DIR/public" -d "$DOMAIN" -d "www.$DOMAIN" \
  --non-interactive --agree-tos -m "contacto@$DOMAIN" --keep-until-expiring
bash "$APP_DIR/deploy/install_nginx.sh"
echo "Certificado instalado. https://$DOMAIN"
