COMPOSE = podman-compose
INSTANCES = 8
DOMAIN = augurlabs.io
INSTANCE ?= 1
REGEN_ARGS ?=

regen:
	@echo "Rebuilding docker-compose.yml ..."
	python3 generate_compose.py $(REGEN_ARGS)

build:
	$(COMPOSE) build

up-one:
	$(COMPOSE) up -d instance$(INSTANCE)

up:
	@echo "Currently running instance containers:"
	@podman ps --format '{{.Names}}' | grep -E '^instance[0-9]+$$' || echo "  None running."
	@echo "Bringing up all instances..."
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
