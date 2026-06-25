#!/bin/bash
# اجرای ربات
cd "$(dirname "$0")"

if [ ! -d venv ]; then
    echo "اول bash install.sh را اجرا کنید"
    exit 1
fi

source venv/bin/activate
echo "ربات در حال اجرا است: http://localhost:5000"
gunicorn app:app --bind 0.0.0.0:5000 --workers 1 --threads 4 --timeout 120 --access-logfile - --error-logfile -
