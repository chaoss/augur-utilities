# --- Global variables ---
COMPOSE = podman-compose
INSTANCES = 8
DOMAIN = sociallycompute.io
INSTANCE ?= 1
AUGUR_PATH ?=

ifndef AUGUR_PATH
$(error AUGUR_PATH is not set. Use 'make AUGUR_PATH=/your/path bootstrap' or export it)
endif

# --- HELP! ---

help:
help:
	@echo ""
	@echo "📦 Augur Multi-Instance Makefile — Usage Reference"
	@echo "--------------------------------------------------"
	@echo ""
	@echo "Core Deployment Commands:"
	@echo "  make regen               Regenerate PostgreSQL configs and docker-compose.yml"
	@echo "  make build               Build all service images using podman-compose"
	@echo "  make up                  Start all containers in detached mode"
	@echo "  make down                Stop and remove containers and orphaned networks"
	@echo "  make restart             Restart all running containers"
	@echo "  make all                 Alias for make up"
	@echo "  make bootstrap           Run full deploy: regen → build → up"
	@echo "  make bootstrap-restore   Full deploy + restore: regen → build → up → restore-all"
	@echo ""
	@echo "Snapshot & Restore:"
	@echo "  make snapshot            pg-only backup using pg_dumpall via snapshot_pg_volumes.sh"
	@echo "  make snapshot-db         Raw PostgreSQL volume archive to tar.gz"
	@echo "  make snapshot-all        Full backup of DB, Redis, and config via snapshot_all.sh"
	@echo "  make restore-db FILE=... Restore a single augurX DB from a snapshot"
	@echo ""
	@echo "Admin & Utilities:"
	@echo "  make ps                  List running containers"
	@echo "  make logs                Tail logs for augur\$$INSTANCE"
	@echo "  make shell               Shell into augur\$$INSTANCE container"
	@echo "  make status              Check for missing instance env files"
	@echo ""
	@echo "Teardown & Cleanup:"
	@echo "  make stop-all            Stop all running podman containers"
	@echo "  make clean               Remove containers/images/networks (preserves DB volumes)"
	@echo "  make nuke                Remove all instance containers and non-DB volumes"
	@echo "  make clean-networks      Remove augur-related podman networks"
	@echo ""
	@echo "SSL & Nginx Setup:"
	@echo "  make nginx               Generate Nginx reverse proxy config"
	@echo "  make certbot             Run Certbot to issue SSL certs for all instances"
	@echo ""


# --- Primary targets ---

all: up

bootstrap:
	@echo "Running full bootstrap: regen -> build -> up"
	$(MAKE) regen
	$(MAKE) build
	$(MAKE) up

regen:
	@echo "Regenerating PostgreSQL config files only..."
	@for i in 1 2 3 4 5 6 7 8; do \
		mkdir -p postgres/augur$$i; \
		echo "# Custom PostgreSQL configuration" > postgres/augur$$i/postgresql.conf; \
		echo "listen_addresses = '*'" >> postgres/augur$$i/postgresql.conf; \
		echo "max_connections = 1000" >> postgres/augur$$i/postgresql.conf; \
		echo "shared_buffers = 10GB" >> postgres/augur$$i/postgresql.conf; \
		echo "work_mem = 3GB" >> postgres/augur$$i/postgresql.conf; \
		echo "maintenance_work_mem = 2GB" >> postgres/augur$$i/postgresql.conf; \
		echo "effective_cache_size = 1GB" >> postgres/augur$$i/postgresql.conf; \
		echo "max_wal_size = 1GB" >> postgres/augur$$i/postgresql.conf; \
		echo "min_wal_size = 1GB" >> postgres/augur$$i/postgresql.conf; \
		echo "wal_buffers = 64MB" >> postgres/augur$$i/postgresql.conf; \
		echo "host all all 0.0.0.0/0 md5" > postgres/augur$$i/pg_hba.conf; \
		echo "host all all ::/0 md5" >> postgres/augur$$i/pg_hba.conf; \
	done
	@echo "Regenerating config files..."
	@echo "Rebuilding docker-compose.yml ..."
	python3 generate_compose.py $(AUGUR_PATH) $(if $(FORCE),--force)

#build:
#	$(COMPOSE) build

build:
	@echo "🔧 Building all services using podman-compose..."
	@exit_code=0; \
	$(COMPOSE) config --services | while read svc; do \
		echo "📦 Building service: $$svc"; \
	done; \
	$(COMPOSE) build || exit_code=$$?; \
	if [ $$exit_code -ne 0 ]; then \
		echo "⚠️  podman-compose build exited with code $$exit_code, but continuing"; \
	fi

up:
	$(COMPOSE) up -d

down:
	$(COMPOSE) down --remove-orphans

# Safe clean: removes containers/networks/images, but NOT DB volumes
clean: down nuke
	@echo "Cleaning up unused resources (excluding named DB volumes)..."
	@podman volume prune -f
	@podman image prune -f
	@podman network prune -f
	@echo "Clean complete."

restart:
	$(COMPOSE) restart

# --- Dev/admin tools ---

nginx:
	python3 generate_nginx.py $(DOMAIN)

certbot:
	sudo certbot --nginx $(shell seq -f "-d augur%g.$(DOMAIN)" 1 $(INSTANCES))

shell:
	$(COMPOSE) exec augur$(INSTANCE) /bin/bash

logs:
	$(COMPOSE) logs -f augur$(INSTANCE)

ps:
	$(COMPOSE) ps

status:
	@echo "Environment files for Augur instances:"
	@for i in $$(seq 1 $(INSTANCES)); do \
		f=envs/augur$$i.env; \
		if [ -f $$f ]; then \
			echo "  $$f (exists)"; \
		else \
			echo "  $$f (MISSING)"; \
		fi; \
	done

# --- Teardown/cleanup ---

stop-all:
	podman stop $$(podman ps -q)

clean-networks:
	-podman network ls --format "{{.Name}}" | grep augur_multi_host_augur | xargs -I {} podman network rm {}

nuke:
	-@echo "Removing instance containers..."
	-@podman ps -a --format "{{.ID}} {{.Names}}" | grep instance | awk '{print $$1}' | xargs -r podman rm -f
	-@echo "Removing instance volumes (excluding DB volumes)..."
	-@podman volume ls --format "{{.Name}}" | grep instance | grep -v postgres | xargs -r podman volume rm
	-@echo "Removing networks with 'knot' in their name..."
	-@podman network ls --format "{{.Name}}" | grep knot | xargs -r podman network rm

snapshot-all:
	@echo "📦 Running full instance + config + Redis snapshot..."
	@bash ./snapshot_all.sh

snapshot:
	@echo "🧠 Creating PostgreSQL volume snapshots using pg_dumpall..."
	@bash ./snapshot_pg_volumes.sh

# Snapshot raw PostgreSQL volume data safely to tar.gz (optional alternative to pg_dumpall)
snapshot-db:
	@echo "📸 Snapshotting raw PostgreSQL volume data..."
	@mkdir -p db_snapshots
	@for i in $(seq 1 $(INSTANCES)); do \
		vol=augur$$i-postgres; \
		mount_path=$$(podman volume inspect $$vol --format '{{ .Mountpoint }}'); \
		if [ -d "$$mount_path" ]; then \
			tarball=db_snapshots/$$vol-`date +%Y%m%d_%H%M%S`.tar.gz; \
			echo "  🔄 Archiving $$vol to $$tarball ..."; \
			tar czf "$$tarball" -C "$$mount_path" .; \
			echo "  ✅ Snapshot complete for $$vol"; \
		else \
			echo "  ⚠️ Volume $$vol not found or not mounted."; \
		fi; \
	done

bootstrap-restore:
	@echo "🚀 Running full bootstrap + restore (regen --force → build → up → restore-all)"
	$(MAKE) FORCE=1 regen
	$(MAKE) build
	$(MAKE) up
	$(MAKE) restore-all

# Restore a single DB volume from snapshot. Usage: make restore-db FILE=db_snapshots/augur1-postgres-20250804_154412.tar.gz
restore-db:
ifndef FILE
	$(error ❌ Please specify a snapshot file to restore, e.g., make restore-db FILE=db_snapshots/augur1-postgres-20250804_*.tar.gz)
endif
	@echo "⏹️ Stopping containers before restore..."
	$(MAKE) down
	@echo "🧠 Restoring from snapshot: $(FILE)"
	@inst=$$(echo $(FILE) | sed -E 's/.*\/augur([0-9]+)-postgres.*/\1/'); \
	vol=augur$$inst-postgres; \
	mount_path=$$(podman volume inspect $$vol --format '{{ .Mountpoint }}'); \
	if [ -d "$$mount_path" ]; then \
		echo "  🔥 Wiping old volume contents for $$vol"; \
		sudo rm -rf "$$mount_path"/*; \
		echo "  📦 Extracting $(FILE) to $$mount_path"; \
		sudo tar xzf $(FILE) -C "$$mount_path"; \
		echo "  ✅ Restore complete for $$vol"; \
	else \
		echo "  ❌ ERROR: Volume $$vol not found"; \
		exit 1; \
	fi
	@echo "🚀 Bringing stack back up..."
	$(MAKE) up

