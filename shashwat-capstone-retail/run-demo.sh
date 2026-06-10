#!/usr/bin/env bash
# Start API in background, then UI in foreground
cd "$(dirname "$0")"
./start-api.sh &
API_PID=$!
sleep 3
echo "API PID: $API_PID"
trap "kill $API_PID 2>/dev/null" EXIT
./start-ui.sh
