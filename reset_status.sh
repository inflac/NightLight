#!/bin/bash
export $(grep -v '^#' /app/.env | xargs)
curl -X GET "http://localhost:5000/update_status?api_key=$API_KEY&status=default"