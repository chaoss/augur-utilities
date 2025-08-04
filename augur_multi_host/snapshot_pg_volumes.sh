#!/bin/bash
# Usage: ./snapshot_pg_volumes.sh

set -euo pipefail

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="pg_backups/$TIMESTAMP"
mkdir -p "$BACKUP_DIR"

echo "🔐 Creating PostgreSQL volume snapshots..."
echo "📁 Backup directory: $BACKUP_DIR"
echo

# Find all containers with "db" in the name
CONTAINERS=$(podman ps -a --format "{{.Names}}" | grep db || true)

if [[ -z "$CONTAINERS" ]]; then
  echo "❌ No database containers found."
  exit 1
fi

for CONTAINER in $CONTAINERS; do
  echo "📦 Dumping database from: $CONTAINER"

  # Extract instance label, e.g., augur1, augur2
  INSTANCE=$(echo "$CONTAINER" | grep -o 'augur[0-9]\+' || echo "$CONTAINER")
  OUTPUT_FILE="$BACKUP_DIR/${INSTANCE}_dump_${TIMESTAMP}.sql.gz"

  if podman exec "$CONTAINER" pg_dumpall -U augur | gzip > "$OUTPUT_FILE"; then
    echo "✅ Compressed and saved: $OUTPUT_FILE"
  else
    echo "❌ Failed to dump: $CONTAINER"
  fi
done

echo
echo "🎉 All detected database containers have been backed up (gzipped)."