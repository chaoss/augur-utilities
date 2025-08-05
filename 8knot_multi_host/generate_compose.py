import os
import sys
from pathlib import Path

# --- Custom PostgreSQL configuration template ---
postgres_conf_template = """# Custom PostgreSQL configuration
listen_addresses = '*'
hba_file = '/etc/postgresql/pg_hba.conf'
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

instances = 8
labels = ["alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta"]

# --- Read CLI args ---
augur_path = sys.argv[1] if len(sys.argv) > 1 else '.'
force = '--force' in sys.argv

# --- Template for docker-compose.yml ---
template = """version: '3.8'

services:
{services}

volumes:
{volumes}

networks:
{networks}
"""

# --- Env generator ---
def generate_env_file(instance_id):
    env_path = Path(f"envs/instance{instance_id}.env")
    if env_path.exists() and not force:
        print(f"Skipping existing {env_path} (use --force to overwrite)")
        return

    env_content = f"""
POSTGRES_DB=augur
POSTGRES_USER=augur
POSTGRES_PASSWORD=augur
REDIS_PASSWORD=redispass{instance_id}
AUGUR_PORT={7000 + instance_id}
AUGUR_DATABASE=augur
AUGUR_USERNAME=augur
AUGUR_PASSWORD=augur
AUGUR_HOST=192.168.1.126
AUGUR_SCHEMA=augur_data
AUGUR_LOGIN_ENABLED=False

EDIS_USERS_HOST=redis-users-{i}
REDIS_USERS_PORT=6379
REDIS_USERS_PASSWORD=redispass4

REDIS_CACHE_HOST=redis-cache-{i}
REDIS_CACHE_PORT=6379
REDIS_CACHE_PASSWORD=redispass4

POSTGRES_CACHE=postgres-cache-{i}
"""
    env_path.write_text(env_content.strip())
    print(f"✅ Created/updated {env_path}")

# --- Service Block Generator ---
def generate_service_block(instance_id):
    port_offset = instance_id
    http_port = 8080 + port_offset
    redis_port = 6379
    label = labels[(instance_id - 1) % len(labels)]
    network = f"knot{instance_id}"

    redis_cmd = 'redis-server --requirepass "$$REDIS_PASSWORD"'

    block = f"""
  redis-cache-{instance_id}:
    image: docker.io/library/redis:6
    command:
      - /bin/sh
      - -c
      - '{redis_cmd}'
    env_file:
      - envs/instance{instance_id}.env
    restart: always
    networks:
      - {network}

  redis-users-{instance_id}:
    image: docker.io/library/redis:6
    command:
      - /bin/sh
      - -c
      - '{redis_cmd}'
    env_file:
      - envs/instance{instance_id}.env
    restart: always
    networks:
      - {network}

  postgres-cache-{instance_id}:
    image: docker.io/library/postgres:17
    restart: unless-stopped
    environment:
      - POSTGRES_DB=augur
      - POSTGRES_USER=augur
      - POSTGRES_PASSWORD=augur
      - PGDATA=/var/lib/postgresql/data/pgdata
    volumes:
      - augur{instance_id}_db_data:/var/lib/postgresql/data
      - ./postgres/augur{instance_id}/postgresql.conf:/etc/postgresql/postgresql.conf
      - ./postgres/augur{instance_id}/pg_hba.conf:/etc/postgresql/pg_hba.conf
    networks:
      - {network}

  instance{instance_id}:
    build:
      context: {augur_path}
      dockerfile: docker/Dockerfile
    ports:
      - "{http_port}:8080"
    env_file:
      - envs/instance{instance_id}.env
    depends_on:
      - postgres-cache-{instance_id}
      - redis-cache-{instance_id}
      - redis-users-{instance_id}
    restart: unless-stopped
    networks:
      - {network}
"""
    return block

# --- Volume Block Generator ---
def generate_volumes():
    return '\n'.join([f"  augur{i}_db_data:" for i in range(1, instances + 1)])

# --- Network Block Generator ---
def generate_networks():
    return '\n'.join([f"  knot{i}:" for i in range(1, instances + 1)])

# --- Main generator logic ---
services = ""
for i in range(1, instances + 1):
    generate_env_file(i)

    # --- Write pg_hba.conf ---
    pg_hba_path = Path(f"postgres/augur{i}/pg_hba.conf")
    pg_hba_path.parent.mkdir(parents=True, exist_ok=True)
    pg_hba_path.write_text("host all all 0.0.0.0/0 md5\n")

    # --- Write postgresql.conf ---
    postgresql_conf_path = Path(f"postgres/augur{i}/postgresql.conf")
    postgresql_conf_path.write_text("""listen_addresses = '*'
max_connections = 1000
shared_buffers = 1GB
work_mem = 64MB
maintenance_work_mem = 256MB
effective_cache_size = 2GB
wal_buffers = 64MB
max_wal_size = 1GB
min_wal_size = 80MB
hba_file = '/etc/postgresql/pg_hba.conf'
""")

    services += generate_service_block(i)

volumes = generate_volumes()
networks = generate_networks()
compose_content = template.format(services=services, volumes=volumes, networks=networks)

Path("docker-compose.yml").write_text("# Auto-generated docker-compose.yml\n" + compose_content)
print(f"✅ docker-compose.yml generated successfully with {instances} instance(s). Each uses its own network.")
