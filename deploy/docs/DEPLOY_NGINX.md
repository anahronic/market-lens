# Market Lens — nginx Reverse Proxy Configuration

## Overview

This guide explains how to configure nginx to reverse-proxy requests from `https://dikenocracy.com/api/` to the local Market Lens API running on `127.0.0.1:8000`.

---

## Prerequisites

- nginx installed and running
- Let's Encrypt SSL certificate configured for domain
- Market Lens API service running on port 8000

---

## 1. Identify Active Site Configuration

```bash
ls -la /etc/nginx/sites-enabled/
```

Look for the config file serving your domain (commonly named after the domain or `default`).

```bash
cat /etc/nginx/sites-enabled/<your-site-config>
```

Find the `server` block for the HTTPS listener (port 443).

---

## 2. Location Block Configuration

The location block to add is provided at:

```
deploy/nginx/market-lens-api-location.conf
```

Contents:

```nginx
location /api/ {
    proxy_pass http://127.0.0.1:8000/;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

---

## 3. Add Location Block to Site Config

Edit your active site config:

```bash
sudo nano /etc/nginx/sites-enabled/<your-site-config>
```

Inside the `server { ... }` block for port 443 (HTTPS), add the location block **before** the final `}`:

```nginx
server {
    listen 443 ssl;
    server_name dikenocracy.com;
    
    # ... existing SSL and other config ...
    
    # Market Lens API reverse proxy
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # ... other location blocks ...
}
```

---

## 4. Test nginx Configuration

```bash
sudo nginx -t
```

Expected output:
```
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

If there are errors, check syntax and fix before proceeding.

---

## 5. Reload nginx

```bash
sudo systemctl reload nginx
```

---

## 6. Verify Public Access

Test the API through the reverse proxy:

```bash
curl https://dikenocracy.com/api/health
```

Expected response:
```json
{"status":"ok","service":"market-lens-api","protocol_version":"0.6.0","constants_version":"0.6.0"}
```

Or use the verification script:

```bash
bash deploy/scripts/verify_public_api.sh dikenocracy.com
```

---

## Troubleshooting

### 502 Bad Gateway

- Check if API service is running: `systemctl status market-lens-api`
- Check if port 8000 is listening: `ss -tlnp | grep 8000`
- Check API logs: `journalctl -u market-lens-api -f`

### 404 Not Found

- Verify location block is inside the correct `server` block
- Check that `proxy_pass` ends with `/` (strips `/api/` prefix)

### Connection Refused

- Ensure API binds to `127.0.0.1:8000` (not just localhost)
- Check firewall: `sudo ufw status`

### nginx Errors

- Check nginx error log: `sudo tail -f /var/log/nginx/error.log`
- Check site-specific logs if configured

---

## URL Mapping

| Public URL | Internal URL |
|------------|--------------|
| `https://dikenocracy.com/api/health` | `http://127.0.0.1:8000/health` |
| `https://dikenocracy.com/api/version` | `http://127.0.0.1:8000/version` |
| `https://dikenocracy.com/api/v1/evaluate` | `http://127.0.0.1:8000/v1/evaluate` |
| `https://dikenocracy.com/api/v1/ingest` | `http://127.0.0.1:8000/v1/ingest` |

---

## Security Notes

- The API only binds to `127.0.0.1`, not accessible from external network directly
- nginx handles SSL termination
- Cloudflare provides additional DDoS protection if DNS proxied

---

## Current Server-Specific Path

On the current production server (`dikenocracy.com`):

- **Active nginx site file:** `/etc/nginx/sites-available/default`
- **Enabled symlink:** `/etc/nginx/sites-enabled/default`

The Certbot-managed HTTPS configuration for `dikenocracy.com` already exists in this file. The `/api/` location block must be inserted into the existing HTTPS `server { ... }` block for `server_name dikenocracy.com www.dikenocracy.com;`.

For step-by-step server-specific instructions, see [DEPLOY_NGINX_SERVER_STEPS.md](DEPLOY_NGINX_SERVER_STEPS.md).
