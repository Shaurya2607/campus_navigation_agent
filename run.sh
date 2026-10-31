#!/bin/bash
# Intelligent Campus Navigation Agent - Convenient Launch Script

set -e
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "=========================================================="
echo "      🧭 INTELLIGENT CAMPUS NAVIGATION AGENT LAUNCHER     "
echo "=========================================================="
echo "1) Start Web Interface & REST API Server (Recommended)"
echo "2) Start Desktop Graphical Interface (Tkinter GUI)"
echo "3) Start Continuous Autonomous Test Server (Loop & Dashboard)"
echo "4) Run Unit Test Suite (9 Tests)"
echo "5) Exit"
echo "=========================================================="

if [ -n "$1" ]; then
    CHOICE="$1"
else
    read -p "Select option [1-5]: " CHOICE
fi

case $CHOICE in
    1)
        echo "Starting Web Server at http://localhost:8080 ..."
        python3 server.py 8080
        ;;
    2)
        echo "Launching Tkinter Desktop GUI..."
        python3 gui_app.py
        ;;
    3)
        echo "Starting Continuous Test Server at http://localhost:8090 ..."
        python3 test_server.py 8090
        ;;
    4)
        echo "Running test suite..."
        python3 test_navigation.py
        ;;
    *)
        echo "Exiting."
        exit 0
        ;;
esac
