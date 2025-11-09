#!/bin/bash

# Run both Django backend and Vue frontend in development mode

echo "🏓 Starting Ping Pong Tracker Development Servers..."
echo ""

# Function to kill processes on exit
cleanup() {
    echo ""
    echo "Shutting down servers..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

# Set up trap to cleanup on script exit
trap cleanup EXIT INT TERM

# Start Django backend
echo "Starting Django backend on http://localhost:8000..."
cd backend
source venv/bin/activate
python manage.py runserver &
BACKEND_PID=$!
cd ..

# Give Django a moment to start
sleep 2

# Start Vue frontend
echo "Starting Vue frontend on http://localhost:5173..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ Both servers are running!"
echo ""
echo "📍 Frontend: http://localhost:5173"
echo "📍 Backend API: http://localhost:8000/api"
echo "📍 Django Admin: http://localhost:8000/admin"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Wait for both processes
wait