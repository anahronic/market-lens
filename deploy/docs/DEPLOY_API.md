# Market Lens API — Production Deployment Guide

## Prerequisites

- Ubuntu 22.04 server
- Python 3.10+ with venv
- nginx installed (for reverse proxy)
- Repository cloned to `/home/admin/projects/market-lens`
- Virtual environment at `/home/admin/projects/market-lens/venv`
- Dependencies installed: `pip install -e ".[dev]"` or `pip install fastapi uvicorn pydantic httpx`

---

## 1. Initialize Queue Directories

```bash
cd ~/projects/market-lens
bash deploy/scripts/init_queue_dirs.sh
```

---

## 2. Install systemd Service

```bash
sudo cp deploy/systemd/market-lens-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable market-lens-api
sudo systemctl start market-lens-api
```

---

## 3. Check Service Status

```bash
systemctl status market-lens-api
```

Expected output:
```
● market-lens-api.service - Market Lens API
     Loaded: loaded (/etc/systemd/system/market-lens-api.service; enabled)
     Active: active (running)
```

---

## 4. View Logs

```bash
journalctl -u market-lens-api -f
```

---

## 5. Health Check

```bash
curl http://127.0.0.1:8000/health
```

Expected response:
```json
{"status":"ok","service":"market-lens-api","protocol_version":"0.6.0","constants_version":"0.6.0"}
```

---

## 6. Version Check

```bash
curl http://127.0.0.1:8000/version
```

Expected response:
```json
{"protocol_version":"0.6.0","constants_version":"0.6.0","engine_version":"0.6.0","service_mode":"production","active_profile_default":"BASE","psl_version":"PSL-2026-01-01"}
```

---

## 7. Service Management Commands

| Command | Description |
|---------|-------------|
| `sudo systemctl start market-lens-api` | Start service |
| `sudo systemctl stop market-lens-api` | Stop service |
| `sudo systemctl restart market-lens-api` | Restart service |
| `sudo systemctl status market-lens-api` | Check status |
| `journalctl -u market-lens-api -f` | Follow logs |

---

## 8. Local Development (without systemd)

```bash
cd ~/projects/market-lens
bash deploy/scripts/run_api_local.sh
```

Or manually:
```bash
cd ~/projects/market-lens
source venv/bin/activate
PYTHONPATH=. uvicorn api.main:app --host 127.0.0.1 --port 8000
```

---

## 9. Verification Script

```bash
bash deploy/scripts/verify_api.sh
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MARKET_LENS_PROFILE` | `BASE` | Profile: BASE or HARDENED |
| `MARKET_LENS_QUEUE_DIR` | `./var/queue` | Queue directory path |
| `MARKET_LENS_SERVICE_MODE` | `local` | Service mode identifier |
| `MARKET_LENS_POLL_INTERVAL` | `5` | Worker poll interval (seconds) |

---

## 10. Install Worker Service

The background worker processes queued ingestion jobs.

```bash
sudo cp deploy/systemd/market-lens-worker.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable market-lens-worker
sudo systemctl start market-lens-worker
```

Check worker status:
```bash
systemctl status market-lens-worker
journalctl -u market-lens-worker -f
```

---

## 11. Combined Install Script

Install both API and worker services at once:

```bash
sudo bash deploy/scripts/install_systemd_services.sh
```

---

## 12. nginx Reverse Proxy

See [DEPLOY_NGINX.md](DEPLOY_NGINX.md) for detailed nginx configuration.

Quick summary:
1. Identify active site config: `ls -la /etc/nginx/sites-enabled/`
2. Add location block from `deploy/nginx/market-lens-api-location.conf`
3. Test: `sudo nginx -t`
4. Reload: `sudo systemctl reload nginx`

---

## 13. Public API Verification

After nginx is configured:

```bash
bash deploy/scripts/verify_public_api.sh dikenocracy.com
```

Or manually:
```bash
curl https://dikenocracy.com/api/health
```

---

## Full Deployment Order

1. `git pull origin main`
2. `pip install fastapi uvicorn pydantic httpx`
3. `bash deploy/scripts/init_queue_dirs.sh`
4. `sudo bash deploy/scripts/install_systemd_services.sh`
5. Configure nginx (see DEPLOY_NGINX.md)
6. `bash deploy/scripts/verify_public_api.sh dikenocracy.com`
