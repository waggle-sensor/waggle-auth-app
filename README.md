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

You can run the test suite using:

```sh
python manage.py test
```

Finally, you can start the dev server:

```sh
python manage.py runserver
```

#### Enabling Globus OIDC login (Optional)

You can configure user login via Globus OIDC by performing the following one time setup:

1. Go to [https://developers.globus.org](https://developers.globus.org)
2. Go to Register your app with Globus
3. Create an app with a name like "Test App"
  * Set redirect URL to: `http://localhost:8000/globus-auth-redirect`
  * Copy the client ID, client secret and redirect URL and add them the following template in a convinient location like `~/waggle-auth-oidc.env`:

```sh
export OIDC_CLIENT_ID="Your Client ID!"
export OIDC_CLIENT_SECRET="Your Client Secret!"
export OIDC_REDIRECT_URI="http://localhost:8000/globus-auth-redirect"
```

Then, source the env using and rerun the server.

```sh
. ~/waggle-auth-oidc.env
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
