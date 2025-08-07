# ------------------------------------------
# Stage 1: Build wireguard-go from source
# ------------------------------------------
FROM golang:1.23-alpine AS builder

# Install build dependencies
RUN apk add --no-cache git make

# Clone and checkout specific wireguard-go tag
ENV WIREGUARD_GO_VERSION=0.0.20250522
RUN git clone https://git.zx2c4.com/wireguard-go \
 && cd wireguard-go \
 && git checkout ${WIREGUARD_GO_VERSION} \
 && make \
 && cp wireguard-go /wireguard-go

# ------------------------------------------
# Stage 2: Final Image with Django
# ------------------------------------------
FROM python:3.11
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y wireguard-tools iproute2
COPY --from=builder /wireguard-go /usr/local/bin/wireguard-go
COPY requirements /app/requirements
RUN pip install --no-cache-dir -r requirements/dev.txt
COPY . /app
# include staticfiles for whitenoise
RUN python manage.py collectstatic --noinput
