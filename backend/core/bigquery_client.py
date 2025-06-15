"""
BigQuery クライアント・スキーマ管理モジュール

@description Google BigQuery を使用したデータ分析基盤の構築
データウェアハウス、分析クエリ、レポート生成機能を提供

@author InfuMatch Development Team
@version 1.0.0
"""

import logging
from typing import Dict, List, Any, Optional, Union, Iterator
from datetime import datetime, timezone
from google.cloud import bigquery
from google.cloud.exceptions import NotFound
from google.oauth2 import service_account
import pandas as pd

from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# グローバル変数でBigQueryクライアントを保持
_bigquery_client: Optional[bigquery.Client] = None


class BigQueryTables:
    """BigQuery テーブル名の定数管理"""
    
    # インフルエンサー関連
    INFLUENCERS = "influencers"
    INFLUENCER_ANALYTICS = "influencer_analytics"
    CHANNEL_STATS = "channel_stats"
    VIDEO_PERFORMANCE = "video_performance"
    
    # 企業・キャンペーン関連
    COMPANIES = "companies"
    CAMPAIGNS = "campaigns"
    CAMPAIGN_PERFORMANCE = "campaign_performance"
    
    # 交渉・マッチング関連
    NEGOTIATIONS = "negotiations"
    MATCHES = "matches"
    MATCH_HISTORY = "match_history"
    
    # 分析・レポート関連
    DAILY_METRICS = "daily_metrics"
    TREND_ANALYSIS = "trend_analysis"
    CATEGORY_INSIGHTS = "category_insights"
    ENGAGEMENT_PATTERNS = "engagement_patterns"
    
    # システム関連
    API_USAGE = "api_usage"
    SYSTEM_EVENTS = "system_events"
    ERROR_LOGS = "error_logs"


class BigQuerySchemas:
    """BigQuery テーブルスキーマの定義"""
    
    INFLUENCERS = [
        bigquery.SchemaField("influencer_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("channel_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("channel_title", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("description", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("subscriber_count", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("video_count", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("view_count", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("category", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("country", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("language", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("contact_email", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("social_links", "JSON", mode="NULLABLE"),
        bigquery.SchemaField("ai_analysis", "JSON", mode="NULLABLE"),
        bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("updated_at", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("is_active", "BOOLEAN", mode="REQUIRED"),
    ]
    
    INFLUENCER_ANALYTICS = [
        bigquery.SchemaField("record_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("influencer_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("date", "DATE", mode="REQUIRED"),
        bigquery.SchemaField("subscriber_growth", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("view_growth", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("engagement_rate", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("avg_views_per_video", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("upload_frequency", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("trend_score", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("category_rank", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("metrics", "JSON", mode="NULLABLE"),
        bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
    ]
    
    VIDEO_PERFORMANCE = [
        bigquery.SchemaField("video_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("influencer_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("title", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("description", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("published_at", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("view_count", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("like_count", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("comment_count", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("duration", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("tags", "JSON", mode="NULLABLE"),
        bigquery.SchemaField("category_id", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("language", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("engagement_rate", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("performance_score", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
    ]
    
    CAMPAIGNS = [
        bigquery.SchemaField("campaign_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("company_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("title", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("description", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("budget", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("target_category", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("target_demographics", "JSON", mode="NULLABLE"),
        bigquery.SchemaField("requirements", "JSON", mode="NULLABLE"),
        bigquery.SchemaField("status", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("start_date", "DATE", mode="NULLABLE"),
        bigquery.SchemaField("end_date", "DATE", mode="NULLABLE"),
        bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("updated_at", "TIMESTAMP", mode="REQUIRED"),
    ]
    
    NEGOTIATIONS = [
        bigquery.SchemaField("negotiation_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("campaign_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("influencer_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("company_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("status", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("offered_amount", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("final_amount", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("deliverables", "JSON", mode="NULLABLE"),
        bigquery.SchemaField("timeline", "JSON", mode="NULLABLE"),
        bigquery.SchemaField("ai_negotiation_log", "JSON", mode="NULLABLE"),
        bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("updated_at", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("completed_at", "TIMESTAMP", mode="NULLABLE"),
    ]
    
    DAILY_METRICS = [
        bigquery.SchemaField("date", "DATE", mode="REQUIRED"),
        bigquery.SchemaField("metric_type", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("category", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("total_influencers", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("active_campaigns", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("completed_negotiations", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("avg_engagement_rate", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("total_revenue", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("growth_metrics", "JSON", mode="NULLABLE"),
        bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
    ]


class BigQueryClient:
    """
    BigQuery クライアントのラッパークラス
    
    データウェアハウス操作、分析クエリ実行、テーブル管理を提供
    シングルトンパターンで実装
    """
    
    _instance: Optional['BigQueryClient'] = None
    _client: Optional[bigquery.Client] = None
    
    def __new__(cls) -> 'BigQueryClient':
        """シングルトンパターンの実装"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初期化処理"""
        if self._client is None:
            self._initialize_client()
    
    def _initialize_client(self):
        """BigQuery クライアントの初期化"""
        try:
            # サービスアカウント認証
            if settings.GOOGLE_APPLICATION_CREDENTIALS:
                credentials = service_account.Credentials.from_service_account_file(
                    settings.GOOGLE_APPLICATION_CREDENTIALS
                )
                self._client = bigquery.Client(
                    credentials=credentials,
                    project=settings.GOOGLE_CLOUD_PROJECT_ID
                )
            else:
                # デフォルト認証
                self._client = bigquery.Client(project=settings.GOOGLE_CLOUD_PROJECT_ID)
            
            logger.info(f"BigQuery client initialized for project: {settings.GOOGLE_CLOUD_PROJECT_ID}")
            
        except Exception as e:
            logger.error(f"Failed to initialize BigQuery client: {str(e)}")
            raise
    
    @property
    def client(self) -> bigquery.Client:
        """BigQuery クライアントを取得"""
        if self._client is None:
            self._initialize_client()
        return self._client
    
    def setup_dataset(self, dataset_id: str = None) -> bigquery.Dataset:
        """データセットのセットアップ"""
        if dataset_id is None:
            dataset_id = settings.BIGQUERY_DATASET
        
        try:
            # データセット参照を作成
            dataset_ref = self.client.dataset(dataset_id)
            
            try:
                # 既存データセットを取得
                dataset = self.client.get_dataset(dataset_ref)
                logger.info(f"Dataset {dataset_id} already exists")
                return dataset
                
            except NotFound:
                # データセットが存在しない場合は作成
                dataset = bigquery.Dataset(dataset_ref)
                dataset.location = "US"  # データの保存場所
                dataset.description = "InfuMatch YouTube Influencer Analytics Data Warehouse"
                
                # データセットを作成
                dataset = self.client.create_dataset(dataset, timeout=30)
                logger.info(f"Created dataset {dataset_id}")
                return dataset
                
        except Exception as e:
            logger.error(f"Failed to setup dataset {dataset_id}: {str(e)}")
            raise
    
    def create_table(self, table_name: str, schema: List[bigquery.SchemaField], 
                    dataset_id: str = None) -> bigquery.Table:
        """テーブルの作成"""
        if dataset_id is None:
            dataset_id = settings.BIGQUERY_DATASET
        
        try:
            # テーブル参照を作成
            table_ref = self.client.dataset(dataset_id).table(table_name)
            
            try:
                # 既存テーブルを確認
                table = self.client.get_table(table_ref)
                logger.info(f"Table {dataset_id}.{table_name} already exists")
                return table
                
            except NotFound:
                # テーブルが存在しない場合は作成
                table = bigquery.Table(table_ref, schema=schema)
                
                # パーティショニング設定（日付カラムがある場合）
                if any(field.name in ['date', 'created_at'] for field in schema):
                    if any(field.name == 'date' for field in schema):
                        table.time_partitioning = bigquery.TimePartitioning(
                            type_=bigquery.TimePartitioningType.DAY,
                            field="date"
                        )
                    else:
                        table.time_partitioning = bigquery.TimePartitioning(
                            type_=bigquery.TimePartitioningType.DAY,
                            field="created_at"
                        )
                
                # テーブルを作成
                table = self.client.create_table(table, timeout=30)
                logger.info(f"Created table {dataset_id}.{table_name}")
                return table
                
        except Exception as e:
            logger.error(f"Failed to create table {table_name}: {str(e)}")
            raise
    
    def setup_all_tables(self, dataset_id: str = None):
        """全テーブルのセットアップ"""
        if dataset_id is None:
            dataset_id = settings.BIGQUERY_DATASET
        
        # データセットをセットアップ
        self.setup_dataset(dataset_id)
        
        # 全テーブルを作成
        tables_to_create = [
            (BigQueryTables.INFLUENCERS, BigQuerySchemas.INFLUENCERS),
            (BigQueryTables.INFLUENCER_ANALYTICS, BigQuerySchemas.INFLUENCER_ANALYTICS),
            (BigQueryTables.VIDEO_PERFORMANCE, BigQuerySchemas.VIDEO_PERFORMANCE),
            (BigQueryTables.CAMPAIGNS, BigQuerySchemas.CAMPAIGNS),
            (BigQueryTables.NEGOTIATIONS, BigQuerySchemas.NEGOTIATIONS),
            (BigQueryTables.DAILY_METRICS, BigQuerySchemas.DAILY_METRICS),
        ]
        
        created_tables = []
        for table_name, schema in tables_to_create:
            try:
                table = self.create_table(table_name, schema, dataset_id)
                created_tables.append(table_name)
            except Exception as e:
                logger.error(f"Failed to create table {table_name}: {str(e)}")
        
        logger.info(f"Setup completed for {len(created_tables)} tables: {created_tables}")
        return created_tables
    
    def insert_rows(self, table_name: str, rows: List[Dict[str, Any]], 
                   dataset_id: str = None) -> bool:
        """行の挿入"""
        if dataset_id is None:
            dataset_id = settings.BIGQUERY_DATASET
        
        try:
            table_ref = self.client.dataset(dataset_id).table(table_name)
            table = self.client.get_table(table_ref)
            
            # データを挿入
            errors = self.client.insert_rows_json(table, rows)
            
            if errors:
                logger.error(f"Failed to insert rows into {table_name}: {errors}")
                return False
            else:
                logger.info(f"Successfully inserted {len(rows)} rows into {table_name}")
                return True
                
        except Exception as e:
            logger.error(f"Error inserting rows into {table_name}: {str(e)}")
            return False
    
    def query(self, sql: str) -> Iterator[bigquery.Row]:
        """SQL クエリの実行"""
        try:
            query_job = self.client.query(sql)
            return query_job.result()
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            raise
    
    def query_to_dataframe(self, sql: str) -> pd.DataFrame:
        """SQL クエリの結果をDataFrameで取得"""
        try:
            return self.client.query(sql).to_dataframe()
        except Exception as e:
            logger.error(f"Query to DataFrame failed: {str(e)}")
            raise
    
    def get_table_info(self, table_name: str, dataset_id: str = None) -> Dict[str, Any]:
        """テーブル情報の取得"""
        if dataset_id is None:
            dataset_id = settings.BIGQUERY_DATASET
        
        try:
            table_ref = self.client.dataset(dataset_id).table(table_name)
            table = self.client.get_table(table_ref)
            
            return {
                "table_id": table.table_id,
                "dataset_id": table.dataset_id,
                "project": table.project,
                "schema": [{"name": field.name, "type": field.field_type, "mode": field.mode} 
                          for field in table.schema],
                "num_rows": table.num_rows,
                "num_bytes": table.num_bytes,
                "created": table.created,
                "modified": table.modified,
                "description": table.description,
            }
        except Exception as e:
            logger.error(f"Error getting table info for {table_name}: {str(e)}")
            raise


class BigQueryAnalytics:
    """BigQuery を使用した分析機能"""
    
    def __init__(self):
        self.client = BigQueryClient()
        self.dataset_id = settings.BIGQUERY_DATASET
    
    def get_influencer_growth_trends(self, days: int = 30) -> pd.DataFrame:
        """インフルエンサーの成長トレンド分析"""
        sql = f"""
        SELECT 
            influencer_id,
            DATE(created_at) as date,
            subscriber_growth,
            view_growth,
            engagement_rate,
            trend_score
        FROM `{settings.GOOGLE_CLOUD_PROJECT_ID}.{self.dataset_id}.{BigQueryTables.INFLUENCER_ANALYTICS}`
        WHERE created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
        ORDER BY created_at DESC
        """
        return self.client.query_to_dataframe(sql)
    
    def get_category_performance(self) -> pd.DataFrame:
        """カテゴリ別パフォーマンス分析"""
        sql = f"""
        SELECT 
            category,
            COUNT(*) as influencer_count,
            AVG(subscriber_count) as avg_subscribers,
            AVG(view_count) as avg_views,
            AVG(JSON_EXTRACT_SCALAR(ai_analysis, '$.engagement_rate')) as avg_engagement
        FROM `{settings.GOOGLE_CLOUD_PROJECT_ID}.{self.dataset_id}.{BigQueryTables.INFLUENCERS}`
        WHERE is_active = true
        GROUP BY category
        ORDER BY avg_engagement DESC
        """
        return self.client.query_to_dataframe(sql)
    
    def get_campaign_roi_analysis(self) -> pd.DataFrame:
        """キャンペーンROI分析"""
        sql = f"""
        SELECT 
            c.campaign_id,
            c.title,
            c.budget,
            COUNT(n.negotiation_id) as negotiations_count,
            SUM(n.final_amount) as total_spent,
            AVG(n.final_amount) as avg_deal_size,
            SAFE_DIVIDE(SUM(n.final_amount), c.budget) as spend_ratio
        FROM `{settings.GOOGLE_CLOUD_PROJECT_ID}.{self.dataset_id}.{BigQueryTables.CAMPAIGNS}` c
        LEFT JOIN `{settings.GOOGLE_CLOUD_PROJECT_ID}.{self.dataset_id}.{BigQueryTables.NEGOTIATIONS}` n 
            ON c.campaign_id = n.campaign_id
        WHERE n.status = 'completed'
        GROUP BY c.campaign_id, c.title, c.budget
        ORDER BY spend_ratio DESC
        """
        return self.client.query_to_dataframe(sql)
    
    def get_daily_metrics_summary(self, days: int = 7) -> pd.DataFrame:
        """日次メトリクス集計"""
        sql = f"""
        SELECT 
            date,
            SUM(total_influencers) as total_influencers,
            SUM(active_campaigns) as active_campaigns,
            SUM(completed_negotiations) as completed_negotiations,
            AVG(avg_engagement_rate) as platform_engagement_rate,
            SUM(total_revenue) as daily_revenue
        FROM `{settings.GOOGLE_CLOUD_PROJECT_ID}.{self.dataset_id}.{BigQueryTables.DAILY_METRICS}`
        WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
        GROUP BY date
        ORDER BY date DESC
        """
        return self.client.query_to_dataframe(sql)


# シングルトンインスタンスの取得関数
def get_bigquery_client() -> BigQueryClient:
    """BigQuery クライアントのシングルトンインスタンスを取得"""
    return BigQueryClient()


def get_bigquery_analytics() -> BigQueryAnalytics:
    """BigQuery 分析クラスのインスタンスを取得"""
    return BigQueryAnalytics()


# 初期化関数
async def initialize_bigquery():
    """BigQuery の初期化（データセットとテーブルのセットアップ）"""
    try:
        client = get_bigquery_client()
        created_tables = client.setup_all_tables()
        logger.info(f"BigQuery initialization completed. Tables created: {created_tables}")
        return True
    except Exception as e:
        logger.error(f"BigQuery initialization failed: {str(e)}")
        return False