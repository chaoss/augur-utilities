# Multi-instance 8Knot with Podman

This setup runs 8 instances of 8Knot on ports 8091–8098.

## 1. Install Podman and podman-compose

```bash
sudo apt update
sudo apt install -y podman python3-pip
pip3 install --user podman-compose
echo 'export PATH=$HOME/.local/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
```

## 2. Generate configuration

```bash
python3 generate_compose.py /home/sean/github/8knot
```

This creates `docker-compose.yml` and env files in `envs/`.

## 3. Run instances

```bash
make build
make up
```

## 4. Run only one instance

```bash
make up-one INSTANCE=3
```

Instances will be available on:
- http://localhost:8091
- ...
- http://localhost:8098

## 4. Logs and shell

```bash
make logs INSTANCE=2
make shell INSTANCE=3
```

## 5. Generate nginx.conf

```bash
python3 generate_nginx.py yourdomain.com
```

Copy to `/etc/nginx/sites-enabled/8knot.conf`, reload nginx, and run:

```bash
sudo certbot --nginx
```
