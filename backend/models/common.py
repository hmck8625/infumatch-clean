"""
共通データモデル

@description 全モデルで共通して使用するベースクラスとミックスイン
Pydantic v2 を使用した型安全なデータモデル

@author InfuMatch Development Team
@version 1.0.0
"""

from datetime import datetime
from typing import Optional, Any, Dict, List
from enum import Enum

from pydantic import BaseModel as PydanticBaseModel, Field, ConfigDict
from pydantic import field_validator, model_validator


class BaseModel(PydanticBaseModel):
    """
    ベースモデルクラス
    
    全モデルの共通設定と機能を提供
    """
    
    model_config = ConfigDict(
        # JSON スキーマ生成時の設定
        json_schema_extra={
            "examples": []
        },
        # その他の設定
        validate_assignment=True,  # 代入時にバリデーション
        use_enum_values=True,      # Enum の値を使用
        extra="forbid",            # 未定義フィールドを禁止
        frozen=False,              # ミュータブル（変更可能）
        populate_by_name=True,     # エイリアス名でも populate 可能
    )
    
    def model_dump_firestore(self) -> Dict[str, Any]:
        """
        Firestore 用の辞書形式に変換
        
        Firestore に保存する際の形式に変換
        None 値を除外し、datetime を適切に処理
        
        Returns:
            Dict[str, Any]: Firestore 用辞書
        """
        data = self.model_dump(exclude_none=True)
        
        # datetime を ISO 形式文字列に変換（Firestore の場合は通常 SERVER_TIMESTAMP を使用）
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        
        return data
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換（後方互換性）"""
        return self.model_dump()


class TimestampMixin(BaseModel):
    """
    タイムスタンプ用ミックスイン
    
    作成日時・更新日時を管理
    """
    
    created_at: Optional[datetime] = Field(
        default=None,
        description="作成日時"
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        description="更新日時"
    )
    
    @field_validator('created_at', 'updated_at', mode='before')
    @classmethod
    def parse_datetime(cls, v):
        """datetime の解析"""
        if v is None:
            return v
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace('Z', '+00:00'))
        return v


class StatusMixin(BaseModel):
    """
    ステータス管理用ミックスイン
    
    共通的なステータス管理を提供
    """
    
    status: str = Field(
        default="active",
        description="ステータス"
    )
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        """ステータスのバリデーション"""
        allowed_statuses = ['active', 'inactive', 'pending', 'blocked', 'deleted']
        if v not in allowed_statuses:
            raise ValueError(f'Status must be one of: {allowed_statuses}')
        return v


class ContactInfo(BaseModel):
    """
    連絡先情報
    
    メールアドレスや SNS アカウント等
    """
    
    email: Optional[str] = Field(
        default=None,
        description="メールアドレス"
    )
    phone: Optional[str] = Field(
        default=None,
        description="電話番号"
    )
    website: Optional[str] = Field(
        default=None,
        description="ウェブサイト URL"
    )
    social_links: Dict[str, str] = Field(
        default_factory=dict,
        description="SNS リンク集"
    )
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        """メールアドレスの簡易バリデーション"""
        if v and '@' not in v:
            raise ValueError('Invalid email format')
        return v
    
    @field_validator('website')
    @classmethod
    def validate_website(cls, v):
        """ウェブサイト URL のバリデーション"""
        if v and not v.startswith(('http://', 'https://')):
            return f'https://{v}'
        return v


class TargetAudience(BaseModel):
    """
    ターゲットオーディエンス情報
    
    年齢層、性別、興味関心等のデモグラフィック情報
    """
    
    age_range: Optional[str] = Field(
        default=None,
        description="年齢層 (e.g., '20-30', '30-40')"
    )
    gender: Optional[str] = Field(
        default=None,
        description="性別 ('male', 'female', 'all')"
    )
    interests: List[str] = Field(
        default_factory=list,
        description="興味関心のリスト"
    )
    location: Optional[str] = Field(
        default=None,
        description="地域"
    )
    income_level: Optional[str] = Field(
        default=None,
        description="所得層"
    )


class ContentRequirements(BaseModel):
    """
    コンテンツ要件
    
    動画やコンテンツに関する要求事項
    """
    
    content_type: str = Field(
        description="コンテンツタイプ"
    )
    duration: Optional[str] = Field(
        default=None,
        description="動画長 (e.g., '5-10分')"
    )
    style: Optional[str] = Field(
        default=None,
        description="スタイル・トーン"
    )
    hashtags: List[str] = Field(
        default_factory=list,
        description="必須ハッシュタグ"
    )
    mentions: List[str] = Field(
        default_factory=list,
        description="メンション要求"
    )
    deliverables: List[str] = Field(
        default_factory=list,
        description="成果物リスト"
    )
    restrictions: List[str] = Field(
        default_factory=list,
        description="制限事項"
    )


class PriceRange(BaseModel):
    """
    価格範囲
    
    最小・最大価格の管理
    """
    
    min_price: int = Field(
        ge=0,
        description="最小価格"
    )
    max_price: int = Field(
        ge=0, 
        description="最大価格"
    )
    currency: str = Field(
        default="JPY",
        description="通貨"
    )
    
    @model_validator(mode='after')
    def validate_price_range(self):
        """価格範囲のバリデーション"""
        if self.min_price > self.max_price:
            raise ValueError('min_price must be less than or equal to max_price')
        return self


class Statistics(BaseModel):
    """
    統計情報
    
    各種メトリクスの管理
    """
    
    views: int = Field(default=0, ge=0, description="視聴回数")
    likes: int = Field(default=0, ge=0, description="いいね数")
    comments: int = Field(default=0, ge=0, description="コメント数")
    shares: int = Field(default=0, ge=0, description="シェア数")
    engagement_rate: float = Field(default=0.0, ge=0.0, le=100.0, description="エンゲージメント率（%）")
    
    @field_validator('engagement_rate')
    @classmethod
    def validate_engagement_rate(cls, v):
        """エンゲージメント率のバリデーション"""
        if v < 0 or v > 100:
            raise ValueError('Engagement rate must be between 0 and 100')
        return round(v, 2)


class AIAnalysis(BaseModel):
    """
    AI 分析結果
    
    AI による分析・予測結果
    """
    
    confidence_score: float = Field(
        ge=0.0, le=1.0,
        description="信頼度スコア (0.0-1.0)"
    )
    analysis_type: str = Field(
        description="分析タイプ"
    )
    results: Dict[str, Any] = Field(
        default_factory=dict,
        description="分析結果"
    )
    model_version: Optional[str] = Field(
        default=None,
        description="使用モデルバージョン"
    )
    analyzed_at: Optional[datetime] = Field(
        default=None,
        description="分析実行日時"
    )


class CompanySize(str, Enum):
    """企業規模"""
    STARTUP = "startup"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    ENTERPRISE = "enterprise"


class SubscriptionPlan(str, Enum):
    """サブスクリプションプラン"""
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class CampaignStatus(str, Enum):
    """キャンペーンステータス"""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class NegotiationStatus(str, Enum):
    """交渉ステータス"""
    INITIATED = "initiated"
    IN_PROGRESS = "in_progress"
    AGREED = "agreed"
    DECLINED = "declined"
    EXPIRED = "expired"


class MessageType(str, Enum):
    """メッセージタイプ"""
    TEXT = "text"
    OFFER = "offer"
    ACCEPTANCE = "acceptance"
    DECLINE = "decline"
    QUESTION = "question"
    SYSTEM = "system"


class ContentType(str, Enum):
    """コンテンツタイプ"""
    PRODUCT_REVIEW = "product_review"
    BRAND_AWARENESS = "brand_awareness"
    TUTORIAL = "tutorial"
    UNBOXING = "unboxing"
    COMPARISON = "comparison"
    LIFESTYLE = "lifestyle"


# 共通レスポンスモデル
class APIResponse(BaseModel):
    """
    API レスポンスの基本形式
    """
    
    success: bool = Field(description="成功フラグ")
    message: str = Field(description="メッセージ")
    data: Optional[Any] = Field(default=None, description="レスポンスデータ")
    errors: Optional[List[str]] = Field(default=None, description="エラーリスト")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="タイムスタンプ")


class PaginationParams(BaseModel):
    """
    ページネーションパラメータ
    """
    
    page: int = Field(default=1, ge=1, description="ページ番号")
    size: int = Field(default=20, ge=1, le=100, description="ページサイズ")
    
    @property
    def offset(self) -> int:
        """オフセット値を計算"""
        return (self.page - 1) * self.size


class PaginatedResponse(BaseModel):
    """
    ページネーション付きレスポンス
    """
    
    items: List[Any] = Field(description="アイテムリスト")
    total: int = Field(description="総件数")
    page: int = Field(description="現在のページ")
    size: int = Field(description="ページサイズ")
    pages: int = Field(description="総ページ数")
    
    @model_validator(mode='after')
    def calculate_pages(self):
        """総ページ数を計算"""
        if self.size > 0:
            self.pages = (self.total + self.size - 1) // self.size
        else:
            self.pages = 0
        return self