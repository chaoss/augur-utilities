#!/usr/bin/env python3
"""
Docker Compose Generator for Multiple 8knot Instances
Generates a docker-compose.yml file with multiple isolated instances of the 8knot application
"""

import yaml
from typing import Dict, Any

def generate_env_file(instance_num: int, base_augur_port: int = 7000) -> str:
    """Generate instance-specific environment file content"""
    augur_port = base_augur_port + instance_num
    redis_pass_base = f"redispass{instance_num}"
    redis_pass_users = f"redispass{instance_num + 1}"
    
    env_content = f"""POSTGRES_PASSWORD=password
REDIS_PASSWORD={redis_pass_base}
AUGUR_PORT={augur_port}
AUGUR_DATABASE=augur
AUGUR_USERNAME=augur
AUGUR_PASSWORD=augur
AUGUR_HOST=192.168.1.126
AUGUR_SCHEMA=augur_data
AUGUR_LOGIN_ENABLED=False
DEFAULT_SEARCHBAR_LABEL=neurodesk
REDIS_USERS_HOST=redis-users-{instance_num}
REDIS_USERS_PORT=6379
REDIS_USERS_PASSWORD={redis_pass_users}
REDIS_CACHE_HOST=redis-cache-{instance_num}
REDIS_CACHE_PORT=6379
REDIS_CACHE_PASSWORD={redis_pass_users}
"""
    return env_content

def generate_compose_file(num_instances: int = 8, base_port: int = 8091, base_augur_port: int = 7000, output_file: str = "docker-compose-multi.yml"):
    """Generate complete docker-compose.yml file with multiple instances and their env files"""
    
    # Start with the basic structure
    compose_content = """version: '3.8'

services:
"""
    
    # Generate each instance
    for i in range(1, num_instances + 1):
        port = base_port + i - 1
        suffix = f"_{i}"
        env_file = f"instance{i}.env"
        
        # Generate environment file for this instance
        env_content = generate_env_file(i, base_augur_port)
        with open(env_file, 'w') as f:
            f.write(env_content)
        print(f"Generated {env_file}")
        
        # Add services for this instance
        compose_content += f"""
  db-init{suffix}:
    build:
      context: .
      dockerfile: ./docker/Dockerfile
    command: ["python3", "./cache_manager/db_init.py"]
    depends_on:
      postgres-cache{suffix}:
        condition: service_healthy
    env_file:
      - {env_file}
    restart: on-failure:1000

  reverse-proxy{suffix}:
    image: nginx:latest
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - app-server{suffix}
    ports:
      - "{port}:{port}"

  app-server{suffix}:
    build:
      context: .
      dockerfile: ./docker/Dockerfile
    command:
      [
        "gunicorn",
        "--reload",
        "--bind",
        ":{port}",
        "app:server",
        "--workers",
        "1",
        "--threads",
        "2",
        "--timeout",
        "300",
        "--keep-alive",
        "5"
      ]
    depends_on:
      - worker-callback{suffix}
      - worker-query{suffix}
      - redis-cache{suffix}
      - redis-users{suffix}
      - postgres-cache{suffix}
      - db-init{suffix}
    env_file:
      - {env_file}
    environment:
      - EIGHTKNOT_SEARCHBAR_OPTS_SORT=shortest
      - EIGHTKNOT_SEARCHBAR_OPTS_MAX_RESULTS=5500
      - EIGHTKNOT_SEARCHBAR_OPTS_MAX_REPOS=5000
    restart: always

  worker-callback{suffix}:
    build:
      context: .
      dockerfile: ./docker/Dockerfile
    command: ["celery", "-A", "app:celery_app", "worker", "--loglevel=INFO", "--concurrency=1", "--time-limit=300", "--soft-time-limit=240"]
    depends_on:
      - redis-cache{suffix}
      - redis-users{suffix}
      - postgres-cache{suffix}
    env_file:
      - {env_file}
    restart: always

  worker-query{suffix}:
    build:
      context: .
      dockerfile: ./docker/Dockerfile
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
      - redis-cache{suffix}
      - postgres-cache{suffix}
    env_file:
      - {env_file}
    restart: always

  redis-cache{suffix}:
    image: docker.io/library/redis:6
    command:
      - /bin/sh
      - -c
      - redis-server --requirepass "$$${{REDIS_PASSWORD:?REDIS_PASSWORD variable is not set}}"
    env_file:
      - {env_file}
    restart: always

  redis-users{suffix}:
    image: docker.io/library/redis:6
    command:
      - /bin/sh
      - -c
      - redis-server --requirepass "$$${{REDIS_PASSWORD:?REDIS_PASSWORD variable is not set}}"
    env_file:
      - {env_file}
    restart: always

  postgres-cache{suffix}:
    image: docker.io/library/postgres:16
    command: ["postgres", "-c", "config_file=/etc/postgresql/postgresql.conf"]
    volumes:
      - /Users/sean/github/oss-aspen/8knot/postgres.conf:/etc/postgresql/postgresql.conf:Z
    env_file:
      - {env_file}
    restart: always
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5
"""
    
    # Add volumes section
    compose_content += "\nvolumes:\n"
    for i in range(1, num_instances + 1):
        compose_content += f"  postgres-cache_{i}:\n"
    
    # Write the file
    with open(output_file, 'w') as f:
        f.write(compose_content)
    
    print(f"Generated {output_file} with {num_instances} instances on ports {base_port}-{base_port + num_instances - 1}")

def main():
    """Main function with CLI options"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate multi-instance docker-compose.yml for 8knot")
    parser.add_argument("--instances", "-n", type=int, default=8, help="Number of instances (default: 8)")
    parser.add_argument("--start-port", "-p", type=int, default=8091, help="Starting port (default: 8091)")
    parser.add_argument("--augur-port", "-a", type=int, default=7000, help="Starting Augur port (default: 7000)")
    parser.add_argument("--output", "-o", type=str, default="docker-compose-multi.yml", help="Output file (default: docker-compose-multi.yml)")
    
    args = parser.parse_args()
    
    generate_compose_file(args.instances, args.start_port, args.augur_port, args.output)
    
    print(f"\nTo run all instances:")
    print(f"podman-compose -f {args.output} up -d")
    print(f"\nTo stop all instances:")
    print(f"podman-compose -f {args.output} down")
    print(f"\nInstances will be available on:")
    for i in range(args.instances):
        print(f"  http://localhost:{args.start_port + i}")

if __name__ == "__main__":
    main()
