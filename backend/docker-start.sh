#!/usr/bin/env bash
set -euo pipefail

export ODOO_DATABASE="${ODOO_DATABASE:-ecosphere_db}"
export ODOO_MODULE="${ODOO_MODULE:-eco_sphere_esg}"
export ODOO_ADDONS_PATH="${ODOO_ADDONS_PATH:-/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons}"
export PORT="${PORT:-5432}"

COMMON_ARGS=(
  "--addons-path=${ODOO_ADDONS_PATH}"
  "--db_host=${HOST:-db}"
  "--db_port=${PORT}"
  "--db_user=${USER:-odoo}"
  "--db_password=${PASSWORD:?Set POSTGRES_PASSWORD in backend/.env}"
  "--db-filter=^${ODOO_DATABASE}$"
)

echo "Bootstrapping ${ODOO_MODULE} in database ${ODOO_DATABASE}..."
odoo "${COMMON_ARGS[@]}" \
  -d "${ODOO_DATABASE}" \
  -i "${ODOO_MODULE}" \
  --stop-after-init \
  --no-http

if [[ "${ECOSPHERE_SEED_DEMO_ACCOUNTS:-0}" == "1" ]]; then
  echo "Ensuring local EcoSphere demo accounts..."
  odoo shell "${COMMON_ARGS[@]}" -d "${ODOO_DATABASE}" --no-http <<'PY'
from odoo.addons.eco_sphere_esg.hooks import seed_demo_accounts

seed_demo_accounts(env)
env.cr.commit()
PY
fi

echo "Starting Odoo on database ${ODOO_DATABASE}..."
exec odoo "${COMMON_ARGS[@]}" -d "${ODOO_DATABASE}"
