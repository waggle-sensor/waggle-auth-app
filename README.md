# Auth App

This is a prototype app which implements user, project and node access permissions management.

## Local Development Env

_I highly recommend creating a virtual env when working on the app. I typically use:_

```sh
# create venv
python3 -m venv venv

# activate for bash (or, if you use fish, . venv/bin/activate.fish)
. venv/bin/activate
```

After activating the venv, instead the dev requirements:

```sh
pip install -r requirements/dev.txt
```

Now you're ready to start developing! You should now be able to run database migratations and create a super user.

## Docker Compose Env

To stand up the docker compose environment, simply run:

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
