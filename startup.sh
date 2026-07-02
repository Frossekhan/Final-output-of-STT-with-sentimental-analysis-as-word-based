#!/bin/bash

# Sales Intelligence Platform - Startup Script
# Run: bash startup.sh or ./startup.sh

clear

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║  Sales Intelligence Platform - Startup Menu               ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "1. Quick Test (single conversation analysis)"
echo "2. Run System Tests (validate all components)"
echo "3. Batch Scoring Demo (score multiple leads)"
echo "4. Start Server (WebSocket streaming ready)"
echo "5. Start Full System (Server + Client in separate terminals)"
echo "6. View Documentation"
echo "7. Exit"
echo ""
read -p "Select option (1-7): " choice

case $choice in
    1)
        echo ""
        echo "Starting quick test..."
        python test_demo_simple.py
        ;;
    2)
        echo ""
        echo "Running system tests..."
        python test_system.py
        ;;
    3)
        echo ""
        echo "Starting batch scoring demo..."
        python demo_complete.py
        ;;
    4)
        echo ""
        echo "Starting FastAPI Server..."
        echo "Server will run on: http://0.0.0.0:8000"
        echo "WebSocket endpoint: ws://localhost:8000/ws/stream"
        echo "API docs: http://localhost:8000/docs"
        echo ""
        echo "Press Ctrl+C to stop the server"
        echo ""
        python server_prod.py
        ;;
    5)
        echo ""
        echo "This will start both server and client..."
        echo "Starting server in background..."
        python server_prod.py &
        SERVER_PID=$!
        echo "Server PID: $SERVER_PID"
        echo ""
        echo "Waiting 3 seconds for server to start..."
        sleep 3
        echo ""
        echo "Starting client..."
        python client_prod.py
        wait $SERVER_PID
        ;;
    6)
        echo ""
        echo "Opening documentation..."
        if command -v xdg-open &> /dev/null; then
            xdg-open PRODUCTION_GUIDE.md
        elif command -v open &> /dev/null; then
            open PRODUCTION_GUIDE.md
        else
            cat PRODUCTION_GUIDE.md
        fi
        ;;
    7)
        echo ""
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo ""
        echo "Invalid option. Exiting..."
        exit 1
        ;;
esac

exit 0
