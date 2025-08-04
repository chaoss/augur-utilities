# 🧠 Augur Multi-Host Deployment + Restore Cheatsheet

This document summarizes the full setup, snapshotting, and restoration process using `make` targets and scripts.

---

## 🔧 Initial Setup

Before you begin:

- Ensure environment variables and paths are correct
- Confirm `AUGUR_PATH` points to your Augur clone

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

---

🚀 You're ready to deploy, preserve, and recover Augur with confidence!

