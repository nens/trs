FROM ubuntu:jammy
# Jammy = 22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
WORKDIR /code

# system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    git \
    build-essential \
    libevent-dev \
    nano \
    npm \
    python3-dev \
    python3-pip \
    python3-venv \
    python3-pil \
    gettext \
    memcached \
&& apt-get clean -y && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY pyproject.toml uv.lock ./
RUN uv sync
ENV PATH="/code/.venv/bin:$PATH"

COPY . .
RUN make install
