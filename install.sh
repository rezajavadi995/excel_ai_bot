#!/usr/bin/env bash

set -e

REPO_URL="https://github.com/rezajavadi995/excel_ai_bot.git"
PROJECT_DIR="excel_ai_bot"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Excel AI Bot | Universal Smart Installer"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# =============================
# تشخیص محیط
# =============================

ENV_TYPE="linux"
PYTHON_BIN="python3"
PKG_INSTALL=""
BIN_DIR="/usr/local/bin"

if [ -d "/data/data/com.termux/files" ]; then
    ENV_TYPE="termux"
    PYTHON_BIN="python"
    PKG_INSTALL="pkg install -y"
    BIN_DIR="$HOME/.local/bin"
    mkdir -p "$BIN_DIR"
    echo "📱 محیط Termux شناسایی شد"
else
    PKG_INSTALL="apt install -y"
    echo "🖥 محیط Linux شناسایی شد"
fi

# =============================
# نصب پیش‌نیازهای سیستمی
# =============================

echo "📦 بررسی و نصب پیش‌نیازهای سیستمی"

if ! command -v git >/dev/null 2>&1; then
    echo "🔧 نصب git"
    $PKG_INSTALL git
fi

if ! command -v $PYTHON_BIN >/dev/null 2>&1; then
    echo "🔧 نصب python"
    $PKG_INSTALL python python3 python3-venv
fi

# مخصوص Termux برای پکیج‌های باینری
if [ "$ENV_TYPE" = "termux" ]; then
    $PKG_INSTALL clang make libffi openssl
fi

# =============================
# دانلود یا بروزرسانی پروژه
# =============================

if [ -d "$PROJECT_DIR/.git" ]; then
    echo "🔄 پروژه وجود دارد → بروزرسانی"
    cd $PROJECT_DIR
    git pull
else
    echo "⬇️ دانلود پروژه از GitHub"
    git clone $REPO_URL
    cd $PROJECT_DIR
fi

# =============================
# ساخت virtualenv
# =============================

if [ ! -d "venv" ]; then
    echo "🐍 ساخت virtualenv"
    $PYTHON_BIN -m venv venv
fi

# =============================
# فعال‌سازی virtualenv (در Installer)
# =============================

source venv/bin/activate

# =============================
# نصب پکیج‌های پایتون
# =============================

echo "📦 نصب پیش‌نیازهای پایتونی"
pip install --upgrade pip
pip install PySocks
pip install -r requirements.txt

# =============================
# اجرای تست‌های هسته
# =============================

echo "🧪 اجرای تست اولیه پروژه (test_project.py)"
python test_project.py

echo "🧪 اجرای تست AI Command Mode (test_ai_command.py)"
python test_ai_command.py

# =============================
# تنظیمات مدیر ربات
# =============================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🛠 تنظیمات مدیر ربات"

read -p "توکن ربات تلگرام (BotFather): " BOT_TOKEN
read -p "ID عددی مدیر (Admin ID): " ADMIN_ID

cat > config.py <<EOF
BOT_TOKEN = "${BOT_TOKEN}"
ADMIN_ID = ${ADMIN_ID}
EOF

echo "✅ توکن و ادمین با موفقیت ثبت شدند"

# =============================
# ساخت دستور سراسری EXCEL
# =============================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔗 ساخت دستور سراسری EXCEL"

EXCEL_PATH="$BIN_DIR/EXCEL"

cat > "$EXCEL_PATH" <<EOF
#!/usr/bin/env bash
cd "$(pwd)"
source venv/bin/activate
python bot/main_bot.py
EOF

chmod +x "$EXCEL_PATH"

# اضافه کردن BIN_DIR به PATH اگر نبود
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo "export PATH=\$PATH:$BIN_DIR" >> ~/.bashrc
    export PATH="$PATH:$BIN_DIR"
fi

echo "✅ دستور EXCEL آماده شد"

# =============================
# اجرای تست UI تلگرام
# =============================

echo "🧪 اجرای تست UI با دکمه‌های تلگرام"
python bot/test_ui_bot.py

# =============================
# پایان
# =============================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎯 نصب کامل و موفق"
echo "📌 اجرای ربات:"
echo "    EXCEL"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
