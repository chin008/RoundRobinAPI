#!/bin/bash
echo "Starting backend on 5001..."
python3 app_api.py 5001 &

echo "Starting backend on 5002..."
python3 app_api.py 5002 &

echo "Starting backend on 5003..."
python3 app_api.py 5003 &

echo "Starting round robin router on 8000..."
python3 round_robin_api.py
