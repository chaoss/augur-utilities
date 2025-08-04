# Operating Your Multi-Container Setup Once Deployed: 
**NOTE**: For information about interacting with the containers once they are started, including Augur and the databases, see [RUNNING.md](./RUNNING.md)

There is a refined version of many of these instructions at (HERE)[./augur_deploy_cheatsheet.md]

This is the [make helpfile.](./MAKEFILE_HELP.md)

We have some notes about [troubleshooting pods that don't seem to be working here.](./troubleshooting-pods.md)

# Multi-Instance Augur Deployment (8 instances)

This setup runs 8 fully isolated Augur instances using Podman and Nginx with automatic Let's Encrypt certificates.

You may need to create a "pro" account on docker hub to run 8 instances, as a non-pro account limits your downloads per six hour period, and if you stop and start several times you quickly exceed that limits since there is a pull for each container for each instance. Logging in doubles your allowed downloads from 100 to 200. At the command line with Podman: 
```bash
podman login docker.io 
podman login docker.com 
``` 

Note that podman may delegate the login to docker-compose on build, so you may need to install `podman-compose`. On OSX, for example, this works: 
```bash
brew install podman-compose
```

You can make this easier by ensuring the `Makefile` in this system specified `podman-compose` at the top:
```bash
COMPOSE = podman-compose
```

## Steps for Public Deployment

1. **Install prerequisites**
   ```bash
   sudo apt update
   sudo apt install nginx certbot python3-certbot-nginx podman-compose
   ```

2. **Clone or copy this project**
   ```bash
   cd ~/augur-multi
   ```

3. **Configure DNS**
   Point:
   ```
   augur1.domain.com -> your server IP
   ...
   augur8.domain.com -> your server IP
   ```

4. **Generate configs**

   Cleaning up Podman: 

   ```bash
      podman system prune -af
      podman volume prune
   ```

   ```bash
   make regen
   make nginx
   ```

   Initial Build: 

   ```bash
   make regen    # always regenerate compose + config first
   make build    # only needed if base image or Dockerfile changed
   make up       # starts all services
   ```

   Subsequent Starts: 

   ```bash
   make regen
   make up 
   ```

   There are parameters available for specifying the location of your Augur clone as well. This will allow you to use this code as an "orchestration directory" that pulls in code from Augur. 
   ```bash
   make regen AUGUR_PATH=/Users/sean/github/wellcome-prod/augur-1 
   ```

   Similarly for nginx, you can specify the domain using these parameters: 
   ```bash
   make nginx DOMAIN=superfascismh8r.ai
   ```

   For example. 

5. **Deploy services**

   It is important to make sure you have sufficient disk space configured for your Podman machine for running 8 augur instances. Try this first: 
   ```bash
   podman machine stop
   podman machine rm
   podman machine init --disk-size 3072 --memory 100000
   podman machine start
   ```

   This configuration requires 100GB of RAM minimum. You can reconfigure for less, depending on limits of your hardware. ls -

   ```bash
   make up
   sudo cp nginx.conf /etc/nginx/sites-available/augur.conf
   sudo ln -s /etc/nginx/sites-available/augur.conf /etc/nginx/sites-enabled/
   sudo nginx -s reload
   ```

6. **Get certificates**
   ```bash
   make certbot
   ```

7. **Access instances**
   - https://augur1.sociallycompute.com
   - …
   - https://augur8.sociallycompute.com

8. **Stop services**
   ```bash
   make down
   ```

Certbot will automatically handle HTTPS redirection and renewal.


# These are localhost port mappings for an 8 instance setup: 

# Augur Multi-Instance Port Mappings (localhost)

## API (backend) ports
   - augur1: http://localhost:6001
   - augur2: http://localhost:6002
   - augur3: http://localhost:6003
   - augur4: http://localhost:6004
   - augur5: http://localhost:6005
   - augur6: http://localhost:6006
   - augur7: http://localhost:6007
   - augur8: http://localhost:6008

## PostgreSQL ports
   - augur1-db: localhost:7001
   - augur2-db: localhost:7002
   - augur3-db: localhost:7003
   - augur4-db: localhost:7004
   - augur5-db: localhost:7005
   - augur6-db: localhost:7006
   - augur7-db: localhost:7007
   - augur8-db: localhost:7008

## Other services
Redis, RabbitMQ, and Keyman services are only accessible on the internal Docker/Podman network.
They are not mapped to host ports for security.