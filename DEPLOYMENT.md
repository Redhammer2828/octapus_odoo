# Docker Deployment

This project can run as an Odoo 17 container with a PostgreSQL container.

## Start

```powershell
copy .env.example .env
docker compose up -d --build
```

Open Odoo at http://localhost:8086.

If you change `POSTGRES_USER`, `POSTGRES_PASSWORD`, or `ODOO_ADMIN_PASSWORD`
in `.env`, also update `odoo.deploy.conf` to match before starting the stack.

## Useful Commands

```powershell
docker compose logs -f odoo
docker compose ps
docker compose down
```

## Notes

- The container config is `odoo.deploy.conf`.
- Odoo loads addons from `/opt/odoo/addons` and `/opt/odoo/custom`.
- Persistent Odoo filestore and PostgreSQL data are stored in Docker volumes.
