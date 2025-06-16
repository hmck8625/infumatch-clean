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

### YouTube Channel Collection Workflow
```bash
# 1. Famous Japanese Channels (エンタメ系チャンネル収集)
python3 simple_famous_collection.py      # 30-40チャンネル収集
python3 save_to_databases.py            # Firestore・BigQuery保存

# 2. Business Channels (ビジネス系チャンネル収集)
python3 manual_business_channels.py     # 30チャンネル作成
python3 save_to_databases.py           # 自動的にビジネス系を優先保存

# 3. Comedian Channels (芸人系チャンネル収集)
python3 comedian_channels.py           # 20チャンネル作成
python3 save_to_databases.py          # 自動的に芸人系を優先保存

# 4. Custom Category Collection Template
# カテゴリ別収集用テンプレート：
# - beauty_channels.py (美容・コスメ系)
# - gaming_channels.py (ゲーム実況系)  
# - cooking_channels.py (料理・グルメ系)
# - tech_channels.py (テクノロジー系)
# - lifestyle_channels.py (ライフスタイル系)
```

### Collection Scripts Architecture
```bash
# YouTube API Quota Management (1日10,000 units制限)
# - search().list(): 100 units/回
# - channels().list(): 1 unit/回
# - 効率的収集: 検索1回で平均2チャンネル取得

# Manual Collection (APIクォータ節約・高品質データ)
manual_business_channels.py    # 手動30チャンネル (0 units使用)
comedian_channels.py          # 手動20チャンネル (0 units使用)

# API Collection (自動収集・大量データ)
simple_famous_collection.py   # API38チャンネル (~2,000 units使用)
collect_more_business_channels.py  # API拡張収集 (~2,100 units使用)

# Database Integration
save_to_databases.py         # 統一保存スクリプト
# - 自動ファイル検出: comedian_ > business_ > famous_ > その他
# - Firestore: influencersコレクション (重複は更新)
# - BigQuery: infumatch_data.influencers (新規追加)
```

### Collection Data Quality Standards
```bash
# Required Fields for All Channels
- channel_id: YouTube Channel ID (必須・ユニーク)
- channel_title: チャンネル名
- description: チャンネル説明
- subscriber_count: 登録者数 (最低5,000人以上)
- video_count: 動画数
- view_count: 総視聴回数
- thumbnail_url: サムネイルURL (100%取得率目標)
- category: カテゴリ分類 (ビジネス/エンターテイメント等)
- is_verified: カテゴリ適合性フラグ
- engagement_estimate: エンゲージメント率推定
- collected_at: 収集日時
- country: 'JP' (日本チャンネル限定)
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

# Deploy backend to Cloud Run (RECOMMENDED: lightweight method)
cd cloud-run-backend && gcloud run deploy infumatch-backend --source . --region asia-northeast1 --allow-unauthenticated --port 8000

# Deploy backend to Cloud Run (ALTERNATIVE: full Docker build - may timeout)
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

### Backend Deployment Strategy
There are two backend deployment approaches:

#### 1. **Lightweight Backend** (RECOMMENDED)
- **Location**: `cloud-run-backend/main.py` (380 lines, minimal implementation)
- **Command**: `cd cloud-run-backend && gcloud run deploy infumatch-backend --source . --region asia-northeast1 --allow-unauthenticated --port 8000`
- **Advantages**: 
  - Fast deployment (2-3 minutes)
  - No Docker build required
  - Minimal dependencies
  - Proven to work without timeouts
- **Use case**: Quick iterations, hackathon development, MVP deployment

#### 2. **Full Backend** (Docker-based)
- **Location**: Full `backend/` directory with all features
- **Command**: `./deploy/scripts/deploy-backend.sh`
- **Issues**: 
  - Docker build timeouts (large dependencies)
  - ARM64 vs x86_64 architecture conflicts
  - Longer deployment time (10+ minutes)
- **Use case**: Production deployment with full feature set

### Deployment Troubleshooting
- **If Docker build times out**: Use lightweight backend method instead
- **If "exec format error"**: Architecture mismatch, use `--source .` deployment
- **If dependencies missing**: Check `cloud-run-backend/main.py` has required imports

### Other Deployment Notes
- Frontend can be deployed to Vercel or as static assets
- Cloud Functions deploy separately with their own requirements.txt
- Infrastructure managed with Terraform (deploy/terraform/)

## Production URLs

### Current Deployment Status
- **Frontend**: https://infumatch-clean.vercel.app/
- **Backend API**: https://infumatch-backend-269567634217.asia-northeast1.run.app/
- **API Documentation**: https://infumatch-backend-269567634217.asia-northeast1.run.app/docs

### API Endpoints
```
GET  /                                    # Health check
GET  /health                              # System health
GET  /api/v1/influencers                  # Influencer list (Firestore)
GET  /api/v1/influencers/{id}             # Influencer details
POST /api/v1/negotiation/initial-contact  # Generate initial email
POST /api/v1/negotiation/continue         # Continue negotiation with custom instructions
GET  /api/v1/negotiation/generate         # Generate negotiation message
POST /api/v1/ai/recommendations           # AI matching recommendations
GET  /api/v1/ai/agents/status             # AI agent status
POST /api/v1/collaboration-proposal       # Generate collaboration proposal
```

## Key Features Implementation Status

### ✅ Completed Features
1. **AI Agent Status Visualization** (`frontend/app/messages/page.tsx`)
   - Real-time processing steps display with timestamps
   - AI thinking process (`reasoning`) shown in UI
   - 7-stage detailed status tracking

2. **Custom Instructions Integration** (`cloud-run-backend/main.py:281-343`)
   - Input field: "📝 カスタム指示（任意）" in messages page
   - Supports: "値引きしたい", "積極的", "丁寧", "急ぎ" keywords
   - Applied to API response content automatically

3. **Company Settings Integration**
   - Company name, products, negotiation settings reflected in replies
   - Data sourced from `/settings` page context

4. **Multi-Agent Negotiation System**
   - Negotiation lifecycle tracking (10 stages)
   - Sentiment analysis (-1.0 to 1.0)
   - Success probability calculation
   - Strategic opportunity assessment

### 🔄 Architecture Details

#### Frontend State Management
```typescript
// Agent status with reasoning display
interface ProcessingStep {
  time: string;
  status: string;
  detail: string;
  reasoning?: string; // AI思考過程
}

const updateAgentStatus = (status: string, detail?: string, reasoning?: string) => {
  // Updates UI with detailed AI processing steps
}
```

#### Backend Custom Instructions Processing
```python
# Custom instructions handling in continue_negotiation
custom_instructions = request.context.get("custom_instructions", "")
company_settings = request.context.get("company_settings", {})

# Keywords detection and response modification
if "値引き" in custom_instructions:
    base_response += "\n\n料金についても、可能な限りご希望に沿えるよう検討させていただきます。"
```

## Data Sources and Database Schema

### Firestore Collections
- **`influencers`**: YouTube creator data with AI analysis
  - Fields: `channel_title`, `subscriber_count`, `engagement_metrics`, `contact_info`
  - AI analysis: `category_tags`, `audience_analysis`, `brand_safety_score`

### Mock Data Fallback
- Used when Firestore unavailable
- Includes 5 sample influencers across gaming, cooking, fitness, beauty, tech categories

## Testing and Quality Assurance

### API Testing
```bash
# Test custom instructions functionality
curl -X POST https://infumatch-backend-269567634217.asia-northeast1.run.app/api/v1/negotiation/continue \
  -H "Content-Type: application/json" \
  -d '{"conversation_history": [], "new_message": "予算について", "context": {"custom_instructions": "値引きしたい"}}'

# Test health endpoint
curl https://infumatch-backend-269567634217.asia-northeast1.run.app/health
```

### Frontend Testing
- Jest unit tests for components
- Playwright E2E tests for user flows
- Real-time status updates testing

## Security and Authentication

### Environment Variables (Production)
```
NEXT_PUBLIC_API_URL=https://infumatch-backend-269567634217.asia-northeast1.run.app
NEXTAUTH_URL=https://infumatch-clean.vercel.app
GOOGLE_CLOUD_PROJECT_ID=hackathon-462905
```

### Google Cloud IAM
- Cloud Run service account with Firestore access
- Secret Manager for API keys (YouTube, Gemini)

## Performance Considerations

### Cloud Run Configuration
- Memory: 2Gi
- CPU: 2
- Max instances: 10
- Timeout: 300s
- Concurrency: 80

### Frontend Optimization
- Client-side filtering for search performance
- SWR caching for API responses
- Lazy loading for heavy components

## Hackathon Requirements

Must use Google Cloud computing services (✅ Cloud Run, Cloud Functions) and AI services (✅ Vertex AI, Gemini API). Repository must remain public until August 5th. Final deliverables include working deployed URL and Zenn article with demo video.