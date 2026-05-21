
FROM python:3.8-slim


ENV FLASK_APP=ekg_cre_redis.py
ENV FLASK_RUN_HOST=0.0.0.0

WORKDIR /app


RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt


COPY . .


CMD ["flask", "run"]
