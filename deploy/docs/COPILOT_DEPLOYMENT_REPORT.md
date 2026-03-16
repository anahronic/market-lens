# COPILOT_DEPLOYMENT_REPORT.md

Generated: 2026-03-16

---

## Files Created

| File | Purpose |
|------|---------|
| `deploy/systemd/market-lens-api.service` | systemd service unit |
| `deploy/scripts/init_queue_dirs.sh` | Queue directory initializer |
| `deploy/scripts/run_api_local.sh` | Local development starter |
| `deploy/scripts/verify_api.sh` | API health verification |
| `deploy/docs/DEPLOY_API.md` | Production deployment guide |
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
    │   └── market-lens-api.service
    │
    ├── scripts/
    │   ├── init_queue_dirs.sh
    │   ├── run_api_local.sh
    │   └── verify_api.sh
    │
    └── docs/
        ├── DEPLOY_API.md
        └── COPILOT_DEPLOYMENT_REPORT.md
```

---

## systemd Service Definition

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

---

## Deployment Commands

### Install Service

```bash
sudo cp deploy/systemd/market-lens-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable market-lens-api
sudo systemctl start market-lens-api
```

### Check Status

```bash
systemctl status market-lens-api
```

### View Logs

```bash
journalctl -u market-lens-api -f
```

### Initialize Queue

```bash
bash deploy/scripts/init_queue_dirs.sh
```

---

## Verification Commands

### Health Check

```bash
curl http://127.0.0.1:8000/health
```

### Version Check

```bash
curl http://127.0.0.1:8000/version
```

### Full Verification Script

```bash
bash deploy/scripts/verify_api.sh
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
- [ ] Install dependencies: `pip install fastapi uvicorn pydantic httpx`
- [ ] Initialize queue: `bash deploy/scripts/init_queue_dirs.sh`
- [ ] Install systemd service: `sudo cp deploy/systemd/market-lens-api.service /etc/systemd/system/`
- [ ] Enable service: `sudo systemctl enable market-lens-api`
- [ ] Start service: `sudo systemctl start market-lens-api`
- [ ] Verify health: `curl http://127.0.0.1:8000/health`

---

## Protocol Integrity

- `protocol_version`: `0.6.0` (unchanged)
- `constants_version`: `0.6.0` (unchanged)
- Engine code: not modified
- API code: not modified
- Tests: not modified
