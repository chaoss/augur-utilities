import os
import sys
from pathlib import Path

INSTANCES = 8
AUGUR_PORT_BASE = 7000
REDIS_PORT_BASE = 7500
POSTGRES_PORT_BASE = 5430

# Read labels from labels.txt
with open("labels.txt") as f:
    labels = [line.strip() for line in f.readlines() if line.strip()]
    if len(labels) < INSTANCES:
        raise ValueError("Not enough labels in labels.txt for all instances")

# Ensure required directories exist
os.makedirs("envs", exist_ok=True)
os.makedirs("postgres", exist_ok=True)

# Compose file template pieces
compose_template = {
    "header": "version: '3.8'\n\nservices:\n",
    "volumes": "\nvolumes:\n",
    "networks": "\nnetworks:\n  knot:\n    driver: bridge\n"
}

services = []
volumes = []

for i in range(1, INSTANCES + 1):
    label = labels[i - 1].lower()
    label_value = labels[i - 1]
    port_offset = i
    
    app_port = AUGUR_PORT_BASE + port_offset
    redis_port = REDIS_PORT_BASE + port_offset
    pg_port = POSTGRES_PORT_BASE + port_offset

    # ENV file
    env_path = f"envs/instance{i}.env"
    with open(env_path, "w") as f:
        f.write(f"""# Instance {i} - {label_value}
AUGUR_DATABASE=augur
AUGUR_HOST=postgres-cache-{i}
AUGUR_PASSWORD=augur
AUGUR_PORT=5432
AUGUR_SCHEMA=augur_data
AUGUR_USERNAME=augur
DEBUG_8KNOT=False
REDIS_PASSWORD=redispass4
REDIS_CACHE_HOST=redis-cache-{i}
REDIS_CACHE_PORT=6379
REDIS_CACHE_PASSWORD=redispass4
DEFAULT_SEARCHBAR_LABEL={label_value}
AUGUR_LOGIN_ENABLED=False
""")

    # PostgreSQL volume
    pgdata_path = f"postgres/augur{i}"
    os.makedirs(pgdata_path, exist_ok=True)
    volumes.append(f"  pgdata{i}:")

    # Service definitions
    services.append(f"""  postgres-cache-{i}:
    image: postgres:17
    restart: unless-stopped
    environment:
      - POSTGRES_PASSWORD=augur
    volumes:
      - pgdata{i}:/var/lib/postgresql/data
    networks:
      - knot
    expose:
      - "5432"
    ports:
      - "{pg_port}:5432"
""")

    services.append(f"""  redis-cache-{i}:
    image: redis:7
    restart: unless-stopped
    command: redis-server --requirepass redispass4
    networks:
      - knot
    expose:
      - "6379"
    ports:
      - "{redis_port}:6379"
""")

    services.append(f"""  instance{i}:
    image: 8knot-instance
    build:
      context: ../8knot
    env_file:
      - envs/instance{i}.env
    depends_on:
      - postgres-cache-{i}
      - redis-cache-{i}
    networks:
      - knot
    ports:
      - "{app_port}:8080"
""")

# Write docker-compose.yml
with open("docker-compose.yml", "w") as f:
    f.write(compose_template["header"])
    for svc in services:
        f.write(svc + "\n")
    f.write(compose_template["volumes"])
    for vol in volumes:
        f.write(vol + "\n")
    f.write(compose_template["networks"])

print("✅ docker-compose.yml and envs regenerated for all instances")
