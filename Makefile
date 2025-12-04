.PHONY: migrate test lint docker-up

migrate:
	docker compose exec backend alembic upgrade head

test:
	pytest backend/tests -q

lint:
	ruff check backend/app backend/tests
	mypy backend/app

docker-up:
	docker compose up -d
