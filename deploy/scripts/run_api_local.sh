#!/usr/bin/env bash
set -e

cd ~/projects/market-lens

source venv/bin/activate

PYTHONPATH=. uvicorn api.main:app --host 127.0.0.1 --port 8000
