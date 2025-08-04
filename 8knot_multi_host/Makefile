COMPOSE = podman-compose
INSTANCES = 8
DOMAIN = augurlabs.io
INSTANCE ?= 1

all: up

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

# Force remove containers and networks for instances
nuke:
	-@echo "Removing instance containers..."
	-@podman ps -a --format "{{.ID}} {{.Names}}" | grep instance | awk '{print $$1}' | xargs -r podman rm -f
	-@echo "Removing instance volumes..."
	-@podman volume ls --format "{{.Name}}" | grep instance | xargs -r podman volume rm
	-@echo "Removing networks with 'knot' in their name..."
	-@podman network ls --format "{{.Name}}" | grep knot | xargs -r podman network rm

# Full clean: stop everything, remove containers/networks/volumes/images
clean: down nuke
	-@echo "Removing orphaned podman resources..."
	-@podman volume prune -f
	-@podman image prune -f
	-@podman network prune -f
	@echo "Clean complete."
