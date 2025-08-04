#!/bin/bash
# Run with: ./snapshot_pg_volumes.sh

set -euo pipefail

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="pg_backups/$TIMESTAMP"
mkdir -p "$BACKUP_DIR"

echo "🔐 Creating PostgreSQL volume snapshots..."
echo "📁 Backup directory: $BACKUP_DIR"
echo

for i in $(seq 1 8); do
  CONTAINER="augur_multi_host_augur${i}-db_1"

  if podman ps -a --format "{{.Names}}" | grep -q "^$CONTAINER$"; then
    echo "📦 Dumping database from container: $CONTAINER"
    OUTPUT_FILE="$BACKUP_DIR/augur${i}_dump_${TIMESTAMP}.sql"
    podman exec "$CONTAINER" pg_dumpall -U augur > "$OUTPUT_FILE"
    echo "✅ Saved: $OUTPUT_FILE"
  else
    echo "⚠️  Skipping augur${i}: container not found"
  fi
done

echo
echo "🎉 All available databases have been backed up."