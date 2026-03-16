# Market Lens — nginx Server Integration Steps

## Current Server State

- **Active nginx site file:** `/etc/nginx/sites-available/default`
- **Enabled symlink:** `/etc/nginx/sites-enabled/default`
- Certbot-managed HTTPS for `dikenocracy.com` is already configured in this file.

---

## Step 1 — Backup Current Config

```bash
sudo cp /etc/nginx/sites-available/default /etc/nginx/sites-available/default.bak-2026-03-16
```

---

## Step 2 — Edit the Site Config

```bash
sudo nano /etc/nginx/sites-available/default
```

---

## Step 3 — Locate the HTTPS Server Block

Find the `server` block with:

```nginx
server_name dikenocracy.com www.dikenocracy.com;
```

This block should have `listen 443 ssl` and SSL certificate directives.

---

## Step 4 — Insert the Location Block

Inside the HTTPS `server { ... }` block, add:

```nginx
    # Market Lens API reverse proxy
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
```

Place it before the closing `}` of the server block.

---

## Step 5 — Test nginx Config

```bash
sudo nginx -t
```

Expected:
```
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

---

## Step 6 — Reload nginx

```bash
sudo systemctl reload nginx
```

---

## Step 7 — Verify Public Access

```bash
curl -I https://dikenocracy.com/api/health
curl https://dikenocracy.com/api/health
curl https://dikenocracy.com/api/version
```

Expected `/health` response:
```json
{"status":"ok","service":"market-lens-api","protocol_version":"0.6.0","constants_version":"0.6.0"}
```

---

## Warnings

**Do NOT:**

- Place the location block in the HTTP-only server block (port 80)
- Place the location block outside any `server { ... }` block
- Execute `deploy/nginx/market-lens-api-location.conf` as a shell command — it is an nginx config snippet for copy/paste only

---

## Helper Scripts

Print the exact snippet to insert:
```bash
bash deploy/scripts/show_nginx_api_snippet.sh
```

Show current nginx site info:
```bash
bash deploy/scripts/show_nginx_target_info.sh
```
