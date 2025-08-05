import sys
from pathlib import Path

INSTANCES = 8
domain = sys.argv[1] if len(sys.argv) > 1 else "example.com"

labels_path = Path("labels.txt")
if not labels_path.exists():
    raise FileNotFoundError("❌ labels.txt file not found!")

labels = labels_path.read_text().splitlines()
if len(labels) < INSTANCES:
    raise ValueError("❌ Not enough labels in labels.txt for all instances!")

nginx_conf = []
for i in range(1, INSTANCES + 1):
    label = labels[i - 1].lower().replace(" ", "")
    port = 8090 + i
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

Path("nginx.conf").write_text("\n".join(nginx_conf))
print(f"✅ nginx.conf created with {INSTANCES} subdomains from labels.txt for domain {domain}")
