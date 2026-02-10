#!/usr/bin/env bash

set -e

REPO_URL="https://github.com/rezajavadi995/excel_ai_bot.git"
PROJECT_DIR="excel_ai_bot"
PYTHON_BIN="python3"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Excel AI Bot | Smart Installer (Final)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# تشخیص محیط
if [ -d "/data/data/com.termux/files" ]; then
    echo "📱 محیط Termux شناسایی شد"
    PYTHON_BIN="python"
fi

# بررسی git
if ! command -v git >/dev/null 2>&1; then
    echo "❌ git نصب نیست"
    echo "👉 نصب کن:"
    echo "   apt install git"
    exit 1
fi

# بررسی پایتون
if ! command -v $PYTHON_BIN >/dev/null 2>&1; then
    echo "❌ Python نصب نیست"
    echo "👉 نصب کن:"
    echo "   apt install python"
    exit 1
fi

# دانلود یا آپدیت پروژه
if [ -d "$PROJECT_DIR/.git" ]; then
    echo "🔄 پروژه وجود دارد → بروزرسانی"
    cd $PROJECT_DIR
    git pull
else
    echo "⬇️ دانلود پروژه از GitHub"
    git clone $REPO_URL
    cd $PROJECT_DIR
fi

# ساخت virtualenv
if [ ! -d "venv" ]; then
    echo "🐍 ساخت virtualenv"
    $PYTHON_BIN -m venv venv
fi

# فعال‌سازی
source venv/bin/activate

# نصب پیش‌نیازها
echo "📦 نصب پیش‌نیازها"
pip install --upgrade pip
pip install -r requirements.txt

# اجرای تست‌ها
echo "🧪 اجرای تست اولیه پروژه (test_project.py)"
if python test_project.py; then
    echo "✅ test_project.py با موفقیت اجرا شد"
else
    echo "❌ خطا در اجرای test_project.py"
    exit 1
fi

echo "🧪 اجرای تست AI Command Mode (test_ai_command.py)"
if python test_ai_command.py; then
    echo "✅ test_ai_command.py با موفقیت اجرا شد"
else
    echo "❌ خطا در اجرای test_ai_command.py"
    exit 1
fi


echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🛠 تنظیمات مدیر ربات"
read -p "توکن ربات تلگرام (از BotFather): " BOT_TOKEN
read -p "ID عددی مدیر: " ADMIN_ID

cat > config.py <<EOL
BOT_TOKEN = "${BOT_TOKEN}"
ADMIN_ID = ${ADMIN_ID}
EOL

echo "✅ توکن و ادمین ست شد"
#

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎯 نصب و تست کامل پروژه با موفقیت انجام شد"
echo "🎉 پروژه آماده استفاده است"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
