# COPILOT_DEPLOYMENT_REPORT.md

Generated: 2026-03-16 (updated)

---

## Files Created

| File | Purpose |
|------|---------|
| `deploy/systemd/market-lens-api.service` | API systemd service unit |
| `deploy/systemd/market-lens-worker.service` | Worker systemd service unit |
| `deploy/nginx/market-lens-api-location.conf` | nginx reverse proxy location block |
| `deploy/scripts/init_queue_dirs.sh` | Queue directory initializer |
| `deploy/scripts/run_api_local.sh` | Local development starter |
| `deploy/scripts/verify_api.sh` | Local API health verification |
| `deploy/scripts/install_systemd_services.sh` | Combined systemd installer |
| `deploy/scripts/verify_public_api.sh` | Public API verification via HTTPS |
| `deploy/scripts/show_nginx_api_snippet.sh` | Print nginx location block snippet |
| `deploy/scripts/show_nginx_target_info.sh` | Print nginx site config info |
| `deploy/docs/DEPLOY_API.md` | Production deployment guide |
| `deploy/docs/DEPLOY_NGINX.md` | nginx reverse proxy guide |
| `deploy/docs/DEPLOY_NGINX_SERVER_STEPS.md` | Server-specific nginx integration steps |
| `deploy/docs/COPILOT_DEPLOYMENT_REPORT.md` | This report |

---

## Directory Structure

```
market-lens/
├── api/
├── engine/
├── ingestion/
├── service/
├── worker/
├── tests/
│
└── deploy/
    ├── systemd/
    │   ├── market-lens-api.service
    │   └── market-lens-worker.service
    │
    ├── nginx/
    │   └── market-lens-api-location.conf
    │
    ├── scripts/
    │   ├── init_queue_dirs.sh
    │   ├── run_api_local.sh
    │   ├── verify_api.sh
    │   ├── install_systemd_services.sh
    │   ├── verify_public_api.sh
    │   ├── show_nginx_api_snippet.sh
    │   └── show_nginx_target_info.sh
    │
    └── docs/
        ├── DEPLOY_API.md
        ├── DEPLOY_NGINX.md
        ├── DEPLOY_NGINX_SERVER_STEPS.md
        └── COPILOT_DEPLOYMENT_REPORT.md
```

---

## systemd Service Definitions

### market-lens-api.service

```ini
[Unit]
Description=Market Lens API
After=network.target

[Service]
User=admin
Group=admin

WorkingDirectory=/home/admin/projects/market-lens

Environment=PYTHONPATH=/home/admin/projects/market-lens
Environment=MARKET_LENS_PROFILE=BASE
Environment=MARKET_LENS_QUEUE_DIR=/home/admin/projects/market-lens/var/queue
Environment=MARKET_LENS_SERVICE_MODE=production

ExecStart=/home/admin/projects/market-lens/venv/bin/uvicorn api.main:app --host 127.0.0.1 --port 8000

Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

### market-lens-worker.service

```ini
[Unit]
Description=Market Lens Worker
After=network.target

[Service]
User=admin
Group=admin
WorkingDirectory=/home/admin/projects/market-lens
Environment=PYTHONPATH=/home/admin/projects/market-lens
Environment=MARKET_LENS_PROFILE=BASE
Environment=MARKET_LENS_QUEUE_DIR=/home/admin/projects/market-lens/var/queue
Environment=MARKET_LENS_SERVICE_MODE=production
Environment=MARKET_LENS_POLL_INTERVAL=5
ExecStart=/home/admin/projects/market-lens/venv/bin/python -m worker.main
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

**Conformance note:** Worker service matches approved minimal spec (`After=network.target`, `RestartSec=3`).

---

## nginx Location Block

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

## Deployment Commands

### Install Services (Combined)

```bash
sudo bash deploy/scripts/install_systemd_services.sh
```

### Install Services (Manual)

```bash
sudo cp deploy/systemd/market-lens-api.service /etc/systemd/system/
sudo cp deploy/systemd/market-lens-worker.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable market-lens-api market-lens-worker
sudo systemctl start market-lens-api market-lens-worker
```

### Check Status

```bash
systemctl status market-lens-api
systemctl status market-lens-worker
```

### View Logs

```bash
journalctl -u market-lens-api -f
journalctl -u market-lens-worker -f
```

### Initialize Queue

```bash
bash deploy/scripts/init_queue_dirs.sh
```

### Configure nginx

See [DEPLOY_NGINX.md](DEPLOY_NGINX.md) for full instructions.

---

## Verification Commands

### Local Health Check

```bash
curl http://127.0.0.1:8000/health
```

### Local Version Check

```bash
curl http://127.0.0.1:8000/version
```

### Local Verification Script

```bash
bash deploy/scripts/verify_api.sh
```

### Public Verification Script

```bash
bash deploy/scripts/verify_public_api.sh dikenocracy.com
```

### Public Health Check

```bash
curl https://dikenocracy.com/api/health
```

---

## Expected Outputs

### `/health`

```json
{
  "status": "ok",
  "service": "market-lens-api",
  "protocol_version": "0.6.0",
  "constants_version": "0.6.0"
}
```

### `/version`

```json
{
  "protocol_version": "0.6.0",
  "constants_version": "0.6.0",
  "engine_version": "0.6.0",
  "service_mode": "production",
  "active_profile_default": "BASE",
  "psl_version": "PSL-2026-01-01"
}
```

---

## Server Deployment Checklist

- [ ] Pull latest from GitHub: `git pull origin main`
- [ ] Activate venv: `source venv/bin/activate` (use existing project virtual environment with installed locked dependencies)
- [ ] Initialize queue: `bash deploy/scripts/init_queue_dirs.sh`
- [ ] Install systemd services: `sudo bash deploy/scripts/install_systemd_services.sh`
- [ ] Start services: `sudo systemctl start market-lens-api market-lens-worker`
- [ ] Verify local health: `curl http://127.0.0.1:8000/health`
- [ ] Configure nginx: See DEPLOY_NGINX.md
- [ ] Test nginx config: `sudo nginx -t`
- [ ] Reload nginx: `sudo systemctl reload nginx`
- [ ] Verify public access: `bash deploy/scripts/verify_public_api.sh dikenocracy.com`

---

## Protocol Integrity

- `protocol_version`: `0.6.0` (unchanged)
- `constants_version`: `0.6.0` (unchanged)
- Engine code: not modified
- API code: not modified
- Tests: not modified

---

## nginx Server-Specific Deployment

### Active Configuration

- **Active nginx site file:** `/etc/nginx/sites-available/default`
- **Enabled symlink:** `/etc/nginx/sites-enabled/default`

### Location Block to Insert

Insert inside the HTTPS `server { ... }` block for `server_name dikenocracy.com www.dikenocracy.com;`:

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

### Verification Commands

```bash
sudo nginx -t
sudo systemctl reload nginx
curl -I https://dikenocracy.com/api/health
curl https://dikenocracy.com/api/health
curl https://dikenocracy.com/api/version
```

### Operator Warning

**The file `deploy/nginx/market-lens-api-location.conf` is NOT an executable script.**

It is an nginx configuration snippet intended for copy/paste into the active nginx site configuration only. Do not attempt to execute it as a shell command.
