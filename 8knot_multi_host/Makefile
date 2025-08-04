COMPOSE = podman-compose
INSTANCES = 8
DOMAIN = augurlabs.io
INSTANCE ?= 1

all: up

regen:
	@echo "Rebuilding docker-compose.yml ..."
	python3 generate_compose.py

build:
	$(COMPOSE) build

up:
	$(COMPOSE) up -d

down:
	$(COMPOSE) down --remove-orphans

restart:
	$(COMPOSE) restart

ps:
	$(COMPOSE) ps

shell:
	$(COMPOSE) exec instance$(INSTANCE) /bin/bash

logs:
	$(COMPOSE) logs -f instance$(INSTANCE)

status:
	@echo "Environment files:"
	@for i in $$(seq 1 $(INSTANCES)); do \
		f=envs/instance$$i.env; \
		if [ -f $$f ]; then echo "  $$f exists"; else echo "  $$f MISSING"; fi; \
	done

stop-all:
	podman stop $$(podman ps -q)

nuke:
	-podman ps -a --format "{{.ID}} {{.Names}}" | grep instance || true | awk '{print $$1}' | xargs podman rm -f
	-podman network ls --format "{{.Name}}" | grep knot | xargs podman network rm
