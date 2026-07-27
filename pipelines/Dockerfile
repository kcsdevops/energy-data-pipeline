# Shared base image for the bronze/silver/gold Spark jobs.
# Each stage's entrypoint is overridden by the Kubernetes Job/CronJob command.
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

ENTRYPOINT ["python"]
