FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY src/ src/
COPY data/ data/

RUN mkdir -p /app/data

EXPOSE 8000

CMD ["airline-sked", "serve", "--host", "0.0.0.0", "--port", "8000"]
