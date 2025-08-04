#!/bin/bash
set -euo pipefail

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="full_backups/${TIMESTAMP}"
mkdir -p "$BACKUP_DIR/pg"
mkdir -p "$BACKUP_DIR/config"
mkdir -p "$BACKUP_DIR/redis"

echo "📦 Creating full backup in $BACKUP_DIR"

# --- PostgreSQL ---
for i in $(seq 1 8); do
  CONTAINER="augur_multi_host_augur${i}-db_1"
  OUTFILE="$BACKUP_DIR/pg/augur${i}_dump_${TIMESTAMP}.sql"
  if podman ps -a --format "{{.Names}}" | grep -q "^$CONTAINER$"; then
    echo "📄 Dumping PostgreSQL from $CONTAINER"
    podman exec "$CONTAINER" pg_dumpall -U augur > "$OUTFILE"
  else
    echo "⚠️  Skipping augur${i}-db: container not found"
  fi
done

# --- Redis dumps ---
for i in $(seq 1 8); do
  CONTAINER="augur_multi_host_augur${i}-redis_1"
  if podman ps -a --format "{{.Names}}" | grep -q "^$CONTAINER$"; then
    echo "📄 Attempting Redis dump from $CONTAINER"
    podman cp "$CONTAINER":/data/dump.rdb "$BACKUP_DIR/redis/augur${i}_dump.rdb" 2>/dev/null || \
      echo "⚠️  No dump.rdb found for augur${i}"
  fi
done

# --- Config files ---
echo "📝 Copying envs/, postgres/, docker-compose.yml"
cp -r envs "$BACKUP_DIR/config/"
cp -r postgres "$BACKUP_DIR/config/"
cp docker-compose.yml "$BACKUP_DIR/config/"

echo
echo "✅ Backup complete. Contents stored in $BACKUP_DIR"