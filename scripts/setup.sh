#!/bin/bash

# ========================================
# SHAYMEE AI AGENT - SETUP SCRIPT
# ========================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check system requirements
check_requirements() {
    print_status "Checking system requirements..."
    
    # Check Node.js
    if ! command_exists node; then
        print_error "Node.js is not installed. Please install Node.js 18+ first."
        exit 1
    fi
    
    NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$NODE_VERSION" -lt 18 ]; then
        print_error "Node.js version 18+ is required. Current version: $(node -v)"
        exit 1
    fi
    
    # Check npm
    if ! command_exists npm; then
        print_error "npm is not installed."
        exit 1
    fi
    
    # Check Python
    if ! command_exists python3; then
        print_error "Python 3.9+ is not installed. Please install Python first."
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    if [ "$(echo "$PYTHON_VERSION < 3.9" | bc -l)" -eq 1 ]; then
        print_error "Python 3.9+ is required. Current version: $PYTHON_VERSION"
        exit 1
    fi
    
    # Check pip
    if ! command_exists pip3; then
        print_error "pip3 is not installed."
        exit 1
    fi
    
    # Check Docker (optional)
    if command_exists docker; then
        print_success "Docker is available"
    else
        print_warning "Docker is not installed. You can install it for containerized deployment."
    fi
    
    # Check Git
    if ! command_exists git; then
        print_error "Git is not installed."
        exit 1
    fi
    
    print_success "All system requirements met!"
}

# Function to create directory structure
create_directories() {
    print_status "Creating directory structure..."
    
    mkdir -p backend/{api/{routes,controllers,middleware},services,utils,database}
    mkdir -p ai-agent/{core,integrations,utils,prompts}
    mkdir -p whatsapp-bot/{handlers,flows}
    mkdir -p dashboard/{src/{components,pages,context,utils,styles},public}
    mkdir -p docs
    mkdir -p scripts
    mkdir -p logs
    mkdir -p uploads
    mkdir -p tests
    
    print_success "Directory structure created!"
}

# Function to install Node.js dependencies
install_node_dependencies() {
    print_status "Installing Node.js dependencies..."
    
    # Install main dependencies
    npm install
    
    # Install dashboard dependencies
    if [ -d "dashboard" ]; then
        cd dashboard
        npm install
        cd ..
    fi
    
    print_success "Node.js dependencies installed!"
}

# Function to install Python dependencies
install_python_dependencies() {
    print_status "Installing Python dependencies..."
    
    # Create virtual environment
    python3 -m venv venv
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install dependencies
    if [ -f "ai-agent/requirements.txt" ]; then
        pip install -r ai-agent/requirements.txt
    fi
    
    # Deactivate virtual environment
    deactivate
    
    print_success "Python dependencies installed!"
}

# Function to setup database
setup_database() {
    print_status "Setting up database..."
    
    # Check if PostgreSQL is installed
    if ! command_exists psql; then
        print_warning "PostgreSQL is not installed. Please install it manually:"
        echo "  Ubuntu/Debian: sudo apt-get install postgresql postgresql-contrib"
        echo "  macOS: brew install postgresql"
        echo "  Windows: Download from https://www.postgresql.org/download/windows/"
        return
    fi
    
    # Create database
    if command_exists createdb; then
        createdb shaymee 2>/dev/null || print_warning "Database 'shaymee' already exists"
    else
        print_warning "Please create database 'shaymee' manually"
    fi
    
    print_success "Database setup completed!"
}

# Function to setup Redis
setup_redis() {
    print_status "Setting up Redis..."
    
    # Check if Redis is installed
    if ! command_exists redis-server; then
        print_warning "Redis is not installed. Please install it manually:"
        echo "  Ubuntu/Debian: sudo apt-get install redis-server"
        echo "  macOS: brew install redis"
        echo "  Windows: Download from https://redis.io/download"
        return
    fi
    
    # Start Redis if not running
    if ! pgrep redis-server > /dev/null; then
        print_status "Starting Redis server..."
        redis-server --daemonize yes
    fi
    
    print_success "Redis setup completed!"
}

# Function to create environment file
create_env_file() {
    print_status "Creating environment configuration..."
    
    if [ ! -f ".env" ]; then
        cp env.example .env
        print_success "Environment file created from template!"
        print_warning "Please update .env file with your actual configuration values"
    else
        print_warning "Environment file already exists"
    fi
}

# Function to setup Git hooks
setup_git_hooks() {
    print_status "Setting up Git hooks..."
    
    # Create pre-commit hook
    cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# Pre-commit hook for Shaymee AI Agent

echo "Running pre-commit checks..."

# Run linting
npm run lint

# Run tests
npm test

echo "Pre-commit checks completed!"
EOF
    
    chmod +x .git/hooks/pre-commit
    
    print_success "Git hooks configured!"
}

# Function to create Docker configuration
create_docker_config() {
    print_status "Creating Docker configuration..."
    
    # Create Dockerfile for backend
    cat > backend/Dockerfile << 'EOF'
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .

EXPOSE 3000

CMD ["npm", "start"]
EOF
    
    # Create Dockerfile for AI agent
    cat > ai-agent/Dockerfile << 'EOF'
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8001

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
EOF
    
    # Create docker-compose.yml
    cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "3000:3000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/shaymee
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    volumes:
      - ./logs:/app/logs
      - ./uploads:/app/uploads

  ai-agent:
    build: ./ai-agent
    ports:
      - "8001:8001"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DATABASE_URL=postgresql://user:pass@db:5432/shaymee
    depends_on:
      - db
      - redis

  whatsapp-bot:
    build: ./whatsapp-bot
    ports:
      - "3002:3002"
    environment:
      - WHATSAPP_TOKEN=${WHATSAPP_TOKEN}
      - AI_AGENT_URL=http://ai-agent:8001
    depends_on:
      - ai-agent

  dashboard:
    build: ./dashboard
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://localhost:3000
    depends_on:
      - backend

  db:
    image: postgres:14
    environment:
      - POSTGRES_DB=shaymee
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
EOF
    
    print_success "Docker configuration created!"
}

# Function to create startup scripts
create_startup_scripts() {
    print_status "Creating startup scripts..."
    
    # Create development startup script
    cat > start-dev.sh << 'EOF'
#!/bin/bash

echo "Starting Shaymee AI Agent in development mode..."

# Start all services
npm run dev &

# Wait for services to start
sleep 10

echo "Services started!"
echo "Backend: http://localhost:3000"
echo "AI Agent: http://localhost:8001"
echo "WhatsApp Bot: http://localhost:3002"
echo "Dashboard: http://localhost:3000"

# Keep script running
wait
EOF
    
    chmod +x start-dev.sh
    
    # Create production startup script
    cat > start-prod.sh << 'EOF'
#!/bin/bash

echo "Starting Shaymee AI Agent in production mode..."

# Build and start with Docker Compose
docker-compose up -d

echo "Services started!"
echo "Backend: http://localhost:3000"
echo "AI Agent: http://localhost:8001"
echo "WhatsApp Bot: http://localhost:3002"
echo "Dashboard: http://localhost:3000"
EOF
    
    chmod +x start-prod.sh
    
    print_success "Startup scripts created!"
}

# Function to run tests
run_tests() {
    print_status "Running tests..."
    
    # Run Node.js tests
    npm test
    
    # Run Python tests (if available)
    if [ -d "ai-agent" ]; then
        cd ai-agent
        source ../venv/bin/activate
        python -m pytest tests/ -v
        deactivate
        cd ..
    fi
    
    print_success "Tests completed!"
}

# Function to display final instructions
display_final_instructions() {
    echo ""
    echo "========================================"
    echo "SHAYMEE AI AGENT - SETUP COMPLETED!"
    echo "========================================"
    echo ""
    echo "Next steps:"
    echo "1. Update .env file with your configuration values"
    echo "2. Configure your APIs:"
    echo "   - OpenAI API Key"
    echo "   - WhatsApp Business API"
    echo "   - Temu API"
    echo "   - Correos de Costa Rica API"
    echo "   - SINPE API"
    echo ""
    echo "3. Start the application:"
    echo "   Development: ./start-dev.sh"
    echo "   Production:  ./start-prod.sh"
    echo ""
    echo "4. Access the services:"
    echo "   - Backend API: http://localhost:3000"
    echo "   - AI Agent: http://localhost:8001"
    echo "   - Dashboard: http://localhost:3000"
    echo "   - WhatsApp Bot: http://localhost:3002"
    echo ""
    echo "5. Documentation:"
    echo "   - Technical Architecture: docs/TECHNICAL_ARCHITECTURE.md"
    echo "   - API Documentation: http://localhost:8001/docs"
    echo ""
    echo "For support, check the README.md file or contact the development team."
    echo ""
}

# Main setup function
main() {
    echo "========================================"
    echo "SHAYMEE AI AGENT - SETUP SCRIPT"
    echo "========================================"
    echo ""
    
    # Check requirements
    check_requirements
    
    # Create directories
    create_directories
    
    # Install dependencies
    install_node_dependencies
    install_python_dependencies
    
    # Setup services
    setup_database
    setup_redis
    
    # Create configuration files
    create_env_file
    create_docker_config
    create_startup_scripts
    
    # Setup Git hooks
    setup_git_hooks
    
    # Run tests
    run_tests
    
    # Display final instructions
    display_final_instructions
    
    print_success "Setup completed successfully!"
}

# Run main function
main "$@" 