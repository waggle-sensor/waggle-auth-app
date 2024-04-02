start:
	@docker-compose up --build -d

stop:
	@docker-compose down --volumes --remove-orphans

migrate:
	@docker-compose exec django python manage.py migrate

collectstatic:
	@docker-compose exec django python manage.py collectstatic --no-input

createsuperuser:
	@docker-compose exec django python manage.py createsuperuser

test:
	@docker-compose exec django python manage.py test
	@docker-compose exec django python manage.py check --deploy
