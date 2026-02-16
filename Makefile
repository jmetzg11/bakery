.PHONY: run stop

run:
	docker compose up -d
	@until docker compose exec db pg_isready -U bakery > /dev/null 2>&1; do sleep 0.5; done
	cd src && uv run python manage.py migrate
	cd src && DJANGO_SUPERUSER_PASSWORD=admin uv run python manage.py createsuperuser --username admin --email "" --noinput 2>/dev/null || true
	cd src && uv run python manage.py runserver

seed:
	cd src && uv run python manage.py seed

stop:
	docker compose down -v
