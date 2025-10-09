#!/bin/bash
# Start both observability and application stacks

set -e

echo "🚀 Starting Cirrostrats Full Stack"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Step 1: Create shared network (if it doesn't exist)
echo -e "${BLUE}📡 Creating shared network...${NC}"
docker network create cirrostrats-network 2>/dev/null || echo "  Network already exists"

# Step 2: Start observability stack
echo ""
echo -e "${BLUE}🔍 Starting Observability Stack...${NC}"
cd cirrostrats-backend
docker-compose -f observability/docker-compose.observability-only.yml up -d
cd ..

# Step 3: Wait for observability to be healthy
echo ""
echo -e "${YELLOW}⏳ Waiting for observability services (30s)...${NC}"
sleep 30

# Step 4: Start application stack
echo ""
echo -e "${BLUE}🎯 Starting Application Stack (Frontend, Backend, Nginx)...${NC}"
docker-compose up -d

# Step 5: Wait for backend to start
echo ""
echo -e "${YELLOW}⏳ Waiting for backend (20s)...${NC}"
sleep 20

# Step 6: Health checks
echo ""
echo "📊 Service Health Check:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

check_service() {
    local name=$1
    local url=$2
    local port=$3

    if curl -sf "$url" > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} $name (http://localhost:$port)"
    else
        echo -e "  ${YELLOW}⚠${NC} $name (http://localhost:$port) - NOT READY YET"
    fi
}

echo ""
echo "Application Services:"
check_service "Backend API       " "http://localhost:8000/health" "8000"
check_service "Frontend          " "http://localhost:5173" "5173"
check_service "Nginx             " "http://localhost:80" "80"

echo ""
echo "Observability Services:"
check_service "Grafana           " "http://localhost:3000/api/health" "3000"
check_service "Prometheus        " "http://localhost:9090/-/healthy" "9090"
check_service "Loki              " "http://localhost:3100/ready" "3100"
check_service "Tempo             " "http://localhost:3200/ready" "3200"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Step 7: Show URLs
echo "🌐 Access Points:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "  ${GREEN}Application${NC}"
echo "    Frontend       → http://localhost:5173"
echo "    Backend API    → http://localhost:8000"
echo "    Nginx          → http://localhost:80"
echo ""
echo -e "  ${GREEN}Observability${NC}"
echo "    Grafana        → http://localhost:3000  (admin/admin)"
echo "    Prometheus     → http://localhost:9090"
echo "    Loki           → http://localhost:3100"
echo "    Tempo          → http://localhost:3200"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo -e "${GREEN}✅ All stacks are running!${NC}"
echo ""
echo "To stop:"
echo "  Application:    docker-compose down"
echo "  Observability:  cd cirrostrats-backend && docker-compose -f observability/docker-compose.observability-only.yml down"
echo ""
