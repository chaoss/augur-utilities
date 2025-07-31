import sys
import os

INSTANCES = 8

# First CLI argument is the base directory
base_dir = sys.argv[1] if len(sys.argv) > 1 else '.'

# Ensure envs directory exists
os.makedirs("envs", exist_ok=True)

placeholder = """ # Environment for Augur instance {i}
AUGUR_DATABASE=augur
AUGUR_HOST=192.168.1.126
AUGUR_PASSWORD=augur
AUGUR_PORT={{DATABASE PORT HERE}}
AUGUR_SCHEMA=augur_data
AUGUR_USERNAME=augur
DEBUG_8KNOT=False
REDIS_PASSWORD=1234
DEFAULT_SEARCHBAR_LABEL=neurodesk
POSTGRES_PASSWORD=somepassword
AUGUR_LOGIN_ENABLED=False
# Secret key used for cryptographic session cookie signing.
# only needed if AUGUR_LOGIN_ENABLED=True
#SECRET_KEY=somethingsecret
"""

template_header = "# Auto-generated multi-instance 8Knot compose\n# Use with `podman compose up -d`\n"
compose = [template_header, "services:"]

# Generate services
for i in range(1, INSTANCES + 1):
    port = 8090 + i
    compose.append(f"""
  instance{i}:
    build:
      context: {base_dir}
      dockerfile: docker/Dockerfile
    env_file:
      - ./envs/instance{i}.env
    ports:
      - "{port}:8080"
    restart: unless-stopped
    networks:
      - knot{i}
""")

# Networks section
compose.append("networks:")
for i in range(1, INSTANCES + 1):
    compose.append(f"  knot{i}:")

# Write docker-compose.yml
with open("docker-compose.yml", "w") as f:
    f.write("\n".join(compose))
""" 
# Create env files
for i in range(1, INSTANCES + 1):
    env_file = f"envs/instance{i}.env"
    if os.path.exists(env_file):
        ans = input(f"{env_file} exists. Overwrite? [y/N]: ").strip().lower()
        if ans != "y":
            print(f"  Skipped {env_file}")
            continue
    with open(env_file, "w") as ef:
        ef.write(placeholder.format(i=i))
        print(f"  Created/updated {env_file}")

print("docker-compose.yml generated successfully.") """

from pathlib import Path

# Load labels from labels.txt
labels_file = Path("labels.txt")
if labels_file.exists():
    with open(labels_file, "r") as lf:
        labels = [line.strip() for line in lf if line.strip()]
else:
    print("labels.txt not found. Using default labels.")
    labels = ["default"]

# ... rest of your script ...

# Inside the loop where you generate env files:
for i in range(1, INSTANCES + 1):
    env_path = Path("envs") / f"instance{i}.env"

    # Select label, cycling if there are fewer labels than instances
    label = labels[(i - 1) % len(labels)]

    content = f"""# Environment for 8Knot instance {i}
AUGUR_DATABASE=augur
AUGUR_HOST=192.168.1.126
AUGUR_PASSWORD=augur 
AUGUR_PORT={7000+i}
AUGUR_SCHEMA=augur_data
AUGUR_USERNAME=augur
DEBUG_8KNOT=False
REDIS_PASSWORD=1234
DEFAULT_SEARCHBAR_LABEL={label}
POSTGRES_PASSWORD=somepassword
AUGUR_LOGIN_ENABLED=False
# Secret key used for cryptographic session cookie signing.
# only needed if AUGUR_LOGIN_ENABLED=True
#SECRET_KEY=somethingsecret
"""

    if env_path.exists():
        overwrite = input(f"{env_path} exists. Overwrite? [y/N]: ").strip().lower()
        if overwrite != "y":
            print(f"Skipping {env_path}")
            continue

    with open(env_path, "w") as ef:
        ef.write(content)
