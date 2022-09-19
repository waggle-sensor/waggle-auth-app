FROM python:3.10
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements /app/requirements
RUN pip install --no-cache-dir -r requirements/prod.txt
COPY . /app
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:80"]
