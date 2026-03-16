#!/usr/bin/env bash
set -euo pipefail

sudo cp deploy/systemd/market-lens-api.service /etc/systemd/system/
sudo cp deploy/systemd/market-lens-worker.service /etc/systemd/system/

sudo systemctl daemon-reload
sudo systemctl enable market-lens-api
sudo systemctl enable market-lens-worker
sudo systemctl restart market-lens-api
sudo systemctl restart market-lens-worker

echo
echo "API status:"
systemctl --no-pager --full status market-lens-api || true

echo
echo "Worker status:"
systemctl --no-pager --full status market-lens-worker || true
