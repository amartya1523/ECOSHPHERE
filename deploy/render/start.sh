#!/usr/bin/env bash
set -euo pipefail

export PORT="${PORT:-10000}"
export ODOO_HTTP_PORT="${ODOO_HTTP_PORT:-8069}"
export ODOO_ADDONS_PATH="${ODOO_ADDONS_PATH:-/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons}"
export ODOO_MODULE="${ODOO_MODULE:-eco_sphere_esg}"

eval "$(
  python3 - <<'PY'
import os
import shlex
from urllib.parse import unquote, urlparse

def first(*names):
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    return ""

database_url = first("DATABASE_URL", "ODOO_DATABASE_URL", "POSTGRES_URL")
host_value = first("ODOO_DB_HOST", "POSTGRES_HOST", "HOST")

if not database_url and host_value.startswith(("postgres://", "postgresql://")):
    database_url = host_value
    host_value = ""

values = {
    "ODOO_DB_HOST": host_value,
    "ODOO_DB_PORT": first("ODOO_DB_PORT", "POSTGRES_PORT", "PORT_DB") or "5432",
    "ODOO_DB_USER": first("ODOO_DB_USER", "POSTGRES_USER") or "odoo",
    "ODOO_DB_PASSWORD": first("ODOO_DB_PASSWORD", "POSTGRES_PASSWORD", "PASSWORD"),
    "ODOO_DATABASE": first("ODOO_DATABASE", "POSTGRES_DB") or "ecosphere_db",
}

if database_url:
    url = urlparse(database_url)
    values.update({
        "ODOO_DB_HOST": url.hostname or "",
        "ODOO_DB_PORT": str(url.port or 5432),
        "ODOO_DB_USER": unquote(url.username or ""),
        "ODOO_DB_PASSWORD": unquote(url.password or ""),
        "ODOO_DATABASE": unquote((url.path or "").lstrip("/")) or values["ODOO_DATABASE"],
    })

for key, value in values.items():
    print(f"export {key}={shlex.quote(value)}")
PY
)"

if [[ -z "${ODOO_DB_HOST:-}" || -z "${ODOO_DB_USER:-}" || -z "${ODOO_DB_PASSWORD:-}" ]]; then
  echo "Missing database settings. Set DATABASE_URL or ODOO_DB_HOST, ODOO_DB_USER, and ODOO_DB_PASSWORD." >&2
  exit 1
fi

python3 - <<'PY'
import json
import os

config = {
    "odooBase": os.environ.get("FRONTEND_ODOO_BASE", "/odoo"),
    "odooDb": os.environ.get("FRONTEND_ODOO_DB") or os.environ.get("ODOO_DATABASE") or "ecosphere_db",
}
with open("/tmp/ecosphere-frontend-config.json", "w", encoding="utf-8") as handle:
    json.dump(config, handle)
PY

envsubst '${PORT} ${ODOO_HTTP_PORT}' \
  < /etc/ecosphere/nginx.conf.template \
  > /tmp/ecosphere-nginx.conf

echo "Waiting for PostgreSQL at ${ODOO_DB_HOST}:${ODOO_DB_PORT}..."
python3 - <<'PY'
import os
import socket
import sys
import time

host = os.environ["ODOO_DB_HOST"]
port = int(os.environ.get("ODOO_DB_PORT", "5432"))
deadline = time.time() + 90
while time.time() < deadline:
    try:
        with socket.create_connection((host, port), timeout=5):
            sys.exit(0)
    except OSError:
        time.sleep(2)
print(f"PostgreSQL was not reachable at {host}:{port}", file=sys.stderr)
sys.exit(1)
PY

COMMON_ARGS=(
  "--addons-path=${ODOO_ADDONS_PATH}"
  "--db_host=${ODOO_DB_HOST}"
  "--db_port=${ODOO_DB_PORT}"
  "--db_user=${ODOO_DB_USER}"
  "--db_password=${ODOO_DB_PASSWORD}"
  "--http-port=${ODOO_HTTP_PORT}"
  "--proxy-mode"
  "--no-database-list"
  "--db-filter=^${ODOO_DATABASE}$"
)

if [[ "${ODOO_AUTO_INIT:-1}" == "1" ]]; then
  echo "Installing/updating ${ODOO_MODULE} in ${ODOO_DATABASE}..."
  odoo "${COMMON_ARGS[@]}" \
    -d "${ODOO_DATABASE}" \
    -i "${ODOO_MODULE}" \
    --stop-after-init \
    --no-http
fi

echo "Starting Odoo on ${ODOO_HTTP_PORT} and Nginx on ${PORT}..."
odoo "${COMMON_ARGS[@]}" -d "${ODOO_DATABASE}" &
ODOO_PID=$!

nginx -c /tmp/ecosphere-nginx.conf -g "daemon off;" &
NGINX_PID=$!

trap 'kill "$ODOO_PID" "$NGINX_PID" 2>/dev/null || true' TERM INT
wait -n "$ODOO_PID" "$NGINX_PID"
