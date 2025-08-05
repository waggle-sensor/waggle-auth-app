# Waggle Site Backend (Previously Auth App)

A Django project providing APIs and services for Waggle, including user authentication, node manifest management, and more.

## Table of Contents
- [Project Overview](#project-overview)
- [Environment Variables](#environment-variables)
- [Local Development](#local-development)
- [Production Deployment](#production-deployment)
- [Object Storage](#object-storage)
- [INVENTORY_TOOLS: Manifest Automation](#inventory_tools-manifest-automation)
- [WireGuard Integration](#wireguard-integration)
- [Globus OIDC Login](#globus-oidc-login)
- [Make Commands for Docker Deployment](#make-commands-for-docker-deployment)
- [Test Data & Running Tests](#test-data--running-tests)

---

## Project Overview

The project is broken down into the following apps:

- **`app`**: Manages user accounts, Globus authentication, and permissions (e.g. scheduling, dev, node access).
- **`manifests`**: Handles node, hardware, and sensor data; provides the manifest API.
- **`downloads`**: Handles HTTP redirects to files captured by nodes.
- **`node_auth`**: Handles node authentication.

---

## Environment Variables

Set these variables as needed:

>NOTE: If you are not working on any of the extensions, you can ignore the environment variables for them.

### Core
- `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_EMAIL`, `DJANGO_SUPERUSER_PASSWORD`: Superuser credentials.
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts.

### Object Storage (Downloads)
- `S3_ACCESS_KEY`, `S3_SECRET_KEY`: S3 credentials.
- `S3_ENDPOINT`, `S3_BUCKET_NAME`, `S3_ROOT_FOLDER`, `S3_REGION`: S3 config.
- `PELICAN_KEY_PATH`: Path to Pelican .pem file (in container).
- `PELICAN_KEY_ID`: JWT public key ID for Pelican.
- `PELICAN_ALGORITHM`, `PELICAN_ISSUER`, `PELICAN_LIFETIME`, `PELICAN_ROOT_URL`, `PELICAN_ROOT_FOLDER`: Pelican config.

### INVENTORY_TOOLS (Manifests Automation)
- `INV_TOOLS_REPO`: Path or URL to the inventory tools repo (e.g., `/app/waggle-inventory-tools` or the GitHub URL).
- `INV_TOOLS_TOKEN`: GitHub token for private repo access (if cloning via HTTPS).
- `INV_TOOLS_SSH_TOOLS`: Path to SSH tools directory (e.g., `/root/git`).
- `INV_TOOLS_SSH_CONFIG`: Path to SSH config directory (e.g., `/root/ssh`).
- `INV_TOOLS_SSH_TOOLS_PW`: Passphrase for the SSH identity file.

### WireGuard
- `WG_ENABLED`: Set to `True` to enable WireGuard.
- `WG_PRIV_KEY`, `WG_PUB_KEY`: WireGuard server's private/public keys.
- `WG_VAR_FILE`: File path in container to store Wireguard variables.
- `WG_IFACE`: Wireguard interface name.
- `WG_SERVER_ADDRESS_WITH_CIDR`: Wireguard server address with CIDR.
- `WG_PORT`: Wireguard server port.

### OIDC/Globus
- `OIDC_CLIENT_ID`, `OIDC_CLIENT_SECRET`: Globus OIDC credentials (see [Globus OIDC Login](#globus-oidc-login)).

---

## Local Development

I highly recommend using local python by creating a virtual environment for fast development, but you can also use docker for an easier startup of the server.

### Using Docker

Using Docker is the easiest way to get started, but developing is slower than using local python.

1. **Start the dev server (in Docker):**
   ```sh
   make up # foreground with logs
   # or
   make start # background
   ```
1. **Access the admin site:**
   - [http://localhost:8000/admin/](http://localhost:8000/admin/)
   - Username: `admin`, Password: `admin`

#### Configurations & Environments

Located in the `env/` folder are the Docker Compose configurations for the dev and prod environments:
- **dev**: For local development (debug enabled).
- **prod**: For production-like testing in Docker Compose (debug disabled, secure settings).

#### Additional Commands for Docker

1. **Run tests:**
   ```sh
   make test
   ```
1. **Load test data:**
   ```sh
   make loaddata DATA_FILE=<path_to_data.json>
   # Default: ../waggle-auth-app-fixtures/data.json
   ```

1. **Apply model changes:**
   ```sh
   make migrate
   ```
>NOTE: See [Make Commands](#make-commands-for-docker-deployment) for more commands.

### Using Local Python

Using local python is faster than using Docker, but requires more setup and knowledge of the project.

1. **Create and activate a virtual environment:**
   ```sh
   python3 -m venv venv
   . venv/bin/activate
   ```
1. **Install dependencies:**
   ```sh
   pip install -r requirements/dev.txt
   ```

1. **Apply model changes:**
   ```sh
   python manage.py makemigrations
   python manage.py migrate
   ```
  
1. **Create a superuser:**
   ```sh
   python manage.py createsuperuser
   ```

1. **Start the dev server:**
   ```sh
   python manage.py runserver
   ```

1. **Access the admin site:**
   - [http://localhost:8000/admin/](http://localhost:8000/admin/)

#### Additional Commands for Local Python

1. **Run tests:**
   ```sh
   pytest
   ```

---

## Production Deployment

1. **Start the production server:**
   ```sh
   make start ENV=prod
   ```
2. **Access admin:**
   - [http://localhost:8000/admin/](http://localhost:8000/admin/)
   - Username: `admin`, Password: `admin`
3. **Stop the server:**
   ```sh
   make stop ENV=prod
   ```

---

## Object Storage

The `downloads` app handles HTTP redirects to the files captured by nodes sitting in the object storage.

There are two ways to handle object storage:
- Using a S3 server
- Using [Pelican](https://pelicanplatform.org/)

---

## INVENTORY_TOOLS: Manifest Automation

**Purpose:** Automatically update node manifests from the inventory tools repo.

>NOTE: If you are not working on `INVENTORY_TOOLS` this can be ignored.

### Environment Setup
- See [Environment Variables](#environment-variables) for the required environment variables.

### Volumes & SSH Setup

**INVENTORY_TOOLS requires SSH access to nodes.**

1. **Clone the inventory tools repo** (if not using a pre-mounted path):
   ```sh
   git clone git@github.com:waggle-sensor/waggle-inventory-tools.git
   # or use HTTPS with INV_TOOLS_TOKEN
   ```
2. **Prepare SSH keys/config:**
   - Place your SSH private key (e.g., `ecdsa-sage-waggle`) in a directory (e.g., `~/waggle-ssh`).
   - Create an SSH config file if needed.
3. **Mount volumes in Docker Compose:**
   - Add to your `docker-compose.yaml`:
     ```yaml
     volumes:
       - /path/to/waggle-inventory-tools:/app/waggle-inventory-tools:rw
       - /path/to/waggle-ssh:/root/git:ro
       - /path/to/ssh-config:/root/ssh:ro
     ```
   - Set corresponding env vars in `.env`:
     ```env
     INV_TOOLS_REPO=/app/waggle-inventory-tools
     INV_TOOLS_SSH_TOOLS=/root/git
     INV_TOOLS_SSH_CONFIG=/root/ssh
     INV_TOOLS_SSH_TOOLS_PW=<your_ssh_key_passphrase>
     ```

>TODO Add a Makefile target to automate this setup.

### Running Locally
- To load manifests for all nodes:
  ```sh
  ./manage.py loadmanifest --repo <inventory_tools_local_path>
  ```
- To load for specific nodes:
  ```sh
  ./manage.py loadmanifest --repo <inventory_tools_local_path> --vsns W08E
  ```
- You can also use the `autoloadmanifest` command for automated/periodic updates.

### Adding Mappers for Computes & Sensors

To extend manifest parsing for new compute or sensor types:
- **Compute mappers:** Edit `manifests/management/commands/mappers/compute_mappers.py`.
- **Sensor mappers:** Edit `manifests/management/commands/mappers/sensor_mappers.py`.
- **Resource mappers:** Edit `manifests/management/commands/mappers/resource_mappers.py`.

**Example:**
```python
# In compute_mappers.py
COMPUTE_MAPPERS.append({
    "match": lambda dev: dev.get("type") == "new_compute_type",
    "resolve_hardware": lambda name: ...,
    # ...
})
```
---

## WireGuard Integration

The `node_auth` app handles the wireguard integration for nodes.

- **Enable by setting `WG_ENABLED=True`.**
- Requires Linux for port forwarding (does not work on macOS/Windows).
- The Docker image installs `wireguard-tools` and `iproute2` for this purpose.

>NOTE: If you are not working on `node_auth` this can be ignored by setting `WG_ENABLED=False`.

### Environment Setup
- See [Environment Variables](#environment-variables) for the required environment variables.

### WireGuard Setup

A Management Command is provided to setup the WireGuard server and clients.
```sh
# see the help for all the arguments
python manage.py setup_wireguard --<argument>
```

---

## Globus OIDC Login

1. **Register your app at [Globus Developers](https://developers.globus.org):**
   - Set redirect URL: `http://localhost:8000/globus-auth-redirect/`
2. **Create a client secret and save to `~/waggle-auth-oidc.env`:**
   ```sh
   export OIDC_CLIENT_ID="Your Client UUID!"
   export OIDC_CLIENT_SECRET="Your Client Secret!"
   ```
3. **Source the env file before starting the server:**
   ```sh
   . ~/waggle-auth-oidc.env
   ```
4. **Promote your user to superuser:**
   ```sh
   python manage.py shell
   >>> from django.contrib.auth import get_user_model
   >>> User = get_user_model()
   >>> user = User.objects.get(username="MY USERNAME")
   >>> user.is_staff = True
   >>> user.is_superuser = True
   >>> user.save()
   ```

---

## Make Commands for Docker Deployment

| Command                | Description                                                                                   |
|------------------------|-----------------------------------------------------------------------------------------------|
| `make start ENV=<env>` | Starts the server in the background (`dev` by default).                                       |
| `make stop ENV=<env>`  | Stops the background server (`dev` by default).                                               |
| `make migrate ENV=<env>` | Applies database migrations (`dev` by default).                                            |
| `make collectstatic ENV=<env>` | Collects static files (`dev` by default).                                          |
| `make createsuperuser ENV=<env>` | Creates a superuser (`dev` by default).                                        |
| `make loaddata DATA_FILE=<path> ENV=<env>` | Loads fixture data (`dev` and `../waggle-auth-app-fixtures/data.json` by default). |
| `make test ENV=<env>`  | Runs tests (`dev` by default).                                                                |
| `make up ENV=<env>`    | Starts the server and displays logs (`dev` by default).                                      |
| `make logs ENV=<env>`  | Displays logs for a running server (`dev` by default).                                        |

> ENV can be `dev` or `prod`.

---

## Test Data & Running Tests

- **Run all tests:**
  ```sh
  pytest
  # or
  make test
  ```
- **Load test data:**
  ```sh
  make loaddata DATA_FILE=<path_to_data.json> # Default: ../waggle-auth-app-fixtures/data.json
  # or
  python manage.py loaddata <path_to_data.json>
  ```

---
