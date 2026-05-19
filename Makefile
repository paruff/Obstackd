.PHONY: check-env up up-apps

check-env:
	./scripts/check-env.sh

up: check-env
	docker compose --profile core up -d

up-apps: check-env
	docker compose --profile core --profile apps up -d
