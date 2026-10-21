FROM python:3.13-slim

WORKDIR /app
COPY . .

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends cron curl && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r requirements.txt

# Configure reset cron job
RUN chmod +x /app/reset_status.sh
RUN echo "0 1 * * * /bin/bash /app/reset_status.sh >> /var/log/cron.log 2>&1" >> /etc/cron.d/reset-status-cron
RUN chmod 0644 /etc/cron.d/reset-status-cron
RUN crontab /etc/cron.d/reset-status-cron

EXPOSE 5000

# Write the container env to /app/.env, since cron jobs (reset_status.sh) do not inherit it
CMD export -p > /app/.env && cron && gunicorn --log-level info --timeout 120 -w 3 -b ${HOST}:5000 server:app
