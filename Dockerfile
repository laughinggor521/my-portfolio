FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8080 UPLOAD_DIR=/data/uploads
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates && rm -rf /var/lib/apt/lists/* && groupadd --system app && useradd --system --gid app --home-dir /app app && mkdir -p /data/uploads && chown -R app:app /app /data
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY site ./site
COPY migrations ./migrations
COPY wsgi.py .
COPY docker-entrypoint.sh .
RUN chmod 755 /app/docker-entrypoint.sh && chown -R app:app /app
USER app
EXPOSE 8080
ENTRYPOINT ["/app/docker-entrypoint.sh"]
