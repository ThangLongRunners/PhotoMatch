# PhotoMatch

Face image search web application powered by AI. Upload a photo containing a face and find similar faces from your image database using state-of-the-art face recognition and vector similarity search.

## 🚀 Features

- **AI-Powered Face Detection**: Automatic face detection using InsightFace
- **Vector Similarity Search**: Fast and accurate search using PostgreSQL + pgvector
- **Smart Face Selection**: Automatically selects the largest face in each image
- **Real-time Search**: Search through thousands of faces in milliseconds
- **Event Tagging**: Organize photos by events or categories
- **Duplicate Detection**: Automatically skip duplicate images using SHA1 hashing
- **Modern UI**: Clean, responsive React interface
- **Dockerized**: Easy deployment with Docker Compose

## 🏗️ Architecture

### Tech Stack

- **Backend**: Python FastAPI
- **Frontend**: React + TypeScript (Vite)
- **Database**: PostgreSQL 15 + pgvector extension
- **Face AI**: InsightFace (buffalo_l model) with PyTorch + CUDA
- **GPU Acceleration**: NVIDIA CUDA 12.1 + cuDNN 8
- **Storage**: Local filesystem served via FastAPI StaticFiles
- **Deployment**: Docker + Docker Compose with GPU support

### Core Components

#### Backend Services
- **Face Detector**: Detects faces and selects the largest one
- **Face Embedder**: Generates normalized 512-dim embeddings
- **Ingest Service**: Processes and stores images with face embeddings
- **Search Service**: Performs vector similarity search
- **Image Store**: Manages image paths and URLs

#### API Endpoints
- `GET /health` - Health check
- `POST /ingest/folder` - Ingest images from a folder
- `POST /search` - Search for similar faces by image upload

#### Database Schema
- **photos** table: Image metadata (path, SHA1, dimensions, event tag)
- **faces** table: Face bounding boxes and 512-dim vector embeddings
- **HNSW index**: Fast cosine similarity search on embeddings

## 📋 Prerequisites

- Docker & Docker Compose
- **NVIDIA GPU with CUDA support** (recommended for best performance)
- NVIDIA Container Toolkit (for GPU support)
- 6GB+ GPU VRAM recommended (or 4GB+ RAM for CPU mode)
- 2GB+ disk space for models and data

### GPU Support (Recommended)

This application is optimized for GPU acceleration:
- **5-10x faster** face detection and embedding
- Uses PyTorch with CUDA for maximum accuracy
- No ONNX quantization - full model precision
- See [GPU_SETUP.md](GPU_SETUP.md) for installation instructions

## 🛠️ Installation & Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd PhotoMatch
```

### 2. Start with Docker Compose

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

This will start:
- PostgreSQL with pgvector (port 5432)
- Backend API (port 8001)
- Frontend UI (port 3000)

### 3. Initialize Database

The database schema is automatically initialized on first run via the migration scripts in `backend/migrations/`.

### 4. Access the Application

- **Frontend UI**: http://localhost:3000
- **Backend API**: http://localhost:8001
- **API Docs**: http://localhost:8001/docs

## 📸 Usage

### Option 1: Web Interface

1. Open http://localhost:3000
2. Upload an image containing a face
3. Adjust search parameters:
   - **Max Results**: Number of results to return (10-100)
   - **Similarity Threshold**: Minimum match percentage (0-100%)
4. View results with similarity scores

### Option 2: API Direct

#### Ingest Images

```bash
curl -X POST "http://localhost:8001/ingest/folder" \
  -H "Content-Type: application/json" \
  -d '{
    "path": "data/images",
    "recursive": true,
    "event_tag": "my_event"
  }'
```

#### Search by Image

```bash
curl -X POST "http://localhost:8001/search?top_k=30&threshold=0.6" \
  -F "file=@/path/to/query_image.jpg"
```

### Option 3: Python Script

```bash
# Copy images to backend/data/images/
cp -r /path/to/photos backend/data/images/

# Run ingest script inside container
docker-compose exec backend python scripts/ingest_folder.py data/images my_event

# Or with local Python environment
cd backend
python scripts/ingest_folder.py data/images my_event
```

## 🔧 Development Setup

### Backend Development

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your settings

# Run database migrations manually if needed
psql -U postgres -d photomatch -f migrations/001_init.sql
psql -U postgres -d photomatch -f migrations/002_indexes.sql

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Set environment variables
cp .env.example .env

# Run development server
npm run dev
```

## 📊 Database Schema

### Photos Table
```sql
CREATE TABLE photos (
    id UUID PRIMARY KEY,
    path TEXT NOT NULL,
    sha1 TEXT NOT NULL UNIQUE,
    width INTEGER NOT NULL,
    height INTEGER NOT NULL,
    event_tag TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### Faces Table
```sql
CREATE TABLE faces (
    id UUID PRIMARY KEY,
    photo_id UUID NOT NULL REFERENCES photos(id),
    x1 INTEGER NOT NULL,
    y1 INTEGER NOT NULL,
    x2 INTEGER NOT NULL,
    y2 INTEGER NOT NULL,
    embedding VECTOR(512) NOT NULL,
    is_primary BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### Vector Index (HNSW)
```sql
CREATE INDEX idx_faces_embedding_hnsw 
ON faces 
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

## 🧠 How It Works

### Ingestion Pipeline

1. **Scan Folder**: Recursively find all image files
2. **Hash Check**: Compute SHA1 and skip duplicates
3. **Load Image**: Read image and get dimensions
4. **Detect Faces**: Find all faces in the image
5. **Select Largest**: Choose the face with biggest bounding box
6. **Generate Embedding**: Create normalized 512-dim vector
7. **Store**: Save metadata to photos table and embedding to faces table

### Search Pipeline

1. **Upload Image**: User uploads query image via web UI or API
2. **Detect Face**: Find largest face in query image
3. **Generate Embedding**: Create normalized 512-dim vector
4. **Vector Search**: Use pgvector cosine similarity search
5. **Filter**: Apply similarity threshold
6. **Rank**: Order results by similarity score (descending)
7. **Return**: Send image URLs and scores to frontend

### Face Processing Rules

- **Multiple Faces**: Only the largest face (by bounding box area) is used
- **No Face Detected**: Image is skipped during ingest, search returns empty
- **Embedding Normalization**: All embeddings are L2-normalized for cosine similarity
- **Primary Face Flag**: Each photo has one primary face (is_primary=true)

## 🐳 Docker Configuration

### Services

- **postgres**: PostgreSQL 15 with pgvector extension
- **backend**: FastAPI application with InsightFace
- **frontend**: React SPA served by Nginx

### Volumes

- `postgres_data`: Persistent database storage
- `insightface_models`: Cached AI models (downloaded on first run)
- `./backend/data/images`: Image storage (mounted to backend)

### Environment Variables

#### Backend
- `DATABASE_URL`: PostgreSQL connection string
- `IMAGES_FOLDER`: Path to image storage directory

#### Frontend
- `VITE_API_URL`: Backend API base URL

## 🔍 Performance

### Search Speed
- **10K faces**: ~50-100ms query time
- **100K faces**: ~200-500ms query time
- **1M faces**: ~1-2s query time

### Optimization Tips

1. **HNSW Index**: Already configured for optimal performance
2. **Increase `m` parameter**: Better recall, slower build time
3. **Increase `ef_construction`**: Better accuracy, slower indexing
4. **Add more RAM**: pgvector benefits from memory for vector index
5. **SSD Storage**: Faster database operations

## 🧪 Testing

```bash
# Test health endpoint
curl http://localhost:8001/health

# Check database connection
docker-compose exec postgres psql -U postgres -d photomatch -c "SELECT COUNT(*) FROM photos;"

# View face count
docker-compose exec postgres psql -U postgres -d photomatch -c "SELECT COUNT(*) FROM faces WHERE is_primary = true;"
```

## 🛡️ Production Considerations

1. **Security**:
   - Change default PostgreSQL credentials
   - Use environment variables for secrets
   - Enable HTTPS/SSL
   - Restrict CORS origins
   - Add authentication/authorization

2. **Scalability**:
   - Use managed PostgreSQL (AWS RDS, Google Cloud SQL)
   - Add Redis for caching
   - Use S3/object storage for images
   - Deploy backend with multiple workers
   - Add load balancer

3. **Monitoring**:
   - Add logging aggregation (ELK, CloudWatch)
   - Set up metrics (Prometheus, Grafana)
   - Configure alerts for errors and performance

4. **Backup**:
   - Regular PostgreSQL backups
   - Image storage backups
   - Test restore procedures

## 📝 License

See [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## 📧 Support

For issues and questions, please open a GitHub issue.

---

Built with ❤️ using FastAPI, React, PostgreSQL, and InsightFace
FaceBibSearch is a computer vision system for searching and retrieving event photos using face recognition and bib number detection.   It is designed for large-scale sports events such as marathons, where participants can quickly find their photos from thousands of images.
