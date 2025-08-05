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