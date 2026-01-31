#!/bin/bash
# Run PhotoMatch backend with GPU support

echo "Starting PhotoMatch with GPU support..."

# Stop existing containers
docker-compose down

# Start postgres first
docker-compose up -d postgres

# Wait for postgres
echo "Waiting for PostgreSQL..."
sleep 10

# Start backend with GPU
docker rm -f photomatch-backend 2>/dev/null || true
docker run -d \
  --name photomatch-backend \
  --gpus all \
  -p 8001:8001 \
  -e DATABASE_URL=postgresql://postgres:postgres@photomatch-postgres:5432/photomatch \
  -e IMAGES_FOLDER=/app/data/images \
  -e NVIDIA_VISIBLE_DEVICES=all \
  -e NVIDIA_DRIVER_CAPABILITIES=compute,utility \
  -v "$(pwd)/backend/data/images:/app/data/images" \
  -v photomatch_insightface_models:/root/.insightface \
  --network photomatch_default \
  --restart unless-stopped \
  --security-opt seccomp:unconfined \
  photomatch_backend:latest

# Start frontend
docker-compose up -d frontend

echo ""
echo "Services started!"
echo "Frontend: http://localhost:3000"
echo "Backend:  http://localhost:8001"
echo "Docs:     http://localhost:8001/docs"
echo ""
echo "Check GPU usage: docker exec photomatch-backend nvidia-smi"
echo "View logs:       docker logs -f photomatch-backend"
