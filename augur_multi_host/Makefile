# --- Global variables ---
COMPOSE = podman-compose
INSTANCES = 8
DOMAIN = sociallycompute.io
INSTANCE ?= 1
AUGUR_PATH ?=

ifndef AUGUR_PATH
$(error AUGUR_PATH is not set. Use 'make AUGUR_PATH=/your/path bootstrap' or export it)
endif

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
	@echo "Rebuilding docker-compose.yml ..."
	python3 generate_compose.py $(AUGUR_PATH)

build:
	$(COMPOSE) build

up:
	$(COMPOSE) up -d

down:
	$(COMPOSE) down --remove-orphans

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
	-podman ps --all --format "{{.ID}} {{.Names}}" | grep augur_multi_host | awk '{print $$1}' | xargs podman rm -f
	-podman network ls --format "{{.Name}}" | grep augur_multi_host_augur | xargs podman network rm