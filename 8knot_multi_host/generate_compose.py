# generate_compose.py

import os
import sys
from pathlib import Path

# --- Constants and Inputs ---
INSTANCES = 8
base_dir = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "."
force = "--force" in sys.argv

os.makedirs("envs", exist_ok=True)

# --- Load secret password from .secrets.env ---
secrets_path = Path(".secrets.env")
if secrets_path.exists():
    with open(secrets_path) as sf:
        for line in sf:
            if line.startswith("AUGUR_PASSWORD="):
                augur_password = line.strip().split("=", 1)[1]
                break
    else:
        augur_password = "augur"
else:
    print("⚠️  .secrets.env not found. Using default 'augur' password.")
    augur_password = "augur"

# --- Load Labels ---
labels_file = Path("labels.txt")
if labels_file.exists():
    with open(labels_file, "r") as lf:
        labels = [line.strip() for line in lf if line.strip()]
else:
    print("labels.txt not found. Using default label.")
    labels = ["default"]

# --- Compose Template ---
compose_template = """version: '3.8'

services:
{services}

networks:
{networks}

volumes:
  postgres-cache:
"""

# --- Service Block Generator ---
def generate_service_block(instance_id):
    port_offset = instance_id
    http_port = 8080 + port_offset
    redis_port = 6379
    label = labels[(instance_id - 1) % len(labels)]
    network = f"knot{instance_id}"

    return f"""
  db-init-{instance_id}:
    build:
      context: {base_dir}
      dockerfile: ./docker/Dockerfile
    command: ["python3", "./cache_manager/db_init.py"]
    depends_on:
      postgres-cache-{instance_id}:
        condition: service_healthy
    env_file:
      - envs/instance{instance_id}.env
    restart: on-failure:1000
    networks:
      - {network}

  reverse-proxy-{instance_id}:
    image: nginx:latest
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - app-server-{instance_id}
    ports:
      - \"{http_port}:{http_port}\"
    networks:
      - {network}

  app-server-{instance_id}:
    build:
      context: {base_dir}
      dockerfile: ./docker/Dockerfile
    command:
      ["gunicorn", "--reload", "--bind", ":{http_port}", "app:server", "--workers", "1", "--threads", "2", "--timeout", "300", "--keep-alive", "5"]
    depends_on:
      - worker-callback-{instance_id}
      - worker-query-{instance_id}
      - redis-cache-{instance_id}
      - redis-users-{instance_id}
      - postgres-cache-{instance_id}
      - db-init-{instance_id}
    env_file:
      - envs/instance{instance_id}.env
    environment:
      - EIGHTKNOT_SEARCHBAR_OPTS_SORT=shortest
      - EIGHTKNOT_SEARCHBAR_OPTS_MAX_RESULTS=5500
      - EIGHTKNOT_SEARCHBAR_OPTS_MAX_REPOS=5000
    restart: always
    networks:
      - {network}

  worker-callback-{instance_id}:
    build:
      context: {base_dir}
      dockerfile: ./docker/Dockerfile
    command: ["celery", "-A", "app:celery_app", "worker", "--loglevel=INFO", "--concurrency=1", "--time-limit=300", "--soft-time-limit=240"]
    depends_on:
      - redis-cache-{instance_id}
      - redis-users-{instance_id}
      - postgres-cache-{instance_id}
    env_file:
      - envs/instance{instance_id}.env
    restart: always
    networks:
      - {network}

  worker-query-{instance_id}:
    build:
      context: {base_dir}
      dockerfile: ./docker/Dockerfile
    command: ["celery", "-A", "app:celery_app", "worker", "--loglevel=INFO", "-Q", "data", "--concurrency=1", "--time-limit=600", "--soft-time-limit=540"]
    depends_on:
      - redis-cache-{instance_id}
      - postgres-cache-{instance_id}
    env_file:
      - envs/instance{instance_id}.env
    restart: always
    networks:
      - {network}

  redis-cache-{instance_id}:
    image: docker.io/library/redis:6
    command: ["/bin/sh", "-c", "redis-server --requirepass \"$$REDIS_PASSWORD\""]
    env_file:
      - envs/instance{instance_id}.env
    restart: always
    networks:
      - {network}

  redis-users-{instance_id}:
    image: docker.io/library/redis:6
    command: ["/bin/sh", "-c", "redis-server --requirepass \"$$REDIS_PASSWORD\""]
    env_file:
      - envs/instance{instance_id}.env
    restart: always
    networks:
      - {network}

  postgres-cache-{instance_id}:
    image: docker.io/library/postgres:16
    command: ["postgres", "-c", "config_file=/etc/postgresql/postgresql.conf"]
    volumes:
      - ./postgres.conf:/etc/postgresql/postgresql.conf:ro
      - postgres-cache:/var/lib/postgresql/data
    env_file:
      - envs/instance{instance_id}.env
    restart: always
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5
    networks:
      - {network}
"""

# --- Env File Writer ---
def generate_env_file(instance_id):
    env_path = Path("envs") / f"instance{instance_id}.env"
    label = labels[(instance_id - 1) % len(labels)]

    content = f"""# Environment for 8Knot instance {instance_id}
AUGUR_DATABASE=augur
AUGUR_HOST=192.168.1.126
AUGUR_PASSWORD=augur
AUGUR_PORT={7000 + instance_id}
AUGUR_SCHEMA=augur_data
AUGUR_USERNAME=augur
DEBUG_8KNOT=False
REDIS_HOST=redis-cache-{instance_id}
REDIS_PORT=6379
REDIS_PASSWORD=1234
DEFAULT_SEARCHBAR_LABEL={label}
POSTGRES_PASSWORD=somepassword
AUGUR_LOGIN_ENABLED=False
"""
    if env_path.exists() and not force:
        print(f"Skipping existing {env_path} (use --force to overwrite)")
        return

    with open(env_path, "w") as f:
        f.write(content)
    print(f"✅ Created/updated {env_path}")

# --- Main Compose Build ---
services = ""
networks = ""
for i in range(1, INSTANCES + 1):
    generate_env_file(i)
    services += generate_service_block(i)
    networks += f"  knot{i}:\n"

with open("docker-compose.yml", "w") as f:
    f.write(compose_template.format(services=services, networks=networks))

print(f"✅ docker-compose.yml generated successfully with {INSTANCES} instance(s). Each uses its own network.")
