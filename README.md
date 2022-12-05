# Waggle Site Backend (Previously Auth App)

This Django project provides a few different APIs and services for Waggle. They are roughly broken down into the following apps:

* `app (to be renamed to something more descriptive)`. Manages user accounts, authentication through Globus, and their permissions across the site. Specfically, scheduler and dev node access is managed by this.
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

Next, run the one time database migratations and create a super user.

```sh
python manage.py migrate
python manage.py createsuperuser
```

You can run the test suite using:

```sh
python manage.py test
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

### Enable user login via Globus OIDC (Optional)

You can configure user login via Globus OIDC by performing the following _one time_ setup:

1. Go to [https://developers.globus.org](https://developers.globus.org)
2. Go to Register your app with Globus
3. Create an app with a name like "Test App"
  * Set redirect URL to: `http://localhost:8000/globus-auth-redirect/`
  * Copy the following template to `~/waggle-auth-oidc.env` and fill in your client ID, client secret and redirect URL:

```sh
export OIDC_CLIENT_ID="Your Client ID!"
export OIDC_CLIENT_SECRET="Your Client Secret!"
```

You can enable Globus OIDC login by sourcing the env file _before_ running either one of the development environments:

```sh
. ~/waggle-auth-oidc.env
```
