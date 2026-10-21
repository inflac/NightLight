#!/bin/bash
set -a
source /app/.env
set +a
curl -X GET "http://localhost:5000/update_status?api_key=$API_KEY&status=default"