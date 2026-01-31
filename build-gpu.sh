#!/bin/bash
# PhotoMatch GPU Build and Test Commands

echo "=========================================="
echo "PhotoMatch - GPU Version Build Script"
echo "=========================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check NVIDIA driver
echo -e "\n${YELLOW}1. Checking NVIDIA Driver...${NC}"
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
    echo -e "${GREEN}✓ NVIDIA Driver detected${NC}"
else
    echo -e "${RED}✗ NVIDIA Driver not found${NC}"
    echo "Please install NVIDIA drivers first"
    exit 1
fi

# Check Docker
echo -e "\n${YELLOW}2. Checking Docker...${NC}"
if command -v docker &> /dev/null; then
    docker --version
    echo -e "${GREEN}✓ Docker detected${NC}"
else
    echo -e "${RED}✗ Docker not found${NC}"
    exit 1
fi

# Check NVIDIA Container Toolkit
echo -e "\n${YELLOW}3. Checking NVIDIA Container Toolkit...${NC}"
if docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi &> /dev/null; then
    echo -e "${GREEN}✓ NVIDIA Container Toolkit working${NC}"
else
    echo -e "${RED}✗ NVIDIA Container Toolkit not working${NC}"
    echo "Please install: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html"
    exit 1
fi

# Build and start
echo -e "\n${YELLOW}4. Building and starting services...${NC}"
docker-compose down
docker-compose up --build -d

# Wait for services
echo -e "\n${YELLOW}5. Waiting for services to start...${NC}"
sleep 10

# Check backend logs
echo -e "\n${YELLOW}6. Checking backend logs for GPU...${NC}"
docker logs photomatch-backend 2>&1 | grep -i "gpu\|cuda" | tail -5

# Run GPU test
echo -e "\n${YELLOW}7. Running GPU performance test...${NC}"
docker exec photomatch-backend python scripts/test_gpu.py

echo -e "\n${GREEN}=========================================="
echo "Setup Complete!"
echo "==========================================${NC}"
echo ""
echo "Frontend: http://localhost:3000"
echo "Backend:  http://localhost:8001"
echo "Docs:     http://localhost:8001/docs"
echo ""
echo "Monitor GPU: watch -n 1 nvidia-smi"
echo "View logs:   docker logs -f photomatch-backend"
echo ""
