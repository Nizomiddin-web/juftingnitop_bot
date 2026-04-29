# Deploy ko'rsatmasi

## VPS (Ubuntu) ga o'rnatish

```bash
# 1. Loyihani klon qiling
cd /home/ubuntu
git clone <repo-url> juftingni_top
cd juftingni_top

# 2. Virtualenv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt   # (yo'q bo'lsa, pastdagi paketlarni o'rnating)
# yoki:
pip install aiogram sqlalchemy aiosqlite python-dotenv geopy aiohttp APScheduler

# 3. .env fayl yarating
cat > .env << EOF
BOT_TOKEN=<token>
DB_URL=sqlite+aiosqlite:///nasib_ai.db
ADMIN_IDS=<sizning_id>
EOF

# 4. systemd service
sudo cp deploy/juftingni-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable juftingni-bot
sudo systemctl start juftingni-bot

# 5. Holatini tekshirish
sudo systemctl status juftingni-bot
tail -f /var/log/juftingni-bot.log
```

## Yangilanish

```bash
cd /home/ubuntu/juftingni_top
git pull
sudo systemctl restart juftingni-bot
```

## Backup

Bot ichida `/backup` admin komandasi DB faylini Telegram'ga yuboradi.

CLI orqali manual:
```bash
cp nasib_ai.db backups/nasib_ai_$(date +%Y%m%d).db
```

## Loglar

```bash
journalctl -u juftingni-bot -f      # systemd logi
tail -f /var/log/juftingni-bot.log  # service log
```
