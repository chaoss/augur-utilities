COMPOSE = podman-compose
INSTANCES = 8
DOMAIN = augurlabs.io
INSTANCE ?= 1
REGEN_ARGS ?=

regen:
	@echo "🔄 Rebuilding docker-compose.yml ..."
	python3 generate_compose.py $(REGEN_ARGS)

regen-nginx:
	@echo "🔄 Generating nginx.conf from labels.txt ..."
	python3 generate_nginx.py $(DOMAIN)

build:
	@echo "🔨 Building all containers ..."
	$(COMPOSE) build

build-one:
	@echo "🔨 Building instance$(INSTANCE) ..."
	$(COMPOSE) build instance$(INSTANCE)

up:
	@echo "🚀 Currently running instance containers:"
	@podman ps --format '{{.Names}}' | grep -E '^instance[0-9]+$$' || echo "  None running."
	@echo "⬆️  Bringing up all instances..."
	podman-compose down --remove-orphans && podman container prune -f && sudo systemctl reset-failed && sudo find /run/systemd/transient /etc/systemd/system -name 'podman-*.timer' -delete
	$(COMPOSE) up -d

up-one:
	@echo "⬆️  Bringing up instance$(INSTANCE) ..."
	$(COMPOSE) up -d instance$(INSTANCE)

down:
	@echo "🧹 Shutting down all containers ..."
	$(COMPOSE) down --remove-orphans

restart:
	@echo "🔁 Restarting all containers ..."
	$(COMPOSE) restart

logs:
	$(COMPOSE) logs -f instance$(INSTANCE)

ps:
	$(COMPOSE) ps

shell:
	$(COMPOSE) exec instance$(INSTANCE) /bin/bash

status:
	@echo "📄 Checking environment files:"
	@for i in $$(seq 1 $(INSTANCES)); do \
		f=envs/instance$$i.env; \
		if [ -f $$f ]; then echo "  ✅ $$f"; else echo "  ❌ $$f MISSING"; fi; \
	done

stop-all:
	@echo "🛑 Stopping all running containers..."
	-podman stop $$(podman ps -q)

nuke:
	@echo "💣 Nuking all containers and networks matching pattern..."
	-podman ps -a --format "{{.ID}} {{.Names}}" | grep instance || true | awk '{print $$1}' | xargs podman rm -f
	-podman network ls --format "{{.Name}}" | grep knot | xargs podman network rm
