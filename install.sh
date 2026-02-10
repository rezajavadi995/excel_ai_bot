#!/usr/bin/env bash

set -e

REPO_URL="https://github.com/rezajavadi995/excel_ai_bot.git"
PROJECT_DIR="excel_ai_bot"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Excel AI Bot | Universal Smart Installer (FINAL)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# =============================
# تشخیص محیط
# =============================

ENV_TYPE="linux"
PYTHON_BIN="python3"
BIN_DIR="/usr/local/bin"

if [ -d "/data/data/com.termux/files" ]; then
    ENV_TYPE="termux"
    PYTHON_BIN="python"
    BIN_DIR="$HOME/.local/bin"
    mkdir -p "$BIN_DIR"
    echo "📱 محیط Termux شناسایی شد"
else
    echo "🖥 محیط Linux شناسایی شد"
fi

# =============================
# نصب پیش‌نیازهای سیستمی
# =============================

echo "📦 نصب پیش‌نیازهای سیستمی (System Dependencies)"

if [ "$ENV_TYPE" = "linux" ]; then
    sudo apt update
    sudo apt install -y \
        git \
        python3 \
        python3-venv \
        python3-dev \
        python3-pip \
        build-essential \
        libffi-dev \
        libssl-dev \
        rustc \
        cargo
fi

if [ "$ENV_TYPE" = "termux" ]; then
    pkg install -y \
        git \
        python \
        clang \
        make \
        libffi \
        openssl \
        rust
fi

# =============================
# دریافت یا بروزرسانی پروژه
# =============================

if [ -d "$PROJECT_DIR/.git" ]; then
    echo "🔄 پروژه موجود است → بروزرسانی"
    cd "$PROJECT_DIR"
    git pull
else
    echo "⬇️ دریافت پروژه از GitHub"
    git clone "$REPO_URL"
    cd "$PROJECT_DIR"
fi

# =============================
# ساخت virtualenv
# =============================

if [ ! -d "venv" ]; then
    echo "🐍 ساخت virtualenv"
    $PYTHON_BIN -m venv venv
fi

# =============================
# فعال‌سازی virtualenv
# =============================

source venv/bin/activate

# =============================
# نصب پکیج‌های پایتون (ترتیب حیاتی)
# =============================

echo "📦 نصب وابستگی‌های پایتون"

pip install --upgrade pip setuptools wheel

# SOCKS فقط از PySocks (جلوگیری از build خراب)
pip install PySocks

# نصب باقی پکیج‌ها بدون isolation
pip install -r requirements.txt --no-build-isolation

# =============================
# اجرای تست‌های پروژه
# =============================

echo "🧪 اجرای تست هسته"
python test_project.py

echo "🧪 اجرای تست AI Command"
python test_ai_command.py

# =============================
# تنظیمات مدیر ربات
# =============================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🛠 تنظیمات مدیر ربات"

read -p "توکن ربات تلگرام (BotFather): " BOT_TOKEN
read -p "ID عددی مدیر (Admin ID): " ADMIN_ID

cat > config.py <<EOF
BOT_TOKEN="${BOT_TOKEN}"
ADMIN_ID=${ADMIN_ID}
EOF

echo "✅ تنظیمات مدیر ذخیره شد"

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

# اضافه شدن PATH در صورت نیاز
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo "export PATH=\$PATH:$BIN_DIR" >> ~/.bashrc
    export PATH="$PATH:$BIN_DIR"
fi

echo "✅ دستور EXCEL آماده استفاده است"

# =============================
# تست UI تلگرام
# =============================

echo "🧪 اجرای تست UI تلگرام (دکمه‌ها)"
python bot/test_ui_bot.py

# =============================
# پایان
# =============================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎯 نصب کامل و موفق"
echo "▶ اجرای ربات:"
echo "    EXCEL"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
