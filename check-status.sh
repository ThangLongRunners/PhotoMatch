#!/bin/bash
# Quick status check for PhotoMatch GPU setup

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  PhotoMatch GPU Status Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check GPU
echo -e "\n${YELLOW}1. GPU Status:${NC}"
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
    echo -e "${GREEN}✓ GPU Available${NC}"
else
    echo -e "${RED}✗ No GPU Found${NC}"
fi

# Check Docker
echo -e "\n${YELLOW}2. Docker Status:${NC}"
if docker ps &> /dev/null; then
    echo -e "${GREEN}✓ Docker Running${NC}"
else
    echo -e "${RED}✗ Docker Not Running${NC}"
fi

# Check Containers
echo -e "\n${YELLOW}3. PhotoMatch Containers:${NC}"
docker ps -a --filter name=photomatch --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Check GPU in Docker
echo -e "\n${YELLOW}4. Docker GPU Access:${NC}"
if docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi &> /dev/null; then
    echo -e "${GREEN}✓ GPU Accessible from Docker${NC}"
else
    echo -e "${RED}✗ GPU Not Accessible from Docker${NC}"
fi

# Check Backend GPU
echo -e "\n${YELLOW}5. Backend GPU Status:${NC}"
if docker ps | grep -q photomatch-backend; then
    if docker exec photomatch-backend nvidia-smi &> /dev/null; then
        echo -e "${GREEN}✓ Backend has GPU access${NC}"
        docker logs photomatch-backend 2>&1 | grep -i "gpu\|cuda" | tail -3
    else
        echo -e "${RED}✗ Backend cannot access GPU${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Backend not running${NC}"
fi

# URLs
echo -e "\n${YELLOW}6. Application URLs:${NC}"
if docker ps | grep -q photomatch-frontend; then
    echo -e "${GREEN}Frontend:${NC} http://localhost:3000"
fi
if docker ps | grep -q photomatch-backend; then
    echo -e "${GREEN}Backend:${NC}  http://localhost:8001"
    echo -e "${GREEN}API Docs:${NC} http://localhost:8001/docs"
fi

echo -e "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
