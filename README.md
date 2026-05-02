**English** | [한국어](README.ko.md)

# pg-mig-webui

A web-based one-click migration tool for PostgreSQL (including PostGIS / pgRouting) databases.
Also works with servers that are only reachable through OpenVPN.

## Getting Started

### 1. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in `ENCRYPTION_KEY` and `JWT_SECRET`. Generation commands are included as comments in the file.

### 2. Start the services

```bash
docker compose up -d
```

### 3. Open in your browser

Visit `http://localhost`.

1. Sign up and log in — the first registered account automatically becomes the admin
2. Add a DB connection — upload an `.ovpn` file if the server requires VPN access
3. On the migration page, choose a source and a target, then click **Start Migration**

## Service Architecture

| Service  | Description |
|----------|-------------|
| nginx    | Reverse proxy (port 80) |
| backend  | FastAPI REST API + WebSocket |
| worker   | Celery worker (pg_dump / pg_restore, OpenVPN) |
| redis    | Task queue and progress pub/sub |
| frontend | React SPA served as static files via nginx |

## Environment Variables

| Variable         | Description |
|------------------|-------------|
| `ENCRYPTION_KEY` | Fernet key used to encrypt DB passwords and `.ovpn` files |
| `JWT_SECRET`     | Secret key used to sign JWT tokens |
| `REDIS_URL`      | Redis connection URL |
| `DATABASE_URL`   | SQLite database file path |

## License

Released under the MIT License — see [LICENSE.md](LICENSE.md).  
For third-party component licenses, see [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md).

---

© 2026 FEENTS
