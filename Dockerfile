FROM ubuntu:focal

ENV DEBIAN_FRONTEND=noninteractive
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

# system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    git \
    build-essential \
    libevent-dev \
    npm \
    python3-dev \
    python3-pip \
    python3-venv \
    python3-pil \
    gettext \
    memcached \
&& apt-get clean -y && rm -rf /var/lib/apt/lists/*

WORKDIR /code
COPY . .
RUN make install
