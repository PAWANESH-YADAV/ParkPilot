# ParkPilot - Deployment Guide

## Prerequisites
- Docker and Docker Compose installed
- PostgreSQL (optional - if not using Docker)
- Node.js 18+
- Python 3.12+

## Local Development Setup

### 1. Backend
```bash
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows
# source venv/bin/activate  # Linux/macOS
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Update .env with your database credentials

# Initialize database
python -m app.db.init_db

# Run server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. AI Service
```bash
cd ai-service
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows
pip install -r requirements.txt
python main.py  # Runs on port 8001
```

### 3. Frontend
```bash
cd frontend
npm install
npm run dev
```

## Docker Deployment

### Full Stack with Docker Compose
```bash
# Build and start all services
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

Services available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- AI Service: http://localhost:8001
- PostgreSQL: localhost:5432

### Environment Variables
Create `.env` files in backend and ai-service directories:

#### backend/.env
```
DATABASE_URL=postgresql://user:password@host:5432/dbname
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
AI_SERVICE_URL=http://localhost:8001
```

#### frontend/.env.local
```
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=your-google-maps-key
```

## Production Deployment

### Frontend to Vercel
1. Push to GitHub repo
2. Connect repo to Vercel
3. Add environment variables in Vercel dashboard
4. Deploy!

### Backend to Railway
1. Push to GitHub
2. Connect repo to Railway
3. Add PostgreSQL service
4. Set environment variables
5. Deploy!

### AI Service
- Deploy to any Python-compatible host (Railway, Render, AWS EC2)
- Ensure you have enough resources for YOLOv8 and OCR
