#!/bin/bash
# Stop both observability and application stacks

echo "🛑 Stopping all services..."
echo ""

# Stop application stack
echo "Stopping application stack..."
docker-compose down

# Stop observability stack
echo "Stopping observability stack..."
cd cirrostrats-backend
docker-compose -f observability/docker-compose.observability-only.yml down
cd ..

echo ""
echo "✅ All services stopped!"
echo ""
echo "To remove the shared network:"
echo "  docker network rm cirrostrats-network"
echo ""
