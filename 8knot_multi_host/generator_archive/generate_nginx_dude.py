for i in range(1, 9):
    conf = f"""
user  nginx;
events {{
    worker_connections   1000;
}}
http {{
    server {{
        listen 809{i};
        access_log  /dev/null;
        location / {{
            proxy_pass http://app-server_{i}:809{i};
            proxy_read_timeout 600s;
        }}
    }}
}}
"""
    with open(f"nginx_{i}.conf", "w") as f:
        f.write(conf.strip() + "\n")
