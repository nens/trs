FROM ubuntu:bionic

# system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    build-essential \
    git \
    libevent-dev \
    python3-dev \
    python3-pip \
    python3-venv \
    python3-pil \
    gettext \
    memcached \
&& apt-get clean -y && rm -rf /var/lib/apt/lists/*

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

VOLUME /code
WORKDIR /code
