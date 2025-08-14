# 🧠 Augur Multi-Host Deployment + Restore Cheatsheet

This document summarizes the full setup, snapshotting, and restoration process using `make` targets and scripts.

---

## 🔧 Initial Setup

Before you begin:

- Ensure environment variables and paths are correct
- Confirm `AUGUR_PATH` points to your Augur clone. Note that if you are working from a symlinked path, you need to, at least on OSX, use the actual, physical path. 

### ✅ Run a full deployment and restore

```bash
make AUGUR_PATH=/absolute/path/to/augur bootstrap-restore 
```

This performs:

1. `regen` (with `--force`)
2. `build`
3. `up`
4. `restore-all` (from most recent backup)

---

## 📅 Create Backups

### ▶️ Full backup of all databases, config files, and Redis dumps

```bash
make snapshot-all
```

Creates:

```
full_backups/20250804_130215/
├── pg/
│   ├── augur1_dump_20250804_130215.sql
│   └── ...
├── redis/
│   ├── augur1_dump.rdb
│   └── ...
└── config/
    ├── envs/
    ├── postgres/
    └── docker-compose.yml
```

---

## ↺ Restore Databases Only

### ▶️ After `make up`, restore all database containers:

```bash
make restore-all
```

- Uses latest timestamped backup from `full_backups/`
- Automatically skips any augurX instance without a backup

---

## 📆 Manual Database Restore (individual)

```bash
podman cp full_backups/20250804_130215/pg/augur4_dump_20250804_130215.sql augur_multi_host_augur4-db_1:/tmp/dump.sql
podman exec -i augur_multi_host_augur4-db_1 psql -U augur -d postgres -f /tmp/dump.sql
```

---

## 💪 Maintenance Targets

| Command                   | Description                                       |
|---------------------------|---------------------------------------------------|
| `make regen`              | Rebuilds env and config (default: interactive)   |
| `make build`              | Builds all service images                        |
| `make up`                 | Brings up containers in detached mode            |
| `make down`               | Stops and removes containers                     |
| `make snapshot`           | pg-only backup using `pg_dumpall`                |
| `make snapshot-all`       | pg + redis + config backups                      |
| `make restore-all`        | Restores databases from latest snapshot          |
| `make bootstrap-restore`  | Full deploy and restore (regen, build, up, restore) |

```bash
make restore-db FILE=db_snapshots/augur1-postgres-20250804_154412.tar.gz
```

---

🚀 You're ready to deploy, preserve, and recover Augur with confidence!

# 📦 Augur Multi-Instance Makefile — Help Table

## 🛠 Core Deployment Commands

| Command                   | Description                                                                 |
|---------------------------|-----------------------------------------------------------------------------|
| `make regen`              | Regenerates PostgreSQL configs and `docker-compose.yml`                    |
| `make build`              | Builds all service images using Podman Compose                             |
| `make up`                 | Brings up all containers in detached mode                                  |
| `make down`               | Stops and removes containers and orphaned networks                         |
| `make restart`            | Restarts all running containers                                             |
| `make all`                | Alias for `make up`                                                         |
| `make bootstrap`          | Runs full deploy: `regen → build → up`                                     |
| `make bootstrap-restore`  | Full deploy with restore: `regen → build → up → restore-all`               |

## 📦 Snapshot & Restore

| Command                     | Description                                                               |
|-----------------------------|---------------------------------------------------------------------------|
| `make snapshot`             | pg-only backup using `pg_dumpall` via `snapshot_pg_volumes.sh`            |
| `make snapshot-db`          | Raw volume archive of each `augurX-postgres` to `.tar.gz`                 |
| `make snapshot-all`         | Full backup of PostgreSQL, Redis, and config via `snapshot_all.sh`        |
| `make restore-db FILE=...`  | Restores a specific `augurX` DB volume from snapshot tarball              |

## 🧰 Admin & Utilities

| Command            | Description                                                      |
|--------------------|------------------------------------------------------------------|
| `make ps`          | Lists all running containers                                     |
| `make logs`        | Tails logs for `augur$(INSTANCE)`                                |
| `make shell`       | Opens a bash shell inside `augur$(INSTANCE)` container          |
| `make status`      | Checks for missing `envs/augurX.env` files for each instance     |

## 🧹 Teardown & Cleanup

| Command               | Description                                                               |
|------------------------|---------------------------------------------------------------------------|
| `make stop-all`        | Stops all running Podman containers                                       |
| `make clean`           | Removes containers/images/networks but **preserves DB volumes**          |
| `make nuke`            | Removes instance containers and non-DB volumes + networks                |
| `make clean-networks`  | Removes networks with `augur_multi_host_` prefix                         |

## 🌐 SSL & Nginx Setup

| Command          | Description                                             |
|------------------|---------------------------------------------------------|
| `make nginx`     | Generates Nginx config for all instances                |
| `make certbot`   | Runs Certbot to issue SSL certificates for subdomains  |