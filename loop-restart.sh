#!/bin/bash

source venv/bin/activate
export PYTHONPATH=$(pwd)
while true; do
    APP_ENV=DEV python3 app/main.py &
    APP_PID=$!

    echo "Uvicorn server started with PID $APP_PID. Running for 10 minute..."
    sleep 600

    echo "Stopping Uvicorn server with PID $APP_PID..."
    kill $APP_PID
    wait $APP_PID 2>/dev/null

    echo "Restarting Uvicorn server..."
done
