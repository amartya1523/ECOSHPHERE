# Run the EcoSphere Odoo backend

The backend is an Odoo addon, so it needs both an Odoo server and PostgreSQL.

## Docker (recommended)

1. Install and open [Docker Desktop](https://www.docker.com/products/docker-desktop/).
2. Create the environment file:

   ```bash
   cd /Users/amartyavikramsingh/Desktop/project/ECOshphere/backend
   cp .env.example .env
   ```

3. Open `.env` and change `POSTGRES_PASSWORD` to a strong local password.
4. Start PostgreSQL and Odoo:

   ```bash
   docker compose up -d
   ```

5. Open `http://localhost:8069`.
6. Create a database named `ecosphere_db` in the Odoo database manager.
7. In Odoo, open **Apps** → **Update Apps List** → search **EcoSphere ESG Management** → **Install**.

## Useful commands

```bash
# Follow Odoo logs
docker compose logs -f odoo

# Stop containers (keeps database data)
docker compose down

# Restart after Python/XML changes
docker compose restart odoo
```

Do not run `docker compose down -v` unless you intentionally want to delete the local PostgreSQL database.
