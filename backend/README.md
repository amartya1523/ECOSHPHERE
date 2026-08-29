# Run the EcoSphere Odoo backend

The backend is an Odoo addon, so it needs both an Odoo server and PostgreSQL.

## Docker (recommended)

1. Install and open [Docker Desktop](https://www.docker.com/products/docker-desktop/).
2. Create the environment file:

   ```bash
   cd /Users/sanketmistry/Desktop/Ecosphere/ECOSHPHERE/backend
   cp .env.example .env
   ```

3. Open `.env` and change `POSTGRES_PASSWORD` to a strong local password.
4. Start PostgreSQL and Odoo:

   ```bash
   docker compose up -d
   ```

5. Open `http://localhost:8069`.
6. Sign in after Docker finishes bootstrapping the `ecosphere_db` database and installing the EcoSphere module.

   Local Docker also creates two demo accounts:

   ```text
   admin@ecosphere.local / Admin@EcoSphere2026
   employee@ecosphere.local / Employee@EcoSphere2026
   ```

Docker mounts this `backend/` folder into Odoo as `/mnt/extra-addons/eco_sphere_esg`. That keeps the local project simple while preserving the Odoo technical module name `eco_sphere_esg`.

## Useful commands

```bash
# Follow Odoo logs
docker compose logs -f odoo

# Stop containers (keeps database data)
docker compose down

# Restart after Python/XML changes
docker compose restart odoo

# Update the EcoSphere module after backend changes
docker compose exec odoo odoo -d ecosphere_db --db_host=db --db_user=odoo --db_password="$POSTGRES_PASSWORD" --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons -u eco_sphere_esg --stop-after-init --no-http

# Run the EcoSphere module tests
docker compose exec odoo odoo -d ecosphere_test --db_host=db --db_user=odoo --db_password="$POSTGRES_PASSWORD" --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons -i eco_sphere_esg --test-enable --test-tags /eco_sphere_esg --stop-after-init --no-http --http-port=8071 --without-demo=all
```

Do not run `docker compose down -v` unless you intentionally want to delete the local PostgreSQL database.
