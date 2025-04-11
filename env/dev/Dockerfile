FROM python:3.11
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
RUN apt-get update && \
    apt-get install -y cron rsync && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements /app/requirements
RUN pip install --no-cache-dir -r requirements/dev.txt
COPY . /app
# include staticfiles for whitenoise
RUN python manage.py collectstatic --noinput
# Create cron job file and set permissions
RUN echo "*/1 * * * * root /usr/local/bin/python /app/manage.py shell < /app/scripts/load_manifest.py > /proc/1/fd/1 2>&1" > /etc/cron.d/update-manifest && \
    chmod 0644 /etc/cron.d/update-manifest