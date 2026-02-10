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

  read -r -p "🔑 توکن ربات تلگرام: " BOT_TOKEN
  read -r -p "👤 Admin ID عددی: " ADMIN_ID

  if ! [[ "$ADMIN_ID" =~ ^[0-9]+$ ]]; then
    echo "❌ ADMIN_ID باید عدد باشد"
    return 1
  fi

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
    token=$(python3 - <<PY
import json
from pathlib import Path
p = Path("$SECRETS_FILE")
data = json.loads(p.read_text())
print(data.get("BOT_TOKEN", ""))
PY
)
    admin=$(python3 - <<PY
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
    read -r -p "آیا تایید می‌کنید؟ (y/n): " CONFIRM
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

while true; do
  echo "1) اجرای ربات"
  echo "2) اجرای تست‌ها"
  echo "3) خروج"
  read -r -p "انتخاب: " choice
  case "$choice" in
    1) python bot/main_bot.py ;;
    2) pytest -q ;;
    3) exit 0 ;;
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

install_deps
ensure_repo
ensure_venv
setup_secrets
create_launcher

cd "$PROJECT_DIR"
pytest -q || true

echo "✅ نصب کامل شد. با دستور EXCEL اجرا کنید."
