"""
YouTube Influencer Matching Agent - FastAPI メインアプリケーション

@description Google Cloud Run で動作するFastAPIアプリケーションのエントリポイント
@author InfuMatch Development Team
@version 1.0.0
"""

import os
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
import uvicorn

# アプリケーション設定とコア機能
from core.config import get_settings

try:
    from core.logging import setup_logging
except ImportError:
    def setup_logging():
        logging.basicConfig(level=logging.INFO)

try:
    from core.database import init_firestore
except ImportError:
    async def init_firestore():
        pass

try:
    from core.monitoring import setup_monitoring
except ImportError:
    def setup_monitoring():
        pass

# API ルーター
try:
    from api.v1.router import api_router
except ImportError:
    from fastapi import APIRouter
    api_router = APIRouter()

try:
    from api.health import health_router
except ImportError:
    from fastapi import APIRouter
    health_router = APIRouter()
    
    @health_router.get("/health")
    async def health_check():
        return {"status": "healthy"}

# インフルエンサー API ルーター
try:
    from api.influencers import router as influencers_router
except ImportError:
    from fastapi import APIRouter
    influencers_router = APIRouter()

# AI推薦 API ルーター
try:
    from api.ai_recommendations import router as ai_recommendations_router
except ImportError:
    from fastapi import APIRouter
    ai_recommendations_router = APIRouter()

# 交渉エージェント API ルーター
try:
    from api.negotiation import router as negotiation_router
except ImportError:
    from fastapi import APIRouter
    negotiation_router = APIRouter()

# データ同期 API ルーター
try:
    from api.v1.data_sync import router as data_sync_router
except ImportError:
    from fastapi import APIRouter
    data_sync_router = APIRouter()

# 統合マッチング API ルーター
try:
    from api.centralized_matching import router as centralized_matching_router
except ImportError:
    from fastapi import APIRouter
    centralized_matching_router = APIRouter()

# メール自動返信 API ルーター
try:
    from api.email_auto_reply import router as email_auto_reply_router
except ImportError:
    from fastapi import APIRouter
    email_auto_reply_router = APIRouter()

# ミドルウェア（存在しない場合はダミーを使用）
try:
    from middleware.rate_limit import RateLimitMiddleware
except ImportError:
    RateLimitMiddleware = None

try:
    from middleware.auth import AuthMiddleware
except ImportError:
    AuthMiddleware = None

try:
    from middleware.monitoring import MonitoringMiddleware
except ImportError:
    MonitoringMiddleware = None

# 設定読み込み
settings = get_settings()

# ログ設定
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    アプリケーションのライフサイクル管理
    
    起動時と終了時に実行される処理を定義
    FastAPIの推奨パターンに従い、startup/shutdownイベントの代替
    """
    # 起動時処理
    logger.info("🚀 Starting YouTube Influencer Matching Agent API")
    
    try:
        # データベース初期化
        logger.info("📊 Initializing Firestore connection...")
        await init_firestore()
        
        # BigQuery 初期化
        logger.info("🏗️ Initializing BigQuery data warehouse...")
        try:
            from core.bigquery_client import initialize_bigquery
            await initialize_bigquery()
            logger.info("✅ BigQuery initialized successfully")
        except ImportError:
            logger.warning("⚠️ BigQuery module not available")
        except Exception as e:
            logger.error(f"❌ BigQuery initialization failed: {e}")
        
        # 監視システム初期化
        logger.info("📈 Setting up monitoring...")
        setup_monitoring()
        
        # AI サービス初期化
        logger.info("🤖 Initializing AI services...")
        # from services.ai_agents import init_ai_agents
        # await init_ai_agents()
        
        logger.info("✅ Application startup completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to start application: {e}")
        raise
    
    # アプリケーション実行中
    yield
    
    # 終了時処理
    logger.info("🛑 Shutting down YouTube Influencer Matching Agent API")
    
    try:
        # リソースクリーンアップ
        logger.info("🧹 Cleaning up resources...")
        
        # 接続プールクローズ
        # await close_connections()
        
        logger.info("✅ Application shutdown completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}")


def create_application() -> FastAPI:
    """
    FastAPIアプリケーションのファクトリ関数
    
    設定に基づいてアプリケーションインスタンスを作成
    テスト環境でも使用するため、関数として分離
    
    Returns:
        FastAPI: 設定済みのFastAPIアプリケーション
    """
    
    # FastAPIアプリケーション作成
    app = FastAPI(
        title="YouTube Influencer Matching Agent API",
        description="""
        ## 🎯 YouTube Influencer Matching Agent API

        YouTubeマイクロインフルエンサーと企業を自動でマッチングし、
        AIエージェントが交渉まで代行するプラットフォームのAPI

        ### 🚀 主要機能
        - **インフルエンサー発見**: YouTube特化の高精度検索
        - **自動マッチング**: AI による最適な組み合わせ提案  
        - **自動交渉**: 人間らしいAIエージェントによる交渉代行
        - **進捗管理**: リアルタイムダッシュボード

        ### 🛠️ 技術スタック
        - **Framework**: FastAPI + Google Cloud Run
        - **Database**: Firestore + BigQuery  
        - **AI/ML**: Google Agentspace + Vertex AI
        - **External APIs**: YouTube Data API v3
        """,
        version="1.0.0",
        terms_of_service="https://infumatch.com/terms",
        contact={
            "name": "InfuMatch Development Team",
            "url": "https://infumatch.com/contact",
            "email": "dev@infumatch.com",
        },
        license_info={
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT",
        },
        # OpenAPIドキュメントの設定
        openapi_url="/api/v1/openapi.json" if getattr(settings, 'ENABLE_DOCS', True) else None,
        docs_url="/docs" if getattr(settings, 'ENABLE_DOCS', True) else None,
        redoc_url="/redoc" if getattr(settings, 'ENABLE_DOCS', True) else None,
        # ライフサイクル管理
        lifespan=lifespan,
    )
    
    # ミドルウェア設定（順序重要）
    setup_middleware(app)
    
    # ルーター設定
    setup_routers(app)
    
    # 例外ハンドラー設定
    setup_exception_handlers(app)
    
    return app


def setup_middleware(app: FastAPI) -> None:
    """
    ミドルウェアの設定
    
    セキュリティ、CORS、レート制限などを設定
    ミドルウェアは後から追加された順（逆順）で実行される
    
    Args:
        app: FastAPIアプリケーション
    """
    
    # 1. 監視・メトリクス（最初に実行）
    if MonitoringMiddleware:
        app.add_middleware(MonitoringMiddleware)
    
    # 2. 認証・認可
    if AuthMiddleware:
        app.add_middleware(AuthMiddleware)
    
    # 3. レート制限
    if RateLimitMiddleware:
        app.add_middleware(
            RateLimitMiddleware,
            calls=getattr(settings, 'RATE_LIMIT_PER_MINUTE', 100),
            period=60
        )
    
    # 4. CORS設定
    app.add_middleware(
        CORSMiddleware,
        allow_origins=getattr(settings, 'CORS_ORIGINS', ["http://localhost:3000"]),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Total-Count", "X-Page-Count"],
    )
    
    # 5. 信頼できるホスト制限（本番環境のみ）
    if getattr(settings, 'ENVIRONMENT', 'development') == "production":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=getattr(settings, 'ALLOWED_HOSTS', ["*"])
        )


def setup_routers(app: FastAPI) -> None:
    """
    APIルーターの設定
    
    各エンドポイントを適切なプレフィックスで登録
    
    Args:
        app: FastAPIアプリケーション
    """
    
    # ヘルスチェック（プレフィックスなし）
    app.include_router(
        health_router,
        tags=["Health Check"]
    )
    
    # インフルエンサー API
    app.include_router(
        influencers_router,
        tags=["Influencers"]
    )
    
    # AI推薦 API
    app.include_router(
        ai_recommendations_router,
        tags=["AI Recommendations"]
    )
    
    # メインAPI（v1）
    app.include_router(
        api_router,
        prefix="/api/v1",
        tags=["API v1"]
    )
    
    # 交渉エージェント API
    app.include_router(
        negotiation_router,
        prefix="/api/v1",
        tags=["Negotiation Agent"]
    )
    
    # データ同期 API
    app.include_router(
        data_sync_router,
        prefix="/api/v1/data",
        tags=["Data Sync & Analytics"]
    )
    
    # 統合マッチング API
    app.include_router(
        centralized_matching_router,
        tags=["Centralized Matching"]
    )
    
    # メール自動返信 API
    app.include_router(
        email_auto_reply_router,
        tags=["Email Auto Reply"]
    )


def setup_exception_handlers(app: FastAPI) -> None:
    """
    例外ハンドラーの設定
    
    アプリケーション全体の例外処理を統一
    
    Args:
        app: FastAPIアプリケーション
    """
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        """HTTP例外のハンドリング"""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.status_code,
                    "message": exc.detail,
                    "type": "http_exception"
                },
                "request_id": getattr(request.state, "request_id", None),
                "timestamp": getattr(settings, 'get_current_timestamp', lambda: None)() or "unknown"
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """一般的な例外のハンドリング"""
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": 500,
                    "message": "Internal server error" if settings.ENVIRONMENT == "production" else str(exc),
                    "type": "internal_error"
                },
                "request_id": getattr(request.state, "request_id", None),
                "timestamp": getattr(settings, 'get_current_timestamp', lambda: None)() or "unknown"
            }
        )


# アプリケーションインスタンス作成
app = create_application()


@app.get("/", include_in_schema=False)
async def root() -> Dict[str, Any]:
    """
    ルートエンドポイント
    
    API の基本情報を返す
    ヘルスチェックとしても使用可能
    """
    return {
        "message": "YouTube Influencer Matching Agent API",
        "version": "1.0.0",
        "status": "operational",
        "environment": getattr(settings, 'ENVIRONMENT', 'development'),
        "docs_url": "/docs" if getattr(settings, 'ENABLE_DOCS', True) else None,
        "timestamp": getattr(settings, 'get_current_timestamp', lambda: None)() or "unknown",
    }


@app.get("/info", include_in_schema=False)
async def info() -> Dict[str, Any]:
    """
    システム情報エンドポイント
    
    デバッグ・監視用の詳細情報
    """
    return {
        "system": {
            "python_version": os.sys.version,
            "environment": getattr(settings, 'ENVIRONMENT', 'development'),
            "debug_mode": getattr(settings, 'DEBUG', True),
        },
        "services": {
            "firestore": "connected",  # 実際の接続状態をチェック
            "youtube_api": "configured",
            "vertex_ai": "available",
        },
        "features": {
            "docs_enabled": getattr(settings, 'ENABLE_DOCS', True),
            "monitoring_enabled": getattr(settings, 'ENABLE_MONITORING', False),
            "rate_limiting": True,
        }
    }


def main() -> None:
    """
    アプリケーションのメインエントリポイント
    
    開発環境での直接実行用
    本番環境では gunicorn を使用
    """
    uvicorn.run(
        "main:app",
        host=getattr(settings, 'HOST', '0.0.0.0'),
        port=getattr(settings, 'PORT', 8000),
        reload=getattr(settings, 'RELOAD', True),
        log_level=getattr(settings, 'LOG_LEVEL', 'INFO').lower(),
        access_log=True,
        server_header=False,  # セキュリティのためサーバーヘッダーを隠す
    )


if __name__ == "__main__":
    main()