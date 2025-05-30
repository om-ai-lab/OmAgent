#!/bin/bash

set -e

echo "🤖 Setting up MCP Tools Docker Environment"
echo "=========================================="

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

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp env.example .env
    echo "✅ .env file created. Please edit it with your API keys and configuration."
    echo "   You need to set at least MEM0_API_KEY for the memory service to work."
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p vlm/images
mkdir -p simulator/logs
mkdir -p logs

# Build all images
echo "🏗️  Building Docker images..."
docker-compose build

# Pull required images
echo "📥 Pulling required images..."
docker-compose pull

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your API keys"
echo "2. Run 'make up' or 'docker-compose up -d' to start all services"
echo "3. Use 'make status' to check service status"
echo "4. Use 'make logs' to view logs"
echo ""
echo "Available services:"
echo "- VLM Server: http://localhost:8009"
echo "- UT Dog Server: http://localhost:3000"
echo "- Thor Simulator: http://localhost:3001"
echo "- Memory Server: http://localhost:8080"
echo "- Milvus Server: http://localhost:8000"
echo "- Switch Robot: http://localhost:8010"
echo ""
echo "For help, run 'make help'" 