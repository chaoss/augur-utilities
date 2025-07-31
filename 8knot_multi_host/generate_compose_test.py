import sys
import os
from pathlib import Path

INSTANCES = 8
base_dir = sys.argv[1] if len(sys.argv) > 1 else '.'

# Ensure envs directory exists
os.makedirs("envs", exist_ok=True)

# Load labels (optional)
labels_file = Path("labels.txt")
if labels_file.exists():
    with open(labels_file, "r") as lf:
        labels = [line.strip() for line in lf if line.strip()]
else:
    print("labels.txt not found. Using default labels.")
    labels = ["default"]

template_header = "# Auto-generated 8Knot multi-instance docker-compose\n"
compose_lines = [template_header, "services:"]

# Generate services for each instance
for i in range(1, INSTANCES + 1):
    http_port = 8090 + i
    pg_port = 5450 + i
    label = labels[(i - 1) % len(labels)]
    env_file = f"./envs/instance{i}.env"

    # db-init
    compose_lines.append(f"""
  db-init-{i}:
    build:
      context: {base_dir}
      dockerfile: docker/Dockerfile
    command: ["python3", "./cache_manager/db_init.py"]
    depends_on:
      postgres-cache-{i}:
        condition: service_healthy
    env_file:
      - {env_file}
    restart: on-failure:1000
""")

    # app-server
    compose_lines.append(f"""
  app-server-{i}:
    build:
      context: {base_dir}
      dockerfile: docker/Dockerfile
    command:
      [
        "gunicorn",
        "--bind",
        ":8080",
        "app:server",
        "--workers",
        "8",
        "--threads",
        "16",
        "--timeout",
        "300",
        "--keep-alive",
        "120"
      ]
    ports:
      - "{http_port}:8080"
    depends_on:
      - db-init-{i}
      - redis-users-{i}
      - redis-cache-{i}
    env_file:
      - {env_file}
    environment:
      - EIGHTKNOT_SEARCHBAR_OPTS_SORT=shortest
      - EIGHTKNOT_SEARCHBAR_OPTS_MAX_RESULTS=5500
      - EIGHTKNOT_SEARCHBAR_OPTS_MAX_REPOS=5000
    restart: always
""")

    # worker-callback
    compose_lines.append(f"""
  worker-callback-{i}:
    build:
      context: {base_dir}
      dockerfile: docker/Dockerfile
    command:
      [
        "celery",
        "-A",
        "app:celery_app",
        "worker",
        "--loglevel=INFO",
        "--concurrency=1",
        "--time-limit=300",
        "--soft-time-limit=240"
      ]
    depends_on:
      - redis-cache-{i}
      - redis-users-{i}
      - postgres-cache-{i}
    env_file:
      - {env_file}
    restart: always
""")

    # worker-query
    compose_lines.append(f"""
  worker-query-{i}:
    build:
      context: {base_dir}
      dockerfile: docker/Dockerfile
    command:
      [
        "celery",
        "-A",
        "app:celery_app",
        "worker",
        "--loglevel=INFO",
        "-Q",
        "data",
        "--concurrency=1",
        "--time-limit=600",
        "--soft-time-limit=540"
      ]
    depends_on:
      - redis-cache-{i}
      - postgres-cache-{i}
    env_file:
      - {env_file}
    restart: always
""")

    # redis-cache
    compose_lines.append(f"""
  redis-cache-{i}:
    image: docker.io/library/redis:6
    command:
      - /bin/sh
      - -c
      - redis-server --requirepass "$${{REDIS_PASSWORD:?REDIS_PASSWORD variable is not set}}"
    env_file:
      - {env_file}
    restart: always
""")

    # redis-users
    compose_lines.append(f"""
  redis-users-{i}:
    image: docker.io/library/redis:6
    command:
      - /bin/sh
      - -c
      - redis-server --requirepass "$${{REDIS_PASSWORD:?REDIS_PASSWORD variable is not set}}"
    env_file:
      - {env_file}
    restart: always
""")

    # postgres-cache
    compose_lines.append(f"""
  postgres-cache-{i}:
    image: docker.io/library/postgres:16
    command: ["postgres", "-c", "config_file=/etc/postgresql/postgresql.conf"]
    volumes:
      - ./postgres.conf:/etc/postgresql/postgresql.conf:ro
    ports:
      - "{pg_port}:5432"
    env_file:
      - {env_file}
    restart: always
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5
""")

# Networks section
compose_lines.append("networks:")
for i in range(1, INSTANCES + 1):
    compose_lines.append(f"  knot{i}:")

# Shared network
#compose_lines.append("""
#networks:
#  default:
#    external: true
#    name: 8knet

#volumes:
#  postgres-cache:
#""")

# Write docker-compose.yml
with open("docker-compose.yml", "w") as f:
    f.write("\n".join(compose_lines))

# Generate env files
for i in range(1, INSTANCES + 1):
    env_path = Path("envs") / f"instance{i}.env"
    label = labels[(i - 1) % len(labels)]
    augur_port = 7000 + i  # fixed to start at 7001
    content = f"""# Environment for 8Knot instance {i}
AUGUR_DATABASE=augur
AUGUR_HOST=192.168.1.126
AUGUR_PASSWORD=augur
AUGUR_PORT={augur_port}
AUGUR_SCHEMA=augur_data
AUGUR_USERNAME=augur
DEBUG_8KNOT=False
REDIS_PASSWORD=1234
DEFAULT_SEARCHBAR_LABEL={label}
POSTGRES_PASSWORD=somepassword
AUGUR_LOGIN_ENABLED=False
"""

    if env_path.exists():
        ans = input(f"{env_path} exists. Overwrite? [y/N]: ").strip().lower()
        if ans != "y":
            print(f"Skipped {env_path}")
            continue

    with open(env_path, "w") as ef:
        ef.write(content)
        print(f"Created/updated {env_path}")

print("docker-compose.yml generated successfully.")
