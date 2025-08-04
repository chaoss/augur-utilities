#!/bin/bash
# Run after `make up` has created new containers

set -euo pipefail

BACKUP_ROOT="full_backups"
LATEST=$(ls -1t "$BACKUP_ROOT" | head -n 1)
BACKUP_DIR="$BACKUP_ROOT/$LATEST/pg"

if [ ! -d "$BACKUP_DIR" ]; then
  echo "❌ No backup directory found at $BACKUP_DIR"
  exit 1
fi

echo "📦 Restoring PostgreSQL backups from: $BACKUP_DIR"

for i in $(seq 1 8); do
  CONTAINER="augur_multi_host_augur${i}-db_1"
  BACKUP_FILE="$BACKUP_DIR/augur${i}_dump_"*.sql

  if [ ! -f $BACKUP_FILE ]; then
    echo "⚠️  No SQL dump found for augur${i}, skipping"
    continue
  fi

  echo "🔁 Restoring augur${i} from $BACKUP_FILE"

  # Copy SQL into the container
  podman cp "$BACKUP_FILE" "$CONTAINER":/tmp/restore.sql

  # Run restore inside the container
  podman exec -i "$CONTAINER" psql -U augur -d postgres -f /tmp/restore.sql

  echo "✅ augur${i} restored"
done

echo
echo "🎉 All available backups restored."