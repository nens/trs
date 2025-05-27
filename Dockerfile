FROM python:3.12-bookworm
LABEL project_name="trs"

# system dependencies
RUN apt-get update && apt-get install -y \
    npm \
&& apt-get clean -y && rm -rf /var/lib/apt/lists/*

WORKDIR /code

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY pyproject.toml uv.lock ./
RUN uv sync
ENV PATH="/code/.venv/bin:$PATH"

ENV PYTHONWARNINGS=always
COPY . .
RUN make install
CMD ["gunicorn", "--bind=0.0.0.0:5000", "--workers=3", "--timeout=180", "--preload", "--max-requests=10000", "trs.wsgi"]
