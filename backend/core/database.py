"""
データベース接続・初期化モジュール

@description Firestore とのコネクション管理、初期化処理
Google Cloud Firestore を使用したデータベース操作の基盤

@author InfuMatch Development Team
@version 1.0.0
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timezone

from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
from google.oauth2 import service_account
import google.auth

from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# グローバル変数でFirestoreクライアントを保持
_firestore_client: Optional[firestore.Client] = None


class FirestoreClient:
    """
    Firestore クライアントのラッパークラス
    
    接続管理、エラーハンドリング、ヘルパーメソッドを提供
    シングルトンパターンで実装
    """
    
    _instance: Optional['FirestoreClient'] = None
    _client: Optional[firestore.Client] = None
    
    def __new__(cls) -> 'FirestoreClient':
        """シングルトンパターンの実装"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初期化処理"""
        if self._client is None:
            self._initialize_client()
    
    def _initialize_client(self) -> None:
        """
        Firestore クライアントの初期化
        
        環境に応じて認証方法を切り替え
        - 開発環境: サービスアカウントキー
        - 本番環境: Cloud Run の自動認証
        """
        try:
            if settings.GOOGLE_APPLICATION_CREDENTIALS and settings.is_development:
                # 開発環境: サービスアカウントキーを使用
                logger.info("🔑 Initializing Firestore with service account credentials")
                credentials = service_account.Credentials.from_service_account_file(
                    settings.GOOGLE_APPLICATION_CREDENTIALS
                )
                self._client = firestore.Client(
                    project=settings.GOOGLE_CLOUD_PROJECT_ID,
                    credentials=credentials,
                    database=settings.FIRESTORE_DATABASE_ID
                )
            else:
                # 本番環境: Cloud Run の自動認証
                logger.info("🔑 Initializing Firestore with default credentials")
                self._client = firestore.Client(
                    project=settings.GOOGLE_CLOUD_PROJECT_ID,
                    database=settings.FIRESTORE_DATABASE_ID
                )
            
            logger.info("✅ Firestore client initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Firestore client: {e}")
            raise
    
    @property
    def client(self) -> firestore.Client:
        """Firestore クライアントを取得"""
        if self._client is None:
            self._initialize_client()
        return self._client
    
    async def test_connection(self) -> bool:
        """
        データベース接続をテスト
        
        Returns:
            bool: 接続成功時 True
        """
        try:
            # テスト用のドキュメントを読み取り
            doc_ref = self.client.collection('_health_check').document('test')
            doc_ref.set({
                'timestamp': firestore.SERVER_TIMESTAMP,
                'status': 'ok'
            })
            
            # 書き込み後すぐに読み取り
            doc = doc_ref.get()
            if doc.exists:
                logger.info("✅ Firestore connection test passed")
                # テストドキュメントを削除
                doc_ref.delete()
                return True
            else:
                logger.warning("⚠️ Firestore connection test failed: document not found")
                return False
                
        except Exception as e:
            logger.error(f"❌ Firestore connection test failed: {e}")
            return False


class DatabaseCollections:
    """
    データベースコレクション定義
    
    Firestore のコレクション名とスキーマを一元管理
    """
    
    # コレクション名定義
    INFLUENCERS = "influencers"
    COMPANIES = "companies"
    CAMPAIGNS = "campaigns"
    NEGOTIATIONS = "negotiations"
    MESSAGES = "messages"
    ANALYTICS = "analytics"
    SYSTEM_LOGS = "system_logs"
    
    # サブコレクション
    CAMPAIGN_MATCHES = "matches"
    NEGOTIATION_MESSAGES = "messages"
    ANALYTICS_DAILY = "daily_stats"
    
    @classmethod
    def get_all_collections(cls) -> List[str]:
        """すべてのコレクション名を取得"""
        return [
            cls.INFLUENCERS,
            cls.COMPANIES,
            cls.CAMPAIGNS,
            cls.NEGOTIATIONS,
            cls.MESSAGES,
            cls.ANALYTICS,
            cls.SYSTEM_LOGS,
        ]


class DatabaseSchemas:
    """
    データベーススキーマ定義
    
    各コレクションのドキュメント構造を定義
    型チェックとデフォルト値を提供
    """
    
    @staticmethod
    def influencer_schema() -> Dict[str, Any]:
        """インフルエンサー情報のスキーマ"""
        return {
            # 基本情報
            "channel_id": "",  # YouTube チャンネルID
            "channel_name": "",
            "custom_url": "",
            "description": "",
            "thumbnail_url": "",
            
            # 統計情報
            "subscriber_count": 0,
            "video_count": 0,
            "view_count": 0,
            "engagement_rate": 0.0,
            
            # 分析結果
            "categories": [],  # カテゴリ一覧
            "topics": [],     # トピック一覧
            "target_audience": {},  # ターゲット層分析
            "content_style": "",    # コンテンツスタイル
            
            # 連絡先情報
            "emails": [],     # 抽出されたメールアドレス
            "social_links": {},  # SNSリンク
            "website": "",
            
            # ビジネス情報
            "collaboration_rate": 0.0,  # コラボ実績率
            "average_price": 0,         # 平均料金
            "availability": True,       # 対応可能状況
            "preferred_categories": [], # 希望カテゴリ
            
            # システム情報
            "created_at": None,
            "updated_at": None,
            "last_analyzed": None,
            "data_quality_score": 0.0,  # データ品質スコア
            "status": "active",  # active, inactive, blocked
        }
    
    @staticmethod
    def company_schema() -> Dict[str, Any]:
        """企業情報のスキーマ"""
        return {
            # 基本情報
            "company_name": "",
            "industry": "",
            "company_size": "",  # startup, small, medium, large
            "website": "",
            "description": "",
            
            # 担当者情報
            "contact_person": "",
            "contact_email": "",
            "contact_phone": "",
            
            # マーケティング情報
            "target_audience": {},
            "marketing_budget": 0,
            "preferred_content_types": [],
            "brand_guidelines": {},
            
            # システム情報
            "user_id": "",  # 認証ユーザーID
            "subscription_plan": "free",  # free, basic, pro, enterprise
            "api_key": "",
            "created_at": None,
            "updated_at": None,
            "status": "active",
        }
    
    @staticmethod
    def campaign_schema() -> Dict[str, Any]:
        """キャンペーン情報のスキーマ"""
        return {
            # 基本情報
            "campaign_name": "",
            "description": "",
            "company_id": "",
            "product_name": "",
            "campaign_type": "",  # product_review, brand_awareness, tutorial
            
            # 予算・条件
            "budget_min": 0,
            "budget_max": 0,
            "target_influencer_count": 0,
            "target_subscriber_range": {"min": 1000, "max": 100000},
            
            # スケジュール
            "start_date": None,
            "end_date": None,
            "content_deadline": None,
            
            # 要件
            "content_requirements": {},
            "deliverables": [],
            "target_categories": [],
            "target_demographics": {},
            
            # 進捗
            "status": "draft",  # draft, active, paused, completed, cancelled
            "matched_influencers": 0,
            "active_negotiations": 0,
            "completed_deals": 0,
            
            # システム情報
            "created_at": None,
            "updated_at": None,
        }
    
    @staticmethod
    def negotiation_schema() -> Dict[str, Any]:
        """交渉情報のスキーマ"""
        return {
            # 関連ID
            "campaign_id": "",
            "influencer_id": "",
            "company_id": "",
            
            # 交渉状況
            "status": "initiated",  # initiated, in_progress, agreed, declined, expired
            "current_stage": "initial_contact",  # initial_contact, price_negotiation, terms_agreement
            
            # 提案内容
            "proposed_price": 0,
            "final_price": 0,
            "deliverables": [],
            "timeline": {},
            "special_terms": {},
            
            # AI エージェント情報
            "ai_agent_id": "",
            "agent_personality": "",
            "conversation_style": "",
            
            # メッセージ統計
            "message_count": 0,
            "last_message_at": None,
            "response_time_avg": 0,  # 平均応答時間（分）
            
            # システム情報
            "created_at": None,
            "updated_at": None,
            "expires_at": None,
        }
    
    @staticmethod
    def message_schema() -> Dict[str, Any]:
        """メッセージ情報のスキーマ"""
        return {
            # 関連ID
            "negotiation_id": "",
            "sender_type": "",  # ai_agent, influencer, company
            "sender_id": "",
            
            # メッセージ内容
            "content": "",
            "message_type": "text",  # text, offer, acceptance, decline
            "attachments": [],
            
            # AI 生成情報
            "generated_by_ai": False,
            "ai_model": "",
            "generation_prompt": "",
            "confidence_score": 0.0,
            
            # 状態管理
            "read_status": False,
            "read_at": None,
            "response_required": False,
            
            # システム情報
            "created_at": None,
            "ip_address": "",
            "user_agent": "",
        }


async def init_firestore() -> FirestoreClient:
    """
    Firestore の初期化
    
    接続テストとインデックス作成を実行
    
    Returns:
        FirestoreClient: 初期化済みクライアント
    """
    logger.info("🚀 Initializing Firestore database...")
    
    # クライアント作成
    db_client = FirestoreClient()
    
    # 接続テスト
    connection_ok = await db_client.test_connection()
    if not connection_ok:
        raise Exception("Failed to establish Firestore connection")
    
    # インデックス作成（本番環境では事前に作成推奨）
    if settings.is_development:
        await create_indexes(db_client)
    
    # 初期データ投入（開発環境のみ）
    if settings.USE_TEST_DATA and settings.is_development:
        await insert_test_data(db_client)
    
    logger.info("✅ Firestore initialization completed")
    return db_client


async def create_indexes(db_client: FirestoreClient) -> None:
    """
    Firestore インデックスの作成
    
    複合クエリで必要なインデックスを作成
    本番環境では Firebase CLI で事前作成を推奨
    
    Args:
        db_client: Firestore クライアント
    """
    logger.info("📋 Creating Firestore indexes...")
    
    try:
        # 注意: Firestore の複合インデックスは実際には Firebase CLI や
        # Google Cloud Console で作成する必要があります
        # ここでは開発時のクエリテスト用の準備のみ
        
        # インフルエンサー検索用
        influencer_indexes = [
            ["subscriber_count", "status"],
            ["categories", "subscriber_count"],
            ["engagement_rate", "availability"],
            ["created_at", "status"],
        ]
        
        # キャンペーン検索用
        campaign_indexes = [
            ["company_id", "status"],
            ["status", "created_at"],
            ["target_categories", "status"],
        ]
        
        logger.info("📋 Index definitions prepared (manual creation required)")
        
    except Exception as e:
        logger.warning(f"⚠️ Index creation failed: {e}")


async def insert_test_data(db_client: FirestoreClient) -> None:
    """
    テストデータの投入
    
    開発・デモ用のサンプルデータを作成
    
    Args:
        db_client: Firestore クライアント
    """
    logger.info("🧪 Inserting test data...")
    
    try:
        client = db_client.client
        
        # サンプルインフルエンサー
        sample_influencers = [
            {
                **DatabaseSchemas.influencer_schema(),
                "channel_id": "UC_sample_1",
                "channel_name": "料理系YouTuber みさき",
                "description": "簡単レシピと料理のコツを紹介！お仕事のご相談は business@example.com まで",
                "subscriber_count": 8500,
                "video_count": 120,
                "view_count": 850000,
                "engagement_rate": 5.2,
                "categories": ["料理", "ライフスタイル"],
                "emails": [{"email": "business@example.com", "priority": 5}],
                "collaboration_rate": 0.8,
                "average_price": 50000,
                "created_at": firestore.SERVER_TIMESTAMP,
                "updated_at": firestore.SERVER_TIMESTAMP,
            },
            {
                **DatabaseSchemas.influencer_schema(),
                "channel_id": "UC_sample_2", 
                "channel_name": "テックレビュー タカシ",
                "description": "最新ガジェットレビュー！コラボ依頼: tech.review@example.com",
                "subscriber_count": 15000,
                "video_count": 80,
                "view_count": 1200000,
                "engagement_rate": 6.8,
                "categories": ["テクノロジー", "ガジェット"],
                "emails": [{"email": "tech.review@example.com", "priority": 5}],
                "collaboration_rate": 0.9,
                "average_price": 80000,
                "created_at": firestore.SERVER_TIMESTAMP,
                "updated_at": firestore.SERVER_TIMESTAMP,
            }
        ]
        
        # サンプル企業
        sample_company = {
            **DatabaseSchemas.company_schema(),
            "company_name": "サンプル株式会社",
            "industry": "食品・飲料",
            "company_size": "medium",
            "website": "https://sample-company.com",
            "contact_email": "marketing@sample-company.com",
            "target_audience": {"age": "20-40", "gender": "female", "interests": ["料理", "健康"]},
            "marketing_budget": 500000,
            "preferred_content_types": ["product_review", "tutorial"],
            "subscription_plan": "pro",
            "created_at": firestore.SERVER_TIMESTAMP,
            "updated_at": firestore.SERVER_TIMESTAMP,
        }
        
        # データ投入
        batch = client.batch()
        
        for i, influencer in enumerate(sample_influencers):
            doc_ref = client.collection(DatabaseCollections.INFLUENCERS).document(f"sample_{i+1}")
            batch.set(doc_ref, influencer)
        
        company_ref = client.collection(DatabaseCollections.COMPANIES).document("sample_company")
        batch.set(company_ref, sample_company)
        
        await batch.commit()
        
        logger.info("✅ Test data inserted successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to insert test data: {e}")


def get_firestore_client() -> FirestoreClient:
    """
    Firestore クライアントを取得
    
    依存性注入で使用
    
    Returns:
        FirestoreClient: クライアントインスタンス
    """
    return FirestoreClient()


class DatabaseHelper:
    """
    データベース操作のヘルパークラス
    
    共通的な CRUD 操作とクエリ機能を提供
    """
    
    def __init__(self, client: FirestoreClient):
        self.client = client.client
    
    async def create_document(
        self, 
        collection: str, 
        data: Dict[str, Any], 
        document_id: Optional[str] = None
    ) -> str:
        """
        ドキュメントを作成
        
        Args:
            collection: コレクション名
            data: ドキュメントデータ
            document_id: ドキュメントID（省略時は自動生成）
            
        Returns:
            str: 作成されたドキュメントID
        """
        try:
            # タイムスタンプを自動追加
            data.update({
                "created_at": firestore.SERVER_TIMESTAMP,
                "updated_at": firestore.SERVER_TIMESTAMP,
            })
            
            if document_id:
                doc_ref = self.client.collection(collection).document(document_id)
                doc_ref.set(data)
                return document_id
            else:
                doc_ref = self.client.collection(collection).add(data)
                return doc_ref[1].id
                
        except Exception as e:
            logger.error(f"Failed to create document in {collection}: {e}")
            raise
    
    async def get_document(self, collection: str, document_id: str) -> Optional[Dict[str, Any]]:
        """
        ドキュメントを取得
        
        Args:
            collection: コレクション名
            document_id: ドキュメントID
            
        Returns:
            Optional[Dict]: ドキュメントデータ（存在しない場合はNone）
        """
        try:
            doc_ref = self.client.collection(collection).document(document_id)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                data["id"] = doc.id
                return data
            return None
            
        except Exception as e:
            logger.error(f"Failed to get document {document_id} from {collection}: {e}")
            raise
    
    async def update_document(
        self, 
        collection: str, 
        document_id: str, 
        data: Dict[str, Any]
    ) -> bool:
        """
        ドキュメントを更新
        
        Args:
            collection: コレクション名
            document_id: ドキュメントID
            data: 更新データ
            
        Returns:
            bool: 更新成功時 True
        """
        try:
            # 更新タイムスタンプを自動追加
            data["updated_at"] = firestore.SERVER_TIMESTAMP
            
            doc_ref = self.client.collection(collection).document(document_id)
            doc_ref.update(data)
            return True
            
        except Exception as e:
            logger.error(f"Failed to update document {document_id} in {collection}: {e}")
            return False
    
    async def delete_document(self, collection: str, document_id: str) -> bool:
        """
        ドキュメントを削除
        
        Args:
            collection: コレクション名
            document_id: ドキュメントID
            
        Returns:
            bool: 削除成功時 True
        """
        try:
            doc_ref = self.client.collection(collection).document(document_id)
            doc_ref.delete()
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete document {document_id} from {collection}: {e}")
            return False
    
    async def query_documents(
        self,
        collection: str,
        filters: Optional[List[tuple]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        ドキュメントをクエリ
        
        Args:
            collection: コレクション名
            filters: フィルター条件のリスト [(field, operator, value), ...]
            order_by: ソート対象フィールド
            limit: 取得件数制限
            
        Returns:
            List[Dict]: マッチしたドキュメントのリスト
        """
        try:
            query = self.client.collection(collection)
            
            # フィルター適用
            if filters:
                for field, operator, value in filters:
                    query = query.where(filter=FieldFilter(field, operator, value))
            
            # ソート適用
            if order_by:
                query = query.order_by(order_by)
            
            # 件数制限
            if limit:
                query = query.limit(limit)
            
            # クエリ実行
            docs = query.stream()
            
            results = []
            for doc in docs:
                data = doc.to_dict()
                data["id"] = doc.id
                results.append(data)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to query documents from {collection}: {e}")
            raise