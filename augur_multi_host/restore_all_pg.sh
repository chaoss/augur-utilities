#!/bin/bash
# Run after `make up` has created new containers

set -euo pipefail

BACKUP_ROOT="pg_backups"
LATEST=$(ls -1t "$BACKUP_ROOT" | head -n 1)
BACKUP_DIR="$BACKUP_ROOT/$LATEST"

if [ ! -d "$BACKUP_DIR" ]; then
  echo "❌ No backup directory found at $BACKUP_DIR"
  exit 1
fi

echo "📦 Restoring PostgreSQL backups from: $BACKUP_DIR"

for i in $(seq 1 8); do
  CONTAINER="augur_multi_host_augur${i}-db_1"
  BACKUP_FILE=$(ls "$BACKUP_DIR"/augur${i}_dump_*.sql.gz 2>/dev/null || true)

  if [ ! -f "$BACKUP_FILE" ]; then
    echo "⚠️  No SQL dump found for augur${i}, skipping"
    continue
  fi

  # Check if container is running
  if ! podman inspect -f '{{.State.Running}}' "$CONTAINER" 2>/dev/null | grep -q true; then
    echo "⏹️  Container $CONTAINER is not running, skipping"
    continue
  fi

  echo "🧹 Dropping and recreating 'augur' database in $CONTAINER"
  podman exec -i "$CONTAINER" psql -U augur -d postgres -c "DROP DATABASE IF EXISTS augur;"
  podman exec -i "$CONTAINER" psql -U augur -d postgres -c "CREATE DATABASE augur;"

  echo "🔁 Restoring augur${i} from $BACKUP_FILE"
  gunzip -c "$BACKUP_FILE" | podman exec -i "$CONTAINER" psql -U augur -d augur

  echo "✅ augur${i} restored"
done

echo
echo "🎉 All available backups restored."
