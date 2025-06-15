"""
アプリケーション設定管理

@description 環境変数や設定値を一元管理するモジュール
Pydantic Settings を使用して型安全な設定管理を実現

@author InfuMatch Development Team
@version 1.0.0
"""

import os
from datetime import datetime
from functools import lru_cache
from typing import List, Optional, Union
from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    アプリケーション設定クラス
    
    環境変数から設定を読み込み、デフォルト値と型チェックを提供
    """
    
    # -----------------------------------------------------------------------------
    # 基本設定
    # -----------------------------------------------------------------------------
    APP_NAME: str = Field(default="YouTube Influencer Matching Agent", description="アプリケーション名")
    VERSION: str = Field(default="1.0.0", description="アプリケーションバージョン")
    ENVIRONMENT: str = Field(default="development", description="実行環境 (development/staging/production)")
    DEBUG: bool = Field(default=True, description="デバッグモード")
    
    # サーバー設定
    HOST: str = Field(default="0.0.0.0", description="サーバーホスト")
    PORT: int = Field(default=8000, description="サーバーポート")
    RELOAD: bool = Field(default=True, description="自動リロード（開発時のみ）")
    
    # ログ設定
    LOG_LEVEL: str = Field(default="INFO", description="ログレベル")
    ENABLE_MONITORING: bool = Field(default=True, description="監視機能の有効化")
    
    # ドキュメント設定
    ENABLE_DOCS: bool = Field(default=True, description="API ドキュメントの有効化")
    
    # -----------------------------------------------------------------------------
    # Google Cloud 設定
    # -----------------------------------------------------------------------------
    GOOGLE_CLOUD_PROJECT_ID: Optional[str] = Field(default="hackathon-462905", description="Google Cloud プロジェクトID")
    GOOGLE_CLOUD_REGION: str = Field(default="asia-northeast1", description="Google Cloud リージョン")
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = Field(default=None, description="サービスアカウントキーファイルパス")
    
    # Firestore 設定
    FIRESTORE_DATABASE_ID: str = Field(default="(default)", description="Firestore データベースID")
    
    # BigQuery 設定
    BIGQUERY_DATASET: str = Field(default="youtube_influencers", description="BigQuery データセット名")
    
    # Vertex AI 設定
    VERTEX_AI_ENDPOINT: str = Field(
        default="https://asia-northeast1-aiplatform.googleapis.com",
        description="Vertex AI エンドポイント"
    )
    AGENTSPACE_PROJECT_ID: Optional[str] = Field(default="hackathon-462905", description="Google Agentspace プロジェクトID")
    AGENTSPACE_LOCATION: str = Field(default="asia-northeast1", description="Agentspace ロケーション")
    
    # Gemini API 設定
    GEMINI_API_KEY: Optional[str] = Field(default=None, description="Gemini API キー")
    GEMINI_MODEL: str = Field(default="gemini-1.5-pro", description="使用する Gemini モデル")
    
    # -----------------------------------------------------------------------------
    # 外部API設定
    # -----------------------------------------------------------------------------
    # YouTube Data API
    YOUTUBE_API_KEY: Optional[str] = Field(default=None, description="YouTube Data API キー")
    YOUTUBE_QUOTA_LIMIT: int = Field(default=10000, description="YouTube API 1日あたりクォータ上限")
    YOUTUBE_RATE_LIMIT_PER_SECOND: int = Field(default=10, description="YouTube API 秒あたりリクエスト制限")
    
    # SendGrid（メール送信）
    SENDGRID_API_KEY: Optional[str] = Field(default=None, description="SendGrid API キー")
    FROM_EMAIL: str = Field(default="noreply@infumatch.com", description="送信者メールアドレス")
    FROM_NAME: str = Field(default="InfuMatch Team", description="送信者名")
    
    # -----------------------------------------------------------------------------
    # セキュリティ設定
    # -----------------------------------------------------------------------------
    # JWT設定
    JWT_SECRET_KEY: Optional[str] = Field(default="development-secret-key", description="JWT シークレットキー")
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT アルゴリズム")
    JWT_EXPIRY: int = Field(default=3600, description="JWT 有効期限（秒）")
    
    # CORS設定
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "https://infumatch.vercel.app"],
        description="CORS 許可オリジン"
    )
    
    # 信頼できるホスト（本番環境）
    ALLOWED_HOSTS: List[str] = Field(
        default=["localhost", "127.0.0.1", "*.run.app", "*.vercel.app"],
        description="許可されたホスト"
    )
    
    # レート制限
    RATE_LIMIT_PER_MINUTE: int = Field(default=100, description="API レート制限（リクエスト/分）")
    
    # -----------------------------------------------------------------------------
    # データベース・キャッシュ設定
    # -----------------------------------------------------------------------------
    # Redis（オプション）
    REDIS_URL: Optional[str] = Field(default=None, description="Redis URL")
    CACHE_TTL: int = Field(default=3600, description="キャッシュ有効期限（秒）")
    
    # -----------------------------------------------------------------------------
    # バックアップ・運用設定
    # -----------------------------------------------------------------------------
    BACKUP_BUCKET: Optional[str] = Field(default=None, description="バックアップ用 Cloud Storage バケット")
    BACKUP_FREQUENCY: str = Field(default="daily", description="バックアップ頻度")
    
    # -----------------------------------------------------------------------------
    # テスト・開発設定
    # -----------------------------------------------------------------------------
    USE_TEST_DATA: bool = Field(default=False, description="テストデータの使用")
    MOCK_EXTERNAL_APIS: bool = Field(default=False, description="外部API のモック使用")
    
    class Config:
        """Pydantic 設定"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        
    # -----------------------------------------------------------------------------
    # バリデーター
    # -----------------------------------------------------------------------------
    
    @validator("ENVIRONMENT")
    def validate_environment(cls, v):
        """環境設定のバリデーション"""
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}")
        return v
    
    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        """ログレベルのバリデーション"""
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {allowed}")
        return v.upper()
    
    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        """CORS オリジンの解析"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("ALLOWED_HOSTS", pre=True)
    def parse_allowed_hosts(cls, v):
        """許可ホストの解析"""
        if isinstance(v, str):
            return [host.strip() for host in v.split(",")]
        return v
    
    # -----------------------------------------------------------------------------
    # プロパティ
    # -----------------------------------------------------------------------------
    
    @property
    def is_development(self) -> bool:
        """開発環境かどうか"""
        return self.ENVIRONMENT == "development"
    
    @property
    def is_production(self) -> bool:
        """本番環境かどうか"""
        return self.ENVIRONMENT == "production"
    
    @property
    def database_url(self) -> str:
        """データベースURL（将来的なRDB対応）"""
        # 現在はFirestoreを使用するため、プロジェクトIDを返す
        return f"firestore://{self.GOOGLE_CLOUD_PROJECT_ID}"
    
    # -----------------------------------------------------------------------------
    # ユーティリティメソッド
    # -----------------------------------------------------------------------------
    
    def get_current_timestamp(self) -> str:
        """現在のタイムスタンプ（ISO形式）"""
        return datetime.utcnow().isoformat() + "Z"
    
    def get_cors_config(self) -> dict:
        """CORS設定の辞書を取得"""
        return {
            "allow_origins": self.CORS_ORIGINS,
            "allow_credentials": True,
            "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["*"],
        }
    
    def get_redis_config(self) -> Optional[dict]:
        """Redis設定の辞書を取得"""
        if not self.REDIS_URL:
            return None
        return {
            "url": self.REDIS_URL,
            "encoding": "utf-8",
            "decode_responses": True,
        }
    
    def get_youtube_api_config(self) -> dict:
        """YouTube API設定の辞書を取得"""
        return {
            "api_key": self.YOUTUBE_API_KEY,
            "quota_limit": self.YOUTUBE_QUOTA_LIMIT,
            "rate_limit_per_second": self.YOUTUBE_RATE_LIMIT_PER_SECOND,
        }
    
    def get_sendgrid_config(self) -> dict:
        """SendGrid設定の辞書を取得"""
        return {
            "api_key": self.SENDGRID_API_KEY,
            "from_email": self.FROM_EMAIL,
            "from_name": self.FROM_NAME,
        }
    
    def get_vertex_ai_config(self) -> dict:
        """Vertex AI設定の辞書を取得"""
        return {
            "project_id": self.GOOGLE_CLOUD_PROJECT_ID,
            "location": self.GOOGLE_CLOUD_REGION,
            "endpoint": self.VERTEX_AI_ENDPOINT,
        }
    
    def get_agentspace_config(self) -> dict:
        """Google Agentspace設定の辞書を取得"""
        return {
            "project_id": self.AGENTSPACE_PROJECT_ID,
            "location": self.AGENTSPACE_LOCATION,
        }


@lru_cache()
def get_settings() -> Settings:
    """
    設定インスタンスをキャッシュ付きで取得
    
    LRU キャッシュにより、同じ設定インスタンスを再利用
    環境変数の読み込みコストを削減
    
    Returns:
        Settings: アプリケーション設定
    """
    return Settings()


# 設定インスタンスをモジュールレベルでエクスポート
settings = get_settings()


def validate_required_settings() -> None:
    """
    必要な設定項目の検証
    
    アプリケーション起動時に呼び出して、
    必須の環境変数が設定されているかチェック
    
    Raises:
        ValueError: 必須設定が不足している場合
    """
    required_settings = [
        "GOOGLE_CLOUD_PROJECT_ID",
        "YOUTUBE_API_KEY",
        "SENDGRID_API_KEY",
        "JWT_SECRET_KEY",
        "AGENTSPACE_PROJECT_ID",
    ]
    
    missing_settings = []
    for setting in required_settings:
        value = getattr(settings, setting, None)
        if not value:
            missing_settings.append(setting)
    
    if missing_settings:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing_settings)}\n"
            f"Please check your .env file or environment configuration."
        )


def print_config_summary() -> None:
    """
    設定の概要を出力（デバッグ用）
    
    機密情報（APIキーなど）はマスクして表示
    """
    print("🔧 Application Configuration Summary:")
    print(f"   Environment: {settings.ENVIRONMENT}")
    print(f"   Debug Mode: {settings.DEBUG}")
    print(f"   API Documentation: {settings.ENABLE_DOCS}")
    print(f"   Monitoring: {settings.ENABLE_MONITORING}")
    print(f"   Google Cloud Project: {settings.GOOGLE_CLOUD_PROJECT_ID}")
    print(f"   YouTube API Key: {'*' * 8 + settings.YOUTUBE_API_KEY[-4:] if settings.YOUTUBE_API_KEY else 'Not Set'}")
    print(f"   CORS Origins: {settings.CORS_ORIGINS}")
    print("=" * 50)


if __name__ == "__main__":
    # 設定テスト用のスクリプト
    try:
        validate_required_settings()
        print_config_summary()
        print("✅ Configuration validation passed!")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        exit(1)