FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        libnetcdf-dev \
        libhdf5-dev \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv==0.4.18

WORKDIR /app

COPY . .

RUN uv pip install --system --no-cache .

ENTRYPOINT ["anga"]
CMD ["--help"]
