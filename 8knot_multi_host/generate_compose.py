import os
import sys
from pathlib import Path

# --- Config ---
instances = 8
#future 
#instances = len(get_labels())  # instead of fixed 8
augur_path = sys.argv[1] if len(sys.argv) > 1 else "."
force = "--force" in sys.argv

template = """version: '3.8'

services:
{services}

volumes:
{volumes}

networks:
{networks}
"""

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

def get_labels():
    label_file = Path("labels.txt")
    if not label_file.exists():
        raise FileNotFoundError("❌ labels.txt not found.")
    labels = [line.strip() for line in label_file.read_text().splitlines() if line.strip()]
    if len(labels) < instances:
        raise ValueError(f"❌ Only {len(labels)} labels found; {instances} required.")
    return labels

labels = get_labels()

def generate_env_file(i):
    env_path.write_text(content.strip() + "\n") 
    if env_path.exists() and not force:
        print(f"Skipping {env_path}")
        return

    label = labels[i - 1]

    content = f"""POSTGRES_PASSWORD=password
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
    env_path.write_text(content.strip())
    print(f"✅ Wrote {env_path} with label {label}")

def generate_service_block(i):
    port = 8080 + i
    network = f"knot{i}"
    redis_cmd = 'redis-server --requirepass "$$REDIS_PASSWORD"'

    return f"""
  redis-cache-{i}:
    image: docker.io/library/redis:6
    command:
      - /bin/sh
      - -c
      - {redis_cmd}
    env_file:
      - envs/instance{i}.env
    restart: always
    networks:
      {network}:
        aliases:
          - redis-cache-{i}
          - redis-cache

  redis-users-{i}:
    image: docker.io/library/redis:6
    command:
      - /bin/sh
      - -c
      - {redis_cmd}
    env_file:
      - envs/instance{i}.env
    restart: always
    networks:
      {network}:
        aliases:
          - redis-users-{i}
          - redis-users

  postgres-cache-{i}:
    image: docker.io/library/postgres:16
    command:
      - postgres
      - -c
      - config_file=/etc/postgresql/postgresql.conf
    restart: unless-stopped
    environment:
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
    networks:
      {network}:
        aliases:
          - postgres-cache-{i}
          - postgres-cache

  db-init-{i}:
    build:
      context: {augur_path}
      dockerfile: docker/Dockerfile
    command:
      - python3
      - ./cache_manager/db_init.py
    depends_on:
      postgres-cache-{i}:
        condition: service_healthy
    env_file:
      - envs/instance{i}.env
    restart: on-failure:1000
    networks:
      {network}:
        aliases:
          - db-init-{i}
          - db-init

  worker-callback-{i}:
    build:
      context: {augur_path}
      dockerfile: docker/Dockerfile
    command:
      - celery
      - -A
      - app:celery_app
      - worker
      - --loglevel=INFO
      - --concurrency=1
      - --time-limit=300
      - --soft-time-limit=240
    depends_on:
      - postgres-cache-{i}
      - redis-cache-{i}
      - redis-users-{i}
    env_file:
      - envs/instance{i}.env
    restart: always
    networks:
      {network}:
        aliases:
          - worker-callback-{i}
          - worker-callback

  worker-query-{i}:
    build:
      context: {augur_path}
      dockerfile: docker/Dockerfile
    command:
      - celery
      - -A
      - app:celery_app
      - worker
      - --loglevel=INFO
      - -Q
      - data
      - --concurrency=1
      - --time-limit=600
      - --soft-time-limit=540
    depends_on:
      - postgres-cache-{i}
      - redis-cache-{i}
    env_file:
      - envs/instance{i}.env
    restart: always
    networks:
      {network}:
        aliases:
          - worker-query-{i}
          - worker-query

  instance{i}:
    build:
      context: {augur_path}
      dockerfile: docker/Dockerfile
    command:
      - gunicorn
      - --reload
      - --bind
      - :8080
      - app:server
      - --workers
      - "1"
      - --threads
      - "2"
      - --timeout
      - "300"
      - --keep-alive
      - "5"
    ports:
      - "{port}:8080"
    env_file:
      - envs/instance{i}.env
    environment:
      - EIGHTKNOT_SEARCHBAR_OPTS_SORT=shortest
      - EIGHTKNOT_SEARCHBAR_OPTS_MAX_RESULTS=5500
      - EIGHTKNOT_SEARCHBAR_OPTS_MAX_REPOS=5000
    depends_on:
      worker-callback-{i}:
        condition: service_started
      worker-query-{i}:
        condition: service_started
      redis-cache-{i}:
        condition: service_started
      redis-users-{i}:
        condition: service_started
      postgres-cache-{i}:
        condition: service_healthy
      db-init-{i}:
        condition: service_completed_successfully
    restart: unless-stopped
    networks:
      {network}:
        aliases:
          - instance{i}
          - instance
"""

def generate_volumes():
    return "\n".join([f"  augur{i}_db_data:" for i in range(1, instances + 1)])

def generate_networks():
    return "\n".join([f"  knot{i}:" for i in range(1, instances + 1)])

# --- Main Execution ---
services = ""
for i in range(1, instances + 1):
    Path("envs").mkdir(exist_ok=True)
    Path(f"postgres/augur{i}").mkdir(parents=True, exist_ok=True)
    generate_env_file(i)
    Path(f"postgres/augur{i}/pg_hba.conf").write_text("host all all 0.0.0.0/0 md5\n")
    Path(f"postgres/augur{i}/postgresql.conf").write_text(postgres_conf_template)
    services += generate_service_block(i)

Path("docker-compose.yml").write_text("# Auto-generated docker-compose.yml\n" + template.format(
    services=services,
    volumes=generate_volumes(),
    networks=generate_networks()
))

print(f"✅ docker-compose.yml generated successfully for {instances} instances.")
