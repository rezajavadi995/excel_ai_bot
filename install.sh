#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/rezajavadi995/excel_ai_bot.git"
PROJECT_DIR="$HOME/excel_ai_bot"
APP_CONFIG_DIR="$HOME/.config/excel_ai_bot"
SECRETS_FILE="$APP_CONFIG_DIR/secrets.json"

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
fi

echo "🚀 Excel AI Bot Installer"

prompt_input() {
  local var_name="$1"
  local label="$2"

  if [ -r /dev/tty ]; then
    read -r -p "$label" "$var_name" < /dev/tty
  else
    read -r -p "$label" "$var_name"
  fi
}

install_deps() {
  if [ "$ENV_TYPE" = "linux" ]; then
    sudo apt update
    sudo apt install -y git python3 python3-venv python3-dev python3-pip build-essential libffi-dev libssl-dev
  else
    pkg install -y git python clang make libffi openssl
  fi
}

ensure_repo() {
  if [ -d "$PROJECT_DIR/.git" ]; then
    cd "$PROJECT_DIR"
    git reset --hard HEAD
    git pull || true
  else
    git clone "$REPO_URL" "$PROJECT_DIR"
    cd "$PROJECT_DIR"
  fi
}

ensure_venv() {
  if [ ! -d "venv" ]; then
    $PYTHON_BIN -m venv venv
  fi
  # shellcheck disable=SC1091
  source venv/bin/activate
  pip install --upgrade pip setuptools wheel
  pip install -r requirements.txt
}

mask_token() {
  local token="$1"
  if [ ${#token} -le 8 ]; then
    echo "********"
  else
    echo "${token:0:6}******${token: -2}"
  fi
}

write_secrets() {
  mkdir -p "$APP_CONFIG_DIR"
  chmod 700 "$APP_CONFIG_DIR"

  while true; do
    prompt_input BOT_TOKEN "🔑 توکن ربات تلگرام: "
    if [ -n "${BOT_TOKEN:-}" ]; then
      break
    fi
    echo "❌ توکن نباید خالی باشد"
  done

  while true; do
    prompt_input ADMIN_ID "👤 Admin ID عددی: "
    if [[ "${ADMIN_ID:-}" =~ ^[0-9]+$ ]]; then
      break
    fi
    echo "❌ ADMIN_ID باید عدد باشد"
  done

  cat > "$SECRETS_FILE" <<EOF
{
  "BOT_TOKEN": "$BOT_TOKEN",
  "ADMIN_ID": $ADMIN_ID
}
EOF
  chmod 600 "$SECRETS_FILE"
}

setup_secrets() {
  if [ -f "$SECRETS_FILE" ]; then
    local token admin
    token=$($PYTHON_BIN - <<PY
import json
from pathlib import Path
p = Path("$SECRETS_FILE")
data = json.loads(p.read_text())
print(data.get("BOT_TOKEN", ""))
PY
)
    admin=$($PYTHON_BIN - <<PY
import json
from pathlib import Path
p = Path("$SECRETS_FILE")
data = json.loads(p.read_text())
print(data.get("ADMIN_ID", ""))
PY
)

    echo "تنظیمات فعلی یافت شد:"
    echo "BOT_TOKEN=$(mask_token "$token")"
    echo "ADMIN_ID=$admin"
    prompt_input CONFIRM "آیا تایید می‌کنید؟ (y/n): "
    if [[ "$CONFIRM" != "y" && "$CONFIRM" != "Y" ]]; then
      write_secrets
    fi
  else
    write_secrets
  fi
}

create_launcher() {
  local excel_path="$BIN_DIR/EXCEL"
  local launcher='#!/usr/bin/env bash
set -e
cd "$HOME/excel_ai_bot"
source venv/bin/activate
export PYTHONPATH="$(pwd):$PYTHONPATH"

while true; do
  echo "1) اجرای ربات"
  echo "2) اجرای تست‌ها"
  echo "3) ریستارت سرویس"
  echo "4) خروج"
  read -r -p "انتخاب: " choice
  case "$choice" in
    1) python -m bot.main_bot ;;
    2) pytest -q ;;
    3)
      if command -v systemctl >/dev/null 2>&1; then
        sudo systemctl restart excel-ai-bot || true
        echo "سرویس ریستارت شد"
      else
        echo "systemctl در دسترس نیست"
      fi ;;
    4) exit 0 ;;
    *) echo "گزینه نامعتبر" ;;
  esac
done'

  if [ "$NEED_SUDO" -eq 1 ]; then
    echo "$launcher" | sudo tee "$excel_path" >/dev/null
    sudo chmod +x "$excel_path"
  else
    echo "$launcher" > "$excel_path"
    chmod +x "$excel_path"
  fi
}

setup_service() {
  if [ "$ENV_TYPE" = "linux" ] && command -v systemctl >/dev/null 2>&1; then
    cat <<EOF | sudo tee /etc/systemd/system/excel-ai-bot.service >/dev/null
[Unit]
Description=Excel AI Bot Telegram Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
Environment=PYTHONPATH=$PROJECT_DIR
ExecStart=$PROJECT_DIR/venv/bin/python -m bot.main_bot
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
    sudo systemctl daemon-reload
    sudo systemctl enable excel-ai-bot >/dev/null 2>&1 || true
    sudo systemctl restart excel-ai-bot || true
    echo "✅ systemd service configured: excel-ai-bot"
  elif [ "$ENV_TYPE" = "termux" ]; then
    mkdir -p "$HOME/.termux/boot"
    cat > "$HOME/.termux/boot/start_excel_ai_bot.sh" <<EOF
#!/data/data/com.termux/files/usr/bin/bash
cd "$PROJECT_DIR"
source venv/bin/activate
export PYTHONPATH="$PROJECT_DIR:\$PYTHONPATH"
nohup python -m bot.main_bot > "$HOME/.excel_ai_bot.log" 2>&1 &
EOF
    chmod +x "$HOME/.termux/boot/start_excel_ai_bot.sh"
    echo "✅ Termux boot script created at ~/.termux/boot/start_excel_ai_bot.sh"
    echo "برای اجرای خودکار بعد از بوت، اپ Termux:Boot را نصب کن."
  fi
}

install_deps
ensure_repo
ensure_venv
setup_secrets
create_launcher
setup_service

cd "$PROJECT_DIR"
pytest -q || true

echo "✅ نصب کامل شد. با دستور EXCEL اجرا کنید."
