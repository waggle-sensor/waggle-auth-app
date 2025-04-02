FROM python:3.11
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Install cron
RUN apt-get update && \
    apt-get install -y cron && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements /app/requirements
RUN pip install --no-cache-dir -r requirements/dev.txt
COPY . /app
# include staticfiles for whitenoise
RUN python manage.py collectstatic --noinput
# Create cron job file with echo
RUN echo "*/30 * * * * root python /app/manage.py shell < /app/scripts/load_manifest.py" > /etc/cron.d/update-manifest
# Set permissions and register the cron job
RUN chmod 0644 /etc/cron.d/update-manifest && \
    crontab /etc/cron.d/update-manifest