#!/usr/bin/env bash
set -e

REPO_URL="https://github.com/rezajavadi995/excel_ai_bot.git"
PROJECT_DIR="$HOME/excel_ai_bot"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Excel AI Bot | Universal Smart Installer (FINAL)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# =============================
# تشخیص محیط
# =============================

ENV_TYPE="linux"
PYTHON_BIN="python3"
BIN_DIR="/usr/local/bin"
NEED_SUDO=1

if [ -d "/data/data/com.termux/files" ]; then
    ENV_TYPE="termux"
    PYTHON_BIN="python"
    BIN_DIR="$HOME/.local/bin"
    NEED_SUDO=0
    mkdir -p "$BIN_DIR"
    echo "📱 محیط Termux شناسایی شد"
else
    echo "🖥 محیط Linux شناسایی شد"
fi

# =============================
# نصب پیش‌نیازهای سیستمی (فقط بار اول)
# =============================

if [ ! -f "$PROJECT_DIR/.system_ready" ]; then
    echo "📦 نصب پیش‌نیازهای سیستمی (یک‌بار)"

    if [ "$ENV_TYPE" = "linux" ]; then
        sudo apt update
        sudo apt install -y \
            git python3 python3-venv python3-dev python3-pip \
            build-essential libffi-dev libssl-dev rustc cargo
    else
        pkg install -y \
            git python clang make libffi openssl rust
    fi

    mkdir -p "$PROJECT_DIR"
    touch "$PROJECT_DIR/.system_ready"
else
    echo "⏩ پیش‌نیازهای سیستمی قبلاً نصب شده‌اند"
fi

# =============================
# دریافت یا بروزرسانی پروژه
# =============================

if [ -d "$PROJECT_DIR/.git" ]; then
    echo "🔄 پروژه موجود است → بروزرسانی کد"
    cd "$PROJECT_DIR"
    git pull
else
    echo "⬇️ دریافت پروژه از GitHub"
    git clone "$REPO_URL" "$PROJECT_DIR"
    cd "$PROJECT_DIR"
fi

# =============================
# ساخت virtualenv
# =============================

if [ ! -d "venv" ]; then
    echo "🐍 ساخت virtualenv"
    $PYTHON_BIN -m venv venv
fi

source venv/bin/activate

# =============================
# نصب پکیج‌های پایتون (فقط اگر لازم)
# =============================

if [ ! -f ".pip_ready" ]; then
    echo "📦 نصب وابستگی‌های پایتون"

    pip install --upgrade pip setuptools wheel
    pip install PySocks
    pip install -r requirements.txt --no-build-isolation

    touch .pip_ready
else
    echo "⏩ پکیج‌های پایتون قبلاً نصب شده‌اند"
fi

# =============================
# اجرای تست‌های هسته
# =============================

echo "🧪 اجرای تست هسته"
python test_project.py

echo "🧪 اجرای تست AI Command"
python test_ai_command.py

# =============================
# تنظیمات مدیر (فقط بار اول)
# =============================

if [ ! -f "config.py" ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🛠 تنظیمات مدیر ربات"

    read -p "توکن ربات تلگرام: " BOT_TOKEN
    read -p "Admin ID عددی: " ADMIN_ID

    cat > config.py <<EOF
BOT_TOKEN="${BOT_TOKEN}"
ADMIN_ID=${ADMIN_ID}
EOF

    echo "✅ تنظیمات ذخیره شد"
else
    echo "⏩ تنظیمات مدیر قبلاً انجام شده"
fi

# =============================
# ساخت لانچر هوشمند EXCEL
# =============================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔗 ساخت لانچر EXCEL"

EXCEL_PATH="$BIN_DIR/EXCEL"

LAUNCHER_CONTENT='#!/usr/bin/env bash
cd "$HOME/excel_ai_bot"
source venv/bin/activate

echo "━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Excel AI Bot Launcher"
echo "━━━━━━━━━━━━━━━━━━━━━━"
echo "1) اجرای ربات تلگرام (Production)"
echo "2) تست رابط کاربری ربات (Keyboard / UI)"
echo "3) تست هسته پردازش اکسل"
echo "4) تست فرمان هوشمند AI"
echo "5) خروج"
read -p "انتخاب: " CHOICE

case "$CHOICE" in
  1) python bot/main_bot.py ;;
  2) python bot/test_ui_bot.py ;;
  3) python test_project.py ;;
  4) python test_ai_command.py ;;
  *) exit 0 ;;
esac
'

if [ "$NEED_SUDO" -eq 1 ]; then
    echo "$LAUNCHER_CONTENT" | sudo tee "$EXCEL_PATH" > /dev/null
    sudo chmod +x "$EXCEL_PATH"
else
    echo "$LAUNCHER_CONTENT" > "$EXCEL_PATH"
    chmod +x "$EXCEL_PATH"
fi

# =============================
# PATH
# =============================

if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo "export PATH=\$PATH:$BIN_DIR" >> ~/.bashrc
    export PATH="$PATH:$BIN_DIR"
fi

# =============================
# پایان
# =============================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎯 نصب کامل و پایدار انجام شد"
echo "▶ برای اجرا:"
echo "    EXCEL"
echo "🔹 این دستور شما را وارد لانچر تست و اجرا می‌کند"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
