#!/usr/bin/env bash
set -euo pipefail

echo "sites-available:"
sudo ls -l /etc/nginx/sites-available
echo

echo "sites-enabled:"
sudo ls -l /etc/nginx/sites-enabled
echo

echo "HTTPS / server_name markers:"
sudo grep -RniE 'server_name|listen 443|ssl_certificate|ssl_certificate_key' /etc/nginx || true
