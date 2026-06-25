#!/bin/bash
# نصب به عنوان سرویس systemd (برای سرور لینوکس)
# اجرا کنید: sudo bash setup_service.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
USER_NAME=$(logname 2>/dev/null || echo $SUDO_USER || echo $USER)

cat > /etc/systemd/system/chartonex.service << EOF
[Unit]
Description=Chartonex Tether Price Bot
After=network.target

[Service]
Type=simple
User=$USER_NAME
WorkingDirectory=$SCRIPT_DIR
ExecStart=$SCRIPT_DIR/venv/bin/gunicorn app:app --bind 0.0.0.0:5000 --workers 1 --threads 4 --timeout 120
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable chartonex
systemctl start chartonex

echo "سرویس نصب و فعال شد"
echo "وضعیت: systemctl status chartonex"
echo "لاگ: journalctl -u chartonex -f"
