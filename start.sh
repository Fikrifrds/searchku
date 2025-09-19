#!/bin/bash

# SearchKu Application Startup Script
# This script helps you get the SearchKu application running quickly

set -e

echo "🚀 Starting SearchKu Application..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create backend .env file if it doesn't exist
if [ ! -f "backend/.env" ]; then
    echo "📝 Creating backend .env file..."
    cp backend/.env.example backend/.env
    echo "⚠️  Please edit backend/.env and add your OpenAI API key!"
fi

# Create frontend .env file if it doesn't exist
if [ ! -f "frontend/.env" ]; then
    echo "📝 Frontend .env file already exists."
fi

# Check if OpenAI API key is set
if grep -q "your_openai_api_key_here" backend/.env; then
    echo "⚠️  Warning: OpenAI API key not set in backend/.env"
    echo "   Please edit backend/.env and replace 'your_openai_api_key_here' with your actual API key"
    echo "   You can continue without it, but semantic search won't work."
    read -p "   Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "🐳 Starting Docker containers..."
docker-compose up -d

echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if services are running
echo "🔍 Checking service status..."
docker-compose ps

echo ""
echo "✅ SearchKu is starting up!"
echo ""
echo "📱 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo "🗄️  Database: localhost:5432 (searchku/searchku_user/searchku_password)"
echo ""
echo "📋 Useful commands:"
echo "   View logs: docker-compose logs -f"
echo "   Stop services: docker-compose down"
echo "   Restart services: docker-compose restart"
echo "   View database: docker-compose exec postgres psql -U searchku_user -d searchku"
echo ""
echo "🎉 Happy searching!"