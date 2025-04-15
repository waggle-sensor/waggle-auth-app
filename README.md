# Waggle Site Backend (Previously Auth App)

This Django project provides a few different APIs and services for Waggle. They are roughly broken down into the following apps:

* `app (to be renamed to something more descriptive)`. Manages user accounts, authentication through Globus, and their permissions across the site. Specifically, scheduler and dev node access is managed by this.
* `manifests`. Manages data for nodes, hardware and sensors and provides our manifest API.

This list may be expanded upon in the future.

## Configurations

There are two development / deployment configurations both in `env` folder:

* dev: intended for fast, local dev on host machine. debug flags are enabled.
* prod: intended for testing in docker compose prior to deploying to production cluster. debug flags are disabled and more security settings are enabled.

Optionally, for either of these environments you can configure...
- user login via Globus OIDC 
- http redirect to files captured by nodes (`downloads` app)
- Automatic updates of node manifests (`INVENTORY_TOOLS`)

### Keys
For both environments, you will have to set up these keys in `env/<environment>/.env` so that the `downloads` app can work. 

- S3_ACCESS_KEY: This is the access key for your S3 storage
- S3_SECRET_KEY: This is the secret key for your S3 storage
- PELICAN_KEY_PATH: This is the path to the .pem file for Pelican in the docker container
- PELICAN_KEY_ID: The id for the jwt public key used for Pelican found in `jwks.json` (https://sagecontinuum.org/.well-known/openid-configuration)

>NOTE: If you are not working on the `downloads` app this can be ignored.

You will also have to set up these keys in `env/<environment>/.env` so that `INVENTORY_TOOLS` can work. `INVENTORY_TOOLS` is used to update the manifest automatically.

- INV_TOOLS_TOKEN: This is a github token with clone/pull access to our [inventory tools repo](https://github.com/waggle-sensor/waggle-inventory-tools)
- INV_TOOLS_SSH_TOOLS_PW: This is the passphrase for our ecdsa-sage-waggle SSH IdentityFile

>NOTE: If you are not working on `INVENTORY_TOOLS` this can be ignored.

### Environment Variables

>TODO: add instructions for INVENTORY_TOOLS env variables and how to set them up

### Volumes

>TODO: Add instructions in setting up waggle_inv_tools for ssh access to nodes within the django container

>TODO: Add a make command to set up INVENTORY_TOOLS ssh and ssh tools volume. aka clone repos and set up ssh config 

>NOTE: If you are not working on `INVENTORY_TOOLS` this can be ignored.

## Local development using dev configuration

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

You can also start a dev server. The server will start in a docker container first running `migrate`, `createsuperuser`, and then `runserver`:
```sh
make up #to run and see logs or...
make start #to run in the background
```

To access the server once it's running visit [http://localhost:8000/admin/](http://localhost:8000/admin/) and log in using:

- Username: `admin`
- Password: `admin`

You can run the test suite using the following [pytest](https://docs.pytest.org/) command:

```sh
# This must be done after one time setup, otherwise some tests will fail!
pytest
```

If you want to load test data run: (Our test data is hosted in this [repo](https://github.com/waggle-sensor/waggle-auth-app-fixtures))

```sh
make loaddata DATA_FILE=<path_to_data.json> #default is ../waggle-auth-app-fixtures/data.json
```

After, making some edits to the models you can run:

```sh
python manage.py makemigrations
```

To implement the model edits to the server run:

```sh
make migrate
```

### Local development Inventory Tools

>TODO: add docs on running inventory tools locally

```sh
./manage.py loadmanifest --repo <inventory_tools_local_path> --vsns 
W08E
```

or to run for one node

```sh
./manage.py loadmanifest --repo <inventory_tools_local_path> --vsns 
W08E
```

## Running a local production server

To stand up the prod environment in docker compose, simply run:

```sh
make start ENV=prod #to run in the background
```

This will perform the one time database migrations, compilation of all static assets and creation of a super user.
To access the server once it's running visit [http://localhost:8000/admin/](http://localhost:8000/admin/) and log in using:

- Username: `admin`
- Password: `admin`

The test suite can be run using:

```sh
make test ENV=prod
```

Finally, when you're done working, you can stop everything using:

```sh
make stop ENV=prod
```

## Enable user login via Globus OIDC

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
user.is_superuser = True
user.save()
```
7. You should now be able to run your django server and log in to the admin site succesfully

## Make Commands

| Command                | Description                                                                                   |
|------------------------|-----------------------------------------------------------------------------------------------|
| `make start ENV=<env>` | Starts the server in the background (`dev` by default).                                       |
| `make stop ENV=<env>`  | Stops the background server (`dev` by default).                                               |
| `make migrate ENV=<env>` | Applies database migrations (`dev` by default).                                            |
| `make collectstatic ENV=<env>` | Collects static files (`dev` by default).                                          |
| `make createsuperuser ENV=<env>` | Creates a superuser (`dev` by default).                                        |
| `make loaddata DATA_FILE=<path> ENV=<env>` | Loads fixture data (`dev` and `../waggle-auth-app-fixtures/data.json` by default).                  |
| `make test ENV=<env>`  | Runs tests (`dev` by default).                                                                |
| `make up ENV=<env>`    | Starts the server and displays logs (`dev` by default).                                      |
| `make logs ENV=<env>`  | Displays logs for a running server (`dev` by default).                                        |
--- 

> ENV can be `dev` or `prod`
