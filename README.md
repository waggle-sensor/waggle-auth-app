# Waggle Site Backend (Previously Auth App)

This Django project provides a few different APIs and services for Waggle. They are roughly broken down into the following apps:

* `app (to be renamed to something more descriptive)`. Manages user accounts, authentication through Globus, and their permissions across the site. Specifically, scheduler and dev node access is managed by this.
* `manifests`. Manages data for nodes, hardware and sensors and provides our manifest API.

This list may be expanded upon in the future.

## Configurations

There are two development / deployment configurations:

* dev: intended for fast, local dev on host machine. debug flags are enabled.
* prod: intended for testing in docker compose prior to deploying to production cluster. debug flags are disabled and more security settings are enabled.

Optionally, you can configure user login via Globus OIDC for either of these environments.

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

Next, run the one time static file collection, database migrations and create a super user.

```sh
python manage.py collectstatic
python manage.py migrate
python manage.py createsuperuser
```

You can run the test suite using the following [pytest](https://docs.pytest.org/) command:

```sh
# This must be done after one time setup, otherwise some tests will fail!
pytest
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
make migrate
make collectstatic
make createsuperuser
```

This will perform the one time database migrations, compilation of all static assets and creation of a super user.

Try visiting [http://localhost:8000/admin/](http://localhost:8000/admin/) to ensure the app is running.

The test suite can be run using:

```sh
make test
```

Finally, when you're done working, you can stop everything using:

```sh
make stop
```

### Enable user login via Globus OIDC

You can configure user login via Globus OIDC by performing the following _one time_ setup:

1. Go to [https://developers.globus.org](https://developers.globus.org)
2. Go to Register your app with Globus
3. Create an app using `Register a portal, science gateway, or other application you host` with a name like "Test App"
  * Set redirect URL to: `http://localhost:8000/globus-auth-redirect/`.
4. Create a client secret using your new app's dashboard
  * Copy the following template to `~/waggle-auth-oidc.env` and fill in your Client UUID and client secret:

```sh
export OIDC_CLIENT_ID="Your Client UUID!"
export OIDC_CLIENT_SECRET="Your Client Secret!"
```

You can enable Globus OIDC login by sourcing the env file _before_ running either one of the development environments:

```sh
. ~/waggle-auth-oidc.env
```
5. Run your django server `python manage.py runserver` and log in by creating a new account. **Keep note of your username**
6. On first run of your server, you will get an error as your account is not a *Superuser*. To fix this, open the django shell and run these commands
```sh
python3 manage.py shell
```
```py
from django.contrib.auth import get_user_model
User = get_user_model()
user = User.objects.get(username="MY USERNAME")
user.is_staff = True
user.is_admin = True
user.is_superuser = True
user.save()
```
7. You should now be able to run your django server and log in to the admin site succesfully
