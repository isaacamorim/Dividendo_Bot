#!/bin/bash
set -e   # para no primeiro erro

echo "=== Deploy iniciado: $(date) ==="
cd /opt/dividendo-bot

# Backend
echo "--- git pull ---"
git pull origin main

echo "--- pip install ---"
source venv/bin/activate
pip install -q -r backend/requirements.txt

echo "--- restart API ---"
systemctl restart dividendo-bot-api
sleep 3
systemctl is-active dividendo-bot-api || exit 1

# Frontend
echo "--- npm install ---"
cd frontend
npm install --silent

echo "--- build ---"
npm run build
# Só reinicia se o build passou (set -e garante isso)

echo "--- pm2 restart ---"
pm2 restart dividendo-bot-front

echo "=== Deploy concluído: $(date) ==="
