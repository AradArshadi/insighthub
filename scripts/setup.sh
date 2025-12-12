#!/bin/bash
# Setup script for Insighthub development

set -e  # Exit on error

echo "🚀 Setting up Insighthub Development Environment..."

# Check if Python 3.11+ is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed. Please install Python 3.11+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo "✅ Python $PYTHON_VERSION detected"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📦 Installing dependencies..."
pip install -e .  # Install in development mode

# Create .env file from template if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📄 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your API keys!"
fi

# Create directory for logs
mkdir -p logs

# Generate a secure secret key if not in .env
if ! grep -q "DJANGO_SECRET_KEY" .env; then
    echo "🔑 Generating Django secret key..."
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))")
    echo "DJANGO_SECRET_KEY=$SECRET_KEY" >> .env
fi

# Setup Docker (optional)
if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
    echo "🐳 Docker detected. Building containers..."
    make build
    
    echo "✅ Setup complete!"
    echo ""
    echo "📝 Next steps:"
    echo "1. Edit .env file with your API keys"
    echo "2. Run 'make up' to start services"
    echo "3. Visit http://localhost:8000"
else
    echo "⚠️  Docker not found. Using local setup..."
    echo "📝 Next steps:"
    echo "1. Install Docker and Docker Compose"
    echo "2. Run 'make up' to start services"
fi

echo ""
echo "🎉 Insighthub is ready for development!"