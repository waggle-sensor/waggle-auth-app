start:
	docker-compose up --build -d

stop:
	docker-compose down --volumes

migrate:
	docker-compose exec django python manage.py migrate

collectstatic:
	docker-compose exec django python manage.py collectstatic --no-input

createsuperuser:
	docker-compose exec django python manage.py createsuperuser
