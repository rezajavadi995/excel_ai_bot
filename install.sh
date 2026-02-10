#!/bin/bash

set -e

REPO_URL="https://github.com/rezajavadi995/excel_ai_bot.git"
PROJECT_DIR="excel_ai_bot"

echo "🚀 شروع نصب پروژه Excel AI Bot"

# بررسی git
if ! command -v git &> /dev/null; then
    echo "❌ git نصب نیست"
    exit 1
fi

# بررسی python
if ! command -v python3 &> /dev/null; then
    echo "❌ python3 نصب نیست"
    exit 1
fi

# کلون پروژه
if [ -d "$PROJECT_DIR" ]; then
    echo "📁 پوشه پروژه وجود دارد، pull انجام می‌شود"
    cd $PROJECT_DIR
    git pull
else
    echo "⬇️ در حال دانلود پروژه از GitHub"
    git clone $REPO_URL
    cd $PROJECT_DIR
fi

# ساخت virtualenv
echo "🐍 ساخت محیط مجازی"
python3 -m venv venv
source venv/bin/activate

# نصب پیش‌نیازها
echo "📦 نصب پیش‌نیازها"
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ نصب کامل شد"

# اجرای تست
echo "🧪 اجرای تست اولیه پروژه"
python test_project.py

echo "🎉 همه چیز با موفقیت انجام شد"
