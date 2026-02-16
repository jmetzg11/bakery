.PHONY: run stop

run:
	docker compose up -d
	@until docker compose exec db pg_isready -U bakery > /dev/null 2>&1; do sleep 0.5; done
	cd src && uv run python manage.py migrate
	cd src && uv run python manage.py seed
	cd src && uv run python manage.py runserver

stop:
	docker compose down -v
