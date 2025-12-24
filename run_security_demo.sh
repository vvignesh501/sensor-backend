#!/bin/bash

# Security Demo Quick Start Script

echo "🔐 Security Implementation Demo"
echo "================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

echo "✓ Python 3 found"

# Install dependencies
echo ""
echo "📦 Installing security dependencies..."
pip install -q -r requirements-security.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "✓ Dependencies installed"

# Start the secure API in background
echo ""
echo "🚀 Starting Secure API..."
python app/secure_app.py &
API_PID=$!

# Wait for API to start
echo "⏳ Waiting for API to start..."
sleep 3

# Check if API is running
if ! ps -p $API_PID > /dev/null; then
    echo "❌ Failed to start API"
    exit 1
fi

echo "✓ API started (PID: $API_PID)"
echo ""
echo "📍 API running at: http://localhost:8000"
echo "📚 API docs at: http://localhost:8000/docs"
echo ""

# Run tests
echo "🧪 Running security tests..."
echo ""
python test_security.py

# Ask user if they want to stop the API
echo ""
read -p "Press Enter to stop the API and exit..."

# Stop the API
echo ""
echo "🛑 Stopping API..."
kill $API_PID
echo "✓ API stopped"
echo ""
echo "Demo complete! 🎉"
