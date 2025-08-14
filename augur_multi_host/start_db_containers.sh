#!/bin/bash
# start_db_containers.sh

set -euo pipefail

echo "🚀 Starting PostgreSQL containers only..."

for i in $(seq 1 8); do
  CONTAINER="augur_multi_host_augur${i}-db_1"

  # Check if container exists
  if podman container exists "$CONTAINER"; then
    STATE=$(podman inspect -f '{{.State.Status}}' "$CONTAINER")

    if [ "$STATE" != "running" ]; then
      echo "▶️  Starting $CONTAINER ..."
      podman start "$CONTAINER"
    else
      echo "✅ $CONTAINER is already running"
    fi
  else
    echo "⚠️  $CONTAINER does not exist (skipping)"
  fi
done

echo "🎉 All available PostgreSQL containers started."
