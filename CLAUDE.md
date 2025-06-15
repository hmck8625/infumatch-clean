# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

InfuMatch is a YouTube Influencer Matching Agent that automatically matches micro-influencers with companies and handles negotiations through AI agents. This is a hackathon project for Google Cloud Japan AI Hackathon Vol.2 with the theme "AIエージェント、創造性の頂へ" (AI Agents, to the Peak of Creativity).

## Architecture Overview

This is a cloud-native application with a clear separation of concerns:

- **Frontend**: Next.js 14 with App Router, TypeScript, Tailwind CSS, shadcn/ui components
- **Backend**: FastAPI with Python 3.11+, deployed on Google Cloud Run
- **AI Agents**: Multi-agent system using Vertex AI and Gemini API for data processing, recommendations, and negotiations
- **Database**: Firestore for NoSQL data, BigQuery for analytics
- **Cloud Infrastructure**: Google Cloud services (Cloud Run, Cloud Functions, Cloud Scheduler, etc.)

The system implements a sophisticated AI agent architecture with specialized agents for data preprocessing, influencer-brand matching, and automated negotiation.

## Common Development Commands

### Environment Setup
```bash
# Start local development environment (starts both frontend and backend)
./start-local.sh

# Stop all local services
./stop-local.sh

# View logs
tail -f backend.log    # Backend logs
tail -f frontend.log   # Frontend logs
```

### AI Analysis and Data Collection
```bash
# AI-enhanced YouTube data collection (with real-time analysis)
python3 backend/enhanced_youtube_collector.py

# Test AI analysis functionality
python3 backend/test_ai_analysis.py

# Multi-category data collection (existing data collector)
python3 backend/multi_category_collector.py

# Register collected data to databases
python3 backend/register_collected_data.py
```

### Frontend Development (cd frontend/)
```bash
# Development server
npm run dev

# Build and type checking
npm run build
npm run type-check

# Linting and formatting
npm run lint
npm run lint:fix
npm run format

# Testing
npm run test              # Unit tests with Jest
npm run test:watch        # Watch mode
npm run test:coverage     # Coverage report
npm run test:e2e          # E2E tests with Playwright
```

### Backend Development (cd backend/)
```bash
# Setup virtual environment (first time)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Code quality
black .              # Format code
isort .              # Sort imports
flake8 .             # Lint
mypy .               # Type checking

# Testing
pytest               # Run tests
pytest --cov        # With coverage
```

### Google Cloud Setup
```bash
# Login and set project
gcloud auth login
gcloud config set project hackathon-462905
gcloud auth application-default login

# Deploy backend to Cloud Run
./deploy/scripts/deploy-backend.sh

# Deploy Cloud Functions
cd cloud_functions && ./deploy.sh
```

## Key Technologies and Dependencies

### Frontend Stack
- **Next.js 14**: App Router with TypeScript
- **UI Components**: shadcn/ui built on Radix UI primitives
- **Styling**: Tailwind CSS with animations
- **Forms**: React Hook Form with Zod validation
- **Data Fetching**: SWR for client-side data fetching, Axios for HTTP
- **Charts**: Recharts for data visualization
- **Testing**: Jest + Testing Library + Playwright

### Backend Stack
- **FastAPI**: High-performance async web framework
- **Pydantic v2**: Data validation and settings management
- **Google Cloud SDKs**: Firestore, BigQuery, Vertex AI, Cloud Functions
- **AI/ML**: google-generativeai (Gemini 1.5 Flash), vertexai for AI agent functionality
- **Authentication**: JWT with PyJWT, Google Auth
- **Task Queue**: Celery with Redis
- **Testing**: pytest with async support

### AI Agent System
The backend includes a sophisticated multi-agent system:
- **Base Agent** (`backend/services/ai_agents/base_agent.py`): Common functionality for all AI agents
- **AI Channel Analyzer** (`backend/services/ai_channel_analyzer.py`): Real-time comprehensive channel analysis using Gemini API
- **Enhanced Collector** (`backend/enhanced_youtube_collector.py`): YouTube data collection with integrated AI analysis
- **Preprocessor Agent**: Data cleaning and preparation for YouTube influencer data
- **Recommendation Agent**: Influencer-brand matching using ML algorithms
- **Negotiation Agent**: Automated deal negotiation between influencers and brands

#### 🤖 AI Real-time Analysis Features
- **Category Auto-tagging**: Primary + sub-categories with confidence scores
- **Channel Summarization**: Structured analysis of content style, expertise, entertainment value
- **Product Matching**: Intelligent recommendation of optimal product categories with detailed reasoning
- **Audience Analysis**: Demographics prediction, engagement levels, reach potential assessment
- **Brand Safety**: Comprehensive risk assessment and compliance scoring
- **Processing**: Real-time analysis during data collection with 0.7-0.9 confidence levels

## Environment Configuration

### Required Environment Variables
- Backend: Copy `.env.example` to `.env` and configure Google Cloud credentials
- Frontend: Copy `frontend/.env.local.example` to `frontend/.env.local` and set API URLs
- The start-local.sh script automatically creates these files if they don't exist

### Google Cloud Services Used
- **Cloud Run**: Backend API hosting
- **Firestore**: Primary NoSQL database
- **BigQuery**: Analytics and reporting
- **Vertex AI**: Machine learning model hosting
- **Cloud Functions**: Scheduled tasks and event processing
- **Cloud Scheduler**: Cron jobs with Pub/Sub
- **YouTube Data API v3**: Influencer data collection
- **Secret Manager**: Secure credential storage

## Development Workflow

1. Use `./start-local.sh` to start both frontend and backend services
2. Frontend runs on http://localhost:3000
3. Backend API runs on http://localhost:8000 with docs at /docs
4. Make changes and test locally before deploying
5. Use `./stop-local.sh` to stop all services

## Testing Strategy

- **Frontend**: Unit tests with Jest, E2E tests with Playwright
- **Backend**: Unit tests with pytest, async support enabled
- **Integration**: API tests using FastAPI's test client
- **Cloud Functions**: Local testing with functions-framework

## Deployment Notes

- Backend deploys to Google Cloud Run via Docker containers
- Frontend can be deployed to Vercel or as static assets
- Cloud Functions deploy separately with their own requirements.txt
- Infrastructure managed with Terraform (deploy/terraform/)

## Hackathon Requirements

Must use Google Cloud computing services (✅ Cloud Run, Cloud Functions) and AI services (✅ Vertex AI, Gemini API). Repository must remain public until August 5th. Final deliverables include working deployed URL and Zenn article with demo video.