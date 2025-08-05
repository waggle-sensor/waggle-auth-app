FROM python:3.11
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y wireguard-tools iproute2
COPY requirements /app/requirements
RUN pip install --no-cache-dir -r requirements/prod.txt
COPY . /app
# include staticfiles for whitenoise
RUN python manage.py collectstatic --noinput