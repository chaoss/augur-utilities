import sys
from pathlib import Path

INSTANCES = 8
domain = sys.argv[1] if len(sys.argv) > 1 else "example.com"

# Read labels.txt if it exists
labels_file = Path("labels.txt")
if labels_file.exists():
    with open(labels_file) as lf:
        labels = [line.strip() for line in lf if line.strip()]
else:
    labels = []

nginx_conf = []
for i in range(1, INSTANCES + 1):
    port = 8090 + i
    # Use label if available, otherwise fallback
    label = labels[i - 1] if i - 1 < len(labels) else f"instance{i}"

    server = f"""
server {{
    listen 80;
    server_name {label}.{domain};

    location / {{
        proxy_pass http://127.0.0.1:{port};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
}}
"""
    nginx_conf.append(server)

with open("nginx.conf", "w") as f:
    f.write("\n".join(nginx_conf))

print(f"nginx.conf created for {INSTANCES} instances at domain {domain}")
