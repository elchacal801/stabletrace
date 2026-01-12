# Multi-stage build for full-stack app

# Stage 1: Build Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app-frontend
COPY app/package*.json ./
RUN npm ci
COPY app/ ./
RUN npm run build

# Stage 2: Final Image (Python + Built Frontend)
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY api/ ./api/
COPY ingest/ ./ingest/
COPY warehouse/ ./warehouse/

# Copy built frontend from Stage 1
COPY --from=frontend-builder /app-frontend/.next/static/ ./.next/static/
COPY --from=frontend-builder /app-frontend/public/ ./public/
# Note: Next.js standalone output would be better for pure production, 
# but for simplicity in this hybrid setup, we normally run them separately 
# or use a unified runner.
#
# SIMPLIFIED STRATEGY for easy deployment:
# We will just run the FastAPI backend in this container.
# The user usually deploys Frontend (Vercel) and Backend (Railway) separately.
#
# HOWEVER, to keep it in ONE repo/container for simple demos:
# We can't easily run both Next.js server AND FastAPI in one container without a supervisor.
#
# LET'S REVERT TO A BACKEND-ONLY DOCKERFILE.
# The user should deploy the 'app' folder to Vercel/Netlify.
# And this Dockerfile to Railway/Render for the API.

EXPOSE 8000

# Run API
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
