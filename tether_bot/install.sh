#!/bin/bash
# =============================================
# Chartonex Tether Bot - نصب سریع
# =============================================
set -e

echo ""
echo "====================================="
echo "  نصب Chartonex Tether Bot"
echo "====================================="
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "خطا: Python 3 نصب نیست"
    exit 1
fi

PYTHON_VER=$(python3 -c 'import sys; print(sys.version_info.minor)')
if [ "$PYTHON_VER" -lt 10 ]; then
    echo "خطا: Python 3.10 یا بالاتر لازم است"
    exit 1
fi

# Create venv
echo "▶ ایجاد محیط مجازی..."
python3 -m venv venv

# Activate
source venv/bin/activate

# Install deps
echo "▶ نصب وابستگی‌ها..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

# Create .env if not exists
if [ ! -f .env ]; then
    cp .env.example .env
    SECRET=$(python3 -c "import secrets; print(secrets.token_hex(24))")
    sed -i "s/change-this-to-a-random-secret-key/$SECRET/" .env
    echo "▶ فایل .env ایجاد شد - لطفاً آن را ویرایش کنید"
fi

echo ""
echo "====================================="
echo "  نصب موفق!"
echo "====================================="
echo ""
echo "مراحل بعدی:"
echo "  1. فایل .env را ویرایش کنید"
echo "  2. اجرا: bash run.sh"
echo ""
