#!/bin/sh
echo "Running database migration..."
cd /app/config
python migrate.py
cd /app
echo "Starting server..."
uvicorn main:app --host 0.0.0.0 --port 8000