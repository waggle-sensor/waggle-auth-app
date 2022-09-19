# Auth App

This is a prototype app which implements user, project and node access permissions management.

## Configurations

There are two development / deployment configurations:

* dev: intended for fast, local dev on host machine. debug flags are enabled.
* prod: intended for testing in docker compose prior to deploying to production cluster. debug flags are disabled and more security settings are enabled.

### Local development using dev configuration

_I highly recommend creating a virtual env when working on the app. I typically use:_

```sh
# create venv
python3 -m venv venv

# activate for bash (or, if you use fish, . venv/bin/activate.fish)
. venv/bin/activate
```

After activating your venv, install the dev requirements:

```sh
pip install -r requirements/dev.txt
```

Next, run the one time database migratations and create a super user.

```sh
python manage.py migrate
python manage.py createsuperuser
```

Finally, you can start the dev server:

```sh
python manage.py runserver
```

### Running in docker compose using prod configuration

To stand up the prod environment in docker compose, simply run:

```sh
make start
```

Wait a moment for all the containers to start, then run:

```sh
make migrate collectstatic
```

This will perform a one time database migration and compilation of all static assets.

Finally, create a super user using:

```sh
make createsuperuser
```

Try visiting [http://localhost:8000/admin/](http://localhost:8000/admin/) to ensure the app is running.
