FROM ubuntu:xenial

MAINTAINER OPS <reinout.vanrees@nelen-schuurmans.nl>

# Change the date to force rebuilding the whole image
ENV REFRESHED_AT 20160830

# system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    build-essential \
    git \
    libevent-dev \
    libfreetype6-dev \
    libpng12-dev \
    python3-dev \
    gettext \
    memcached \
&& apt-get clean -y && rm -rf /var/lib/apt/lists/*

VOLUME /code
WORKDIR /code
