import os
import sys
from pathlib import Path

# --- Custom PostgreSQL configuration template ---
postgres_conf_template = """# Custom PostgreSQL configuration
listen_addresses = '*'
max_connections = 1000
shared_buffers = 10GB
work_mem = 3GB
maintenance_work_mem = 2GB
effective_cache_size = 1GB
max_wal_size = 1GB
min_wal_size = 1GB
wal_buffers = 64MB
"""
# --- End custom PostgreSQL configuration template ---

# Usage: python3 generate_compose.py /path/to/augur/clone
# Default context is current directory if not given.
instances = 8
augur_path = sys.argv[1] if len(sys.argv) > 1 else '.'

# Ensure envs directory exists
os.makedirs("envs", exist_ok=True)

template = """version: '3.8'

services:
{services}
volumes:
{volumes}
networks:
{networks}
"""

service_block = """
  augur{i}-db:
    image: postgres:17
    restart: unless-stopped
    environment:
      - POSTGRES_DB=augur
      - POSTGRES_USER=augur
      - POSTGRES_PASSWORD=augur
      - PGDATA=/var/lib/postgresql/data/pgdata
      - POSTGRES_INITDB_ARGS=--config-file=/etc/postgresql/postgresql.conf
    ports:
      - "{pg_port}:5432"
    volumes:
      - augur{i}-postgres:/var/lib/postgresql/data
      - ./postgres/augur{i}/postgresql.conf:/etc/postgresql/postgresql.conf
      - ./postgres/augur{i}/pg_hba.conf:/etc/postgresql/pg_hba.conf
    networks: [augur{i}]

  augur{i}-redis:
    image: redis:alpine
    networks: [augur{i}]

  augur{i}-keyman:
    image: augur-keyman
    build:
      context: {augur_path}
      dockerfile: docker/keyman/Dockerfile
    environment:
      - REDIS_CONN_STRING=redis://augur{i}-redis:6379
    depends_on:
      - augur{i}-redis
    networks: [augur{i}]
    user: 3456:3456

  augur{i}-rabbitmq:
    image: augur-rabbitmq
    build:
      context: {augur_path}
      dockerfile: docker/rabbitmq/Dockerfile
      args:
        - RABBIT_MQ_DEFAULT_USER=augur
        - RABBIT_MQ_DEFAULT_PASSWORD=password123
        - RABBIT_MQ_DEFAULT_VHOST=augur_vhost
    networks: [augur{i}]

  augur{i}:
    image: augur-new:latest
    build:
      context: {augur_path}
      dockerfile: docker/backend/${{AUGUR_TARGET:-Dockerfile}}
    restart: unless-stopped
    ports:
      - "{api_port}:5000"
    volumes:
      - augur{i}-cache:/cache:rw
      - augur{i}-config:/config:rw
      - augur{i}-facade:/facade:rw
      - augur{i}-logs:/logs:rw
    env_file:
      - ./envs/augur{i}.env
    environment:
      - AUGUR_DB=postgresql+psycopg2://augur:augur@augur{i}-db:5432/augur
      - AUGUR_DB_SCHEMA_BUILD=1
      - AUGUR_FACADE_REPO_DIRECTORY=/facade
      - REDIS_CONN_STRING=redis://augur{i}-redis:6379
      - RABBITMQ_CONN_STRING=amqp://augur:password123@augur{i}-rabbitmq:5672/augur_vhost
      - CONFIG_LOCATION=/config/config.yml
      - CACHE_DATADIR=/cache
      - CACHE_LOCKDIR=/cache
      - CELERYBEAT_SCHEDULE_DB=/tmp/celerybeat-schedule.db
    depends_on:
      - augur{i}-db
      - augur{i}-redis
      - augur{i}-keyman
      - augur{i}-rabbitmq
    networks: [augur{i}]
    user: 2345:2345
"""

placeholder_content = """# Environment variables for augur{index}
AUGUR_GITHUB_API_KEY={{your value here}}
AUGUR_GITLAB_API_KEY={{your value here}}
AUGUR_GITHUB_USERNAME={{your value here}}
AUGUR_GITLAB_USERNAME={{your value here}}
AUGUR_FLAGS={{your value here}}
"""

services, volumes, networks = "", "", ""
for i in range(1, instances + 1):
    services += service_block.format(i=i, pg_port=7000 + i, api_port=6000 + i, augur_path=augur_path)
    volumes += f"""  augur{i}-postgres:\n  augur{i}-cache:\n  augur{i}-config:\n  augur{i}-facade:\n  augur{i}-logs:\n"""
    networks += f"  augur{i}:\n"

    # Ensure postgres config dir exists and write config files
    pg_dir = Path("postgres") / f"augur{i}"
    pg_dir.mkdir(parents=True, exist_ok=True)

    with open(pg_dir / "postgresql.conf", "w") as f:
        f.write(postgres_conf_template)

    # Create pg_hba.conf with md5 auth
    pg_hba_path = pg_dir / "pg_hba.conf"
    if not pg_hba_path.exists():
        pg_hba_path.write_text(
            "host all all 0.0.0.0/0 md5\n"
            "host all all ::/0 md5\n"
        )

    # Prompt before overwriting env files
    env_file = os.path.join("envs", f"augur{i}.env")
    if os.path.exists(env_file):
        overwrite = input(f"envs/augur{i}.env already exists. Overwrite? [y/N]: ").strip().lower()
        if overwrite != "y":
            print(f"  Skipping envs/augur{i}.env")
            continue

    with open(env_file, "w") as ef:
        ef.write(placeholder_content.format(index=i))
        print(f"  Created/updated envs/augur{i}.env")

with open("docker-compose.yml", "w") as f:
    f.write(template.format(services=services, volumes=volumes, networks=networks))

print(f"docker-compose.yml generated successfully with Augur path: {augur_path}")