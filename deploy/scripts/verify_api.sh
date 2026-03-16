#!/usr/bin/env bash

echo "Health endpoint:"
curl -s http://127.0.0.1:8000/health
echo

echo "Version endpoint:"
curl -s http://127.0.0.1:8000/version
echo
