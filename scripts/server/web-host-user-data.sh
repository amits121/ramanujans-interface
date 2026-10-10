#!/bin/bash
# Ramanujan's Interface - web host bootstrap (EC2 user data, Amazon Linux 2023, arm64 or x86_64).
#
# Fill the three values below, then paste the whole file into "User data" when launching the instance.
# What it does: installs nginx to serve the engine's pre-rendered static output from /var/www/<site>,
# installs site-sync (pull the latest build of a site from the sites bucket, atomic swap) and
# site-cert (Let's Encrypt certificate + HTTPS redirect, renewal timer). Session Manager only: no SSH
# server is opened and no key pair is used. No secrets: the host reads the bucket through its role.
#
# Copyright (c) 2026 Intelligent Cloud Lab Inc.
set -euxo pipefail

HOST="__HOST__"          # the site's host name, e.g. the label chosen in F-7 plus .techinnovations.io
SITE="__SITE__"          # the site folder name used by scripts/deploy_site.py, e.g. sample-landing
BUCKET="__BUCKET__"      # the sites bucket, e.g. icl-sites-<account id>

dnf -y update
dnf -y install nginx python3 python3-pip augeas-libs

# certbot through pip (Amazon Linux 2023 ships no certbot package)
python3 -m venv /opt/certbot
/opt/certbot/bin/pip install --quiet --upgrade pip
/opt/certbot/bin/pip install --quiet certbot certbot-nginx
ln -sf /opt/certbot/bin/certbot /usr/local/bin/certbot

mkdir -p /etc/icl-web-host "/var/www/$SITE"
echo "$BUCKET" > /etc/icl-web-host/bucket
echo "$HOST" > /etc/icl-web-host/host
printf '<!doctype html><html lang="en"><head><meta charset="utf-8"><title>%s</title></head><body><p>%s: first deploy pending.</p></body></html>\n' "$HOST" "$HOST" > "/var/www/$SITE/index.html"
chown -R nginx:nginx /var/www

cat > /etc/nginx/nginx.conf <<'NGINX'
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log notice;
pid /run/nginx.pid;
include /usr/share/nginx/modules/*.conf;
events { worker_connections 1024; }
http {
    log_format main '$remote_addr - $remote_user [$time_local] "$request" $status $body_bytes_sent "$http_referer" "$http_user_agent"';
    access_log /var/log/nginx/access.log main;
    sendfile on;
    tcp_nopush on;
    keepalive_timeout 65;
    types_hash_max_size 4096;
    server_tokens off;
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    gzip on;
    gzip_types text/css application/javascript image/svg+xml application/json text/plain;
    include /etc/nginx/conf.d/*.conf;
    # anything that is not one of our host names (including the bare address) gets no answer
    server { listen 80 default_server; listen [::]:80 default_server; server_name _; return 444; }
}
NGINX

cat > "/etc/nginx/conf.d/$SITE.conf" <<SITECONF
server {
    listen 80;
    listen [::]:80;
    server_name $HOST;
    root /var/www/$SITE;
    index index.html;
    add_header X-Content-Type-Options nosniff always;
    add_header X-Frame-Options DENY always;
    add_header Referrer-Policy strict-origin-when-cross-origin always;
    location /assets/ { expires 1h; try_files \$uri =404; }
    location / { expires 5m; try_files \$uri \$uri/ =404; }
}
SITECONF

cat > /usr/local/bin/site-sync <<'SYNC'
#!/bin/bash
# site-sync <site>: pull the latest build of <site> from the sites bucket into the web root, atomically.
set -euo pipefail
SITE="${1:?usage: site-sync <site>}"
BUCKET="$(cat /etc/icl-web-host/bucket)"
LIVE="/var/www/$SITE"; NEW="/var/www/.$SITE.new"; OLD="/var/www/.$SITE.old"
rm -rf "$NEW" "$OLD"
aws s3 sync "s3://$BUCKET/$SITE/" "$NEW/" --only-show-errors
test -f "$NEW/index.html"
chown -R nginx:nginx "$NEW"
if [ -d "$LIVE" ]; then mv "$LIVE" "$OLD"; fi
mv "$NEW" "$LIVE"
rm -rf "$OLD"
echo "synced $SITE  index.html sha256 $(sha256sum "$LIVE/index.html" | cut -c1-64)"
SYNC
chmod 755 /usr/local/bin/site-sync

cat > /usr/local/bin/site-cert <<'CERT'
#!/bin/bash
# site-cert <host> <email>: issue the Let's Encrypt certificate for <host> and turn on the HTTPS redirect.
# Run once the host name resolves to this instance (port 80 must be reachable from the internet).
set -euo pipefail
HOST="${1:?usage: site-cert <host> <email>}"; EMAIL="${2:?usage: site-cert <host> <email>}"
/usr/local/bin/certbot --nginx -d "$HOST" -m "$EMAIL" --agree-tos --no-eff-email --redirect --non-interactive
nginx -t && systemctl reload nginx
echo "certificate issued for $HOST"
CERT
chmod 755 /usr/local/bin/site-cert

cat > /etc/systemd/system/certbot-renew.service <<'UNIT'
[Unit]
Description=Renew Let's Encrypt certificates
[Service]
Type=oneshot
ExecStart=/usr/local/bin/certbot renew --quiet --deploy-hook "systemctl reload nginx"
UNIT
cat > /etc/systemd/system/certbot-renew.timer <<'UNIT'
[Unit]
Description=Twice-daily certificate renewal check
[Timer]
OnCalendar=*-*-* 03,15:17:00
RandomizedDelaySec=1h
Persistent=true
[Install]
WantedBy=timers.target
UNIT

systemctl daemon-reload
systemctl enable --now certbot-renew.timer
systemctl enable --now amazon-ssm-agent || true
nginx -t
systemctl enable --now nginx

# first pull, if a build is already in the bucket; otherwise the placeholder page stays up
/usr/local/bin/site-sync "$SITE" || echo "no build in the bucket yet for $SITE"
echo "web host ready for $HOST"
