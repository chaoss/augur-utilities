import os
import sys
from pathlib import Path

# Configuration
instances = 8
labels = ["alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta"]
augur_path = sys.argv[1] if len(sys.argv) > 1 else "."
force = "--force" in sys.argv

# Docker Compose template
template = """version: '3.8'

services:
{services}

volumes:
{volumes}

networks:
{networks}
"""

# PostgreSQL config content
postgres_conf_template = """listen_addresses = '*'
max_connections = 1000
shared_buffers = 1GB
work_mem = 64MB
maintenance_work_mem = 256MB
effective_cache_size = 2GB
wal_buffers = 64MB
max_wal_size = 1GB
min_wal_size = 80MB
hba_file = '/etc/postgresql/pg_hba.conf'
"""

## Generate .env file
def generate_env_file(i):
    env_path = Path(f"envs/instance{i}.env")
    if env_path.exists() and not force:
        print(f"Skipping {env_path}")
        return

    label = labels[i - 1] if i - 1 < len(labels) else f"instance{i}"

    env_content = f"""POSTGRES_DB=augur
POSTGRES_USER=augur
POSTGRES_PASSWORD=augur
REDIS_PASSWORD=redispass{i}
AUGUR_PORT={7000 + i}
AUGUR_DATABASE=augur
AUGUR_USERNAME=augur
AUGUR_PASSWORD=augur
AUGUR_HOST=192.168.1.126
AUGUR_SCHEMA=augur_data
AUGUR_LOGIN_ENABLED=False
DEFAULT_SEARCHBAR_LABEL={label}
REDIS_USERS_HOST=redis-users-{i}
REDIS_USERS_PORT=6379
REDIS_USERS_PASSWORD=redispass4
REDIS_CACHE_HOST=redis-cache-{i}
REDIS_CACHE_PORT=6379
REDIS_CACHE_PASSWORD=redispass4
POSTGRES_CACHE=postgres-cache-{i}"""
    env_path.write_text(env_content.strip())
    print(f"✅ Wrote {env_path}")

# Generate service block
def generate_service_block(i):
    network = f"knot{i}"
    http_port = 8080 + i
    redis_cmd = 'redis-server --requirepass "$$REDIS_PASSWORD"'
    return f"""
  redis-cache-{i}:
    image: docker.io/library/redis:6
    command: ["/bin/sh", "-c", "{redis_cmd}"]
    env_file: [envs/instance{i}.env]
    restart: always
    networks: [{network}]

  redis-users-{i}:
    image: docker.io/library/redis:6
    command: ["/bin/sh", "-c", "{redis_cmd}"]
    env_file: [envs/instance{i}.env]
    restart: always
    networks: [{network}]

  postgres-cache-{i}:
    image: docker.io/library/postgres:17
    command: ["postgres", "-c", "config_file=/etc/postgresql/postgresql.conf"]
    restart: unless-stopped
    environment:
      - POSTGRES_DB=augur
      - POSTGRES_USER=augur
      - POSTGRES_PASSWORD=augur
      - PGDATA=/var/lib/postgresql/data/pgdata
    volumes:
      - augur{i}_db_data:/var/lib/postgresql/data
      - ./postgres/augur{i}/postgresql.conf:/etc/postgresql/postgresql.conf
      - ./postgres/augur{i}/pg_hba.conf:/etc/postgresql/pg_hba.conf
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U augur"]
      interval: 5s
      timeout: 5s
      retries: 5
    networks: [{network}]

  db-init-{i}:
    build:
      context: {augur_path}
      dockerfile: docker/Dockerfile
    command: ["python3", "./cache_manager/db_init.py"]
    depends_on:
      postgres-cache-{i}:
        condition: service_healthy
    env_file: [envs/instance{i}.env]
    restart: on-failure:1000
    networks: [{network}]

  worker-callback-{i}:
    build:
      context: {augur_path}
      dockerfile: docker/Dockerfile
    command: ["celery", "-A", "app:celery_app", "worker", "--loglevel=INFO", "--concurrency=1", "--time-limit=300", "--soft-time-limit=240"]
    depends_on:
      - postgres-cache-{i}
      - redis-cache-{i}
      - redis-users-{i}
    env_file: [envs/instance{i}.env]
    restart: always
    networks: [{network}]

  worker-query-{i}:
    build:
      context: {augur_path}
      dockerfile: docker/Dockerfile
    command: ["celery", "-A", "app:celery_app", "worker", "--loglevel=INFO", "-Q", "data", "--concurrency=1", "--time-limit=600", "--soft-time-limit=540"]
    depends_on:
      - postgres-cache-{i}
      - redis-cache-{i}
    env_file: [envs/instance{i}.env]
    restart: always
    networks: [{network}]

  instance{i}:
    build:
      context: {augur_path}
      dockerfile: docker/Dockerfile
    ports:
      - "{http_port}:8080"
    env_file: [envs/instance{i}.env]
    depends_on:
      db-init-{i}:
        condition: service_completed_successfully
    restart: unless-stopped
    networks: [{network}]
"""

# Generate volumes and networks
def generate_volumes():
    return "\n".join([f"  augur{i}_db_data:" for i in range(1, instances + 1)])

def generate_networks():
    return "\n".join([f"  knot{i}:" for i in range(1, instances + 1)])

# Main logic
services = ""
for i in range(1, instances + 1):
    Path("envs").mkdir(exist_ok=True)
    Path(f"postgres/augur{i}").mkdir(parents=True, exist_ok=True)
    generate_env_file(i)
    Path(f"postgres/augur{i}/pg_hba.conf").write_text("host all all 0.0.0.0/0 md5\n")
    Path(f"postgres/augur{i}/postgresql.conf").write_text(postgres_conf_template)
    services += generate_service_block(i)

volumes = generate_volumes()
networks = generate_networks()

# Final output
Path("docker-compose.yml").write_text("# Auto-generated docker-compose.yml\n" + template.format(
    services=services,
    volumes=volumes,
    networks=networks
))

print("✅ docker-compose.yml generated successfully.")
