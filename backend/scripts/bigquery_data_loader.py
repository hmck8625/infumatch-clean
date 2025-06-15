#!/usr/bin/env python3
"""
BigQuery データ登録スクリプト

@description BigQueryに実データを登録するための実行スクリプト
テストデータの生成と実際のデータ登録を行う

@author InfuMatch Development Team
@version 1.0.0
"""

import sys
import os
import asyncio
import logging
from datetime import datetime, timezone, timedelta
import json
import random
from typing import Dict, Any, List

# プロジェクトのルートディレクトリをPythonパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.config import get_settings
from core.database import get_firestore_client, DatabaseHelper, DatabaseCollections
from core.bigquery_client import get_bigquery_client, BigQueryTables, initialize_bigquery
from services.data_integration import get_data_integration_service

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BigQueryDataLoader:
    """BigQuery データローダークラス"""
    
    def __init__(self):
        self.settings = get_settings()
        self.bq_client = get_bigquery_client()
        self.db_helper = DatabaseHelper()
        self.integration = get_data_integration_service()
        
    async def initialize_bigquery_tables(self):
        """BigQuery テーブルの初期化"""
        logger.info("🏗️ Initializing BigQuery tables...")
        
        try:
            # BigQuery 初期化
            await initialize_bigquery()
            logger.info("✅ BigQuery tables initialized successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to initialize BigQuery: {str(e)}")
            return False
    
    def generate_sample_influencers(self, count: int = 50) -> List[Dict[str, Any]]:
        """サンプルインフルエンサーデータの生成"""
        logger.info(f"🎲 Generating {count} sample influencers...")
        
        categories = ['beauty', 'gaming', 'cooking', 'tech', 'fitness', 'fashion', 'travel', 'education']
        countries = ['JP', 'US', 'UK', 'FR', 'DE', 'KR', 'TW']
        languages = ['ja', 'en', 'ko', 'zh']
        
        influencers = []
        
        for i in range(count):
            # ランダムなデータ生成
            subscriber_count = random.randint(1000, 1000000)
            video_count = random.randint(10, 1000)
            view_count = subscriber_count * random.randint(10, 100)
            engagement_rate = round(random.uniform(0.01, 0.10), 4)
            
            influencer = {
                'influencer_id': f'UC{random.randint(10**15, 10**16-1)}',
                'channel_id': f'UC{random.randint(10**15, 10**16-1)}',
                'channel_title': f'サンプルチャンネル {i+1}',
                'description': f'これはサンプルインフルエンサー {i+1} の説明文です。{random.choice(categories)}カテゴリで活動しています。',
                'subscriber_count': subscriber_count,
                'video_count': video_count,
                'view_count': view_count,
                'category': random.choice(categories),
                'country': random.choice(countries),
                'language': random.choice(languages),
                'contact_email': f'sample{i+1}@example.com' if random.random() > 0.5 else '',
                'social_links': json.dumps({
                    'twitter': f'@sample{i+1}' if random.random() > 0.5 else None,
                    'instagram': f'@sample{i+1}' if random.random() > 0.5 else None,
                }),
                'ai_analysis': json.dumps({
                    'engagement_rate': engagement_rate,
                    'content_quality_score': round(random.uniform(0.5, 1.0), 2),
                    'brand_safety_score': round(random.uniform(0.7, 1.0), 2),
                    'growth_potential': round(random.uniform(0.3, 0.9), 2),
                }),
                'created_at': (datetime.now(timezone.utc) - timedelta(days=random.randint(0, 365))).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat(),
                'is_active': random.random() > 0.1  # 90%がアクティブ
            }
            
            influencers.append(influencer)
        
        logger.info(f"✅ Generated {len(influencers)} sample influencers")
        return influencers
    
    def generate_sample_campaigns(self, count: int = 20) -> List[Dict[str, Any]]:
        """サンプルキャンペーンデータの生成"""
        logger.info(f"🎲 Generating {count} sample campaigns...")
        
        categories = ['beauty', 'gaming', 'cooking', 'tech', 'fitness', 'fashion', 'travel', 'education']
        statuses = ['draft', 'active', 'completed', 'paused']
        
        campaigns = []
        
        for i in range(count):
            start_date = datetime.now() + timedelta(days=random.randint(-30, 30))
            end_date = start_date + timedelta(days=random.randint(7, 90))
            
            campaign = {
                'campaign_id': f'camp_{random.randint(10**9, 10**10-1)}',
                'company_id': f'comp_{random.randint(1000, 9999)}',
                'title': f'サンプルキャンペーン {i+1}',
                'description': f'これはサンプルキャンペーン {i+1} の説明文です。',
                'budget': float(random.randint(50000, 5000000)),
                'target_category': random.choice(categories),
                'target_demographics': json.dumps({
                    'age_range': f'{random.choice([18, 20, 25])}-{random.choice([35, 45, 55])}',
                    'gender': random.choice(['all', 'male', 'female']),
                    'interests': random.sample(categories, k=random.randint(1, 3))
                }),
                'requirements': json.dumps({
                    'min_subscribers': random.choice([1000, 5000, 10000, 50000]),
                    'min_engagement_rate': round(random.uniform(0.01, 0.05), 3),
                    'content_type': random.choice(['video_review', 'shorts', 'live_stream', 'post'])
                }),
                'status': random.choice(statuses),
                'start_date': start_date.date().isoformat(),
                'end_date': end_date.date().isoformat(),
                'created_at': (datetime.now(timezone.utc) - timedelta(days=random.randint(0, 60))).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat(),
            }
            
            campaigns.append(campaign)
        
        logger.info(f"✅ Generated {len(campaigns)} sample campaigns")
        return campaigns
    
    def generate_sample_analytics(self, influencer_ids: List[str], days: int = 30) -> List[Dict[str, Any]]:
        """サンプル分析データの生成"""
        logger.info(f"🎲 Generating analytics data for {len(influencer_ids)} influencers over {days} days...")
        
        analytics = []
        
        for influencer_id in influencer_ids[:20]:  # 最初の20人分のみ生成
            base_subscribers = random.randint(10000, 100000)
            
            for day in range(days):
                date = datetime.now() - timedelta(days=day)
                
                record = {
                    'record_id': f'{influencer_id}_{date.strftime("%Y%m%d")}',
                    'influencer_id': influencer_id,
                    'date': date.date().isoformat(),
                    'subscriber_growth': random.randint(-100, 1000),
                    'view_growth': random.randint(-1000, 10000),
                    'engagement_rate': round(random.uniform(0.01, 0.10), 4),
                    'avg_views_per_video': float(random.randint(1000, 100000)),
                    'upload_frequency': round(random.uniform(0.1, 2.0), 2),
                    'trend_score': round(random.uniform(0.1, 1.0), 3),
                    'category_rank': random.randint(1, 1000),
                    'metrics': json.dumps({
                        'likes_per_video': random.randint(10, 10000),
                        'comments_per_video': random.randint(1, 1000),
                        'shares_per_video': random.randint(0, 500)
                    }),
                    'created_at': datetime.now(timezone.utc).isoformat(),
                }
                
                analytics.append(record)
        
        logger.info(f"✅ Generated {len(analytics)} analytics records")
        return analytics
    
    def generate_daily_metrics(self, days: int = 30) -> List[Dict[str, Any]]:
        """日次メトリクスデータの生成"""
        logger.info(f"🎲 Generating daily metrics for {days} days...")
        
        metrics = []
        categories = ['beauty', 'gaming', 'cooking', 'tech', 'fitness', 'all']
        
        for day in range(days):
            date = datetime.now() - timedelta(days=day)
            
            for category in categories:
                metric = {
                    'date': date.date().isoformat(),
                    'metric_type': 'daily_summary' if category == 'all' else 'category_breakdown',
                    'category': category,
                    'total_influencers': random.randint(100, 1000),
                    'active_campaigns': random.randint(5, 50),
                    'completed_negotiations': random.randint(0, 10),
                    'avg_engagement_rate': round(random.uniform(0.02, 0.06), 4),
                    'total_revenue': float(random.randint(100000, 10000000)),
                    'growth_metrics': json.dumps({
                        'new_influencers': random.randint(0, 50),
                        'new_campaigns': random.randint(0, 10),
                        'success_rate': round(random.uniform(0.5, 0.9), 2)
                    }),
                    'created_at': datetime.now(timezone.utc).isoformat(),
                }
                
                metrics.append(metric)
        
        logger.info(f"✅ Generated {len(metrics)} daily metrics")
        return metrics
    
    async def load_sample_data_to_firestore(self):
        """サンプルデータをFirestoreに登録"""
        logger.info("📥 Loading sample data to Firestore...")
        
        try:
            # インフルエンサーデータ生成・登録
            influencers = self.generate_sample_influencers(50)
            
            for influencer in influencers:
                # Firestore用にデータを調整
                firestore_data = {
                    'channel_id': influencer['channel_id'],
                    'channel_title': influencer['channel_title'],
                    'description': influencer['description'],
                    'subscriber_count': influencer['subscriber_count'],
                    'video_count': influencer['video_count'],
                    'view_count': influencer['view_count'],
                    'category': influencer['category'],
                    'country': influencer['country'],
                    'language': influencer['language'],
                    'contact_info': {
                        'email': influencer['contact_email']
                    },
                    'social_links': json.loads(influencer['social_links']),
                    'ai_analysis': json.loads(influencer['ai_analysis']),
                    'status': 'active' if influencer['is_active'] else 'inactive',
                    'created_at': influencer['created_at'],
                    'updated_at': influencer['updated_at']
                }
                
                await self.db_helper.create_document(
                    collection=DatabaseCollections.INFLUENCERS,
                    document_id=influencer['channel_id'],
                    data=firestore_data
                )
            
            logger.info(f"✅ Loaded {len(influencers)} influencers to Firestore")
            
            # キャンペーンデータ生成・登録
            campaigns = self.generate_sample_campaigns(20)
            
            for campaign in campaigns:
                # Firestore用にデータを調整
                firestore_data = {
                    'campaign_id': campaign['campaign_id'],
                    'company_id': campaign['company_id'],
                    'title': campaign['title'],
                    'description': campaign['description'],
                    'budget': campaign['budget'],
                    'target_category': campaign['target_category'],
                    'target_demographics': json.loads(campaign['target_demographics']),
                    'requirements': json.loads(campaign['requirements']),
                    'status': campaign['status'],
                    'start_date': campaign['start_date'],
                    'end_date': campaign['end_date'],
                    'created_at': campaign['created_at'],
                    'updated_at': campaign['updated_at']
                }
                
                await self.db_helper.create_document(
                    collection=DatabaseCollections.CAMPAIGNS,
                    document_id=campaign['campaign_id'],
                    data=firestore_data
                )
            
            logger.info(f"✅ Loaded {len(campaigns)} campaigns to Firestore")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to load data to Firestore: {str(e)}")
            return False
    
    def load_data_directly_to_bigquery(self):
        """BigQueryに直接データを登録"""
        logger.info("📥 Loading data directly to BigQuery...")
        
        try:
            # インフルエンサーデータ
            influencers = self.generate_sample_influencers(100)
            success = self.bq_client.insert_rows(BigQueryTables.INFLUENCERS, influencers)
            if success:
                logger.info(f"✅ Loaded {len(influencers)} influencers to BigQuery")
            else:
                logger.error("❌ Failed to load influencer data")
            
            # キャンペーンデータ
            campaigns = self.generate_sample_campaigns(30)
            success = self.bq_client.insert_rows(BigQueryTables.CAMPAIGNS, campaigns)
            if success:
                logger.info(f"✅ Loaded {len(campaigns)} campaigns to BigQuery")
            else:
                logger.error("❌ Failed to load campaign data")
            
            # 分析データ
            influencer_ids = [inf['influencer_id'] for inf in influencers]
            analytics = self.generate_sample_analytics(influencer_ids, days=30)
            
            # バッチで挿入（100件ずつ）
            for i in range(0, len(analytics), 100):
                batch = analytics[i:i+100]
                success = self.bq_client.insert_rows(BigQueryTables.INFLUENCER_ANALYTICS, batch)
                if success:
                    logger.info(f"✅ Loaded analytics batch {i//100 + 1}")
            
            # 日次メトリクス
            metrics = self.generate_daily_metrics(30)
            success = self.bq_client.insert_rows(BigQueryTables.DAILY_METRICS, metrics)
            if success:
                logger.info(f"✅ Loaded {len(metrics)} daily metrics to BigQuery")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to load data to BigQuery: {str(e)}")
            return False
    
    async def sync_firestore_to_bigquery(self):
        """FirestoreのデータをBigQueryに同期"""
        logger.info("🔄 Syncing Firestore data to BigQuery...")
        
        try:
            # 完全同期を実行
            result = await self.integration.full_sync()
            
            logger.info(f"📊 Sync completed:")
            logger.info(f"  - Total synced: {result['total_synced']} records")
            logger.info(f"  - Failed: {result['total_failed']} records")
            logger.info(f"  - Duration: {result['duration_seconds']:.2f} seconds")
            
            if result['errors']:
                logger.warning(f"  - Errors: {result['errors']}")
            
            return result['success']
            
        except Exception as e:
            logger.error(f"❌ Sync failed: {str(e)}")
            return False
    
    def verify_bigquery_data(self):
        """BigQueryに登録されたデータの確認"""
        logger.info("🔍 Verifying data in BigQuery...")
        
        try:
            # 各テーブルのレコード数を確認
            tables = [
                BigQueryTables.INFLUENCERS,
                BigQueryTables.CAMPAIGNS,
                BigQueryTables.INFLUENCER_ANALYTICS,
                BigQueryTables.DAILY_METRICS
            ]
            
            for table in tables:
                sql = f"""
                SELECT COUNT(*) as count 
                FROM `{self.settings.GOOGLE_CLOUD_PROJECT_ID}.{self.settings.BIGQUERY_DATASET}.{table}`
                """
                
                try:
                    result = list(self.bq_client.query(sql))
                    count = result[0]['count'] if result else 0
                    logger.info(f"✅ Table {table}: {count} records")
                except Exception as e:
                    logger.warning(f"⚠️ Table {table} not found or empty: {str(e)}")
            
            # サンプルクエリの実行
            logger.info("\n📊 Sample query results:")
            
            # カテゴリ別インフルエンサー数
            sql = f"""
            SELECT 
                category,
                COUNT(*) as influencer_count,
                AVG(subscriber_count) as avg_subscribers
            FROM `{self.settings.GOOGLE_CLOUD_PROJECT_ID}.{self.settings.BIGQUERY_DATASET}.{BigQueryTables.INFLUENCERS}`
            WHERE is_active = true
            GROUP BY category
            ORDER BY influencer_count DESC
            LIMIT 5
            """
            
            results = self.bq_client.query(sql)
            logger.info("\nTop 5 categories by influencer count:")
            for row in results:
                logger.info(f"  {row['category']}: {row['influencer_count']} influencers, "
                          f"avg {row['avg_subscribers']:.0f} subscribers")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Verification failed: {str(e)}")
            return False


async def main():
    """メイン実行関数"""
    loader = BigQueryDataLoader()
    
    print("\n" + "="*80)
    print("🚀 BigQuery Data Loading Tool")
    print("="*80)
    print("\n以下のオプションから選択してください:\n")
    print("1. BigQueryテーブルを初期化")
    print("2. サンプルデータをFirestoreに登録")
    print("3. サンプルデータを直接BigQueryに登録")
    print("4. FirestoreからBigQueryに同期")
    print("5. BigQueryのデータを確認")
    print("6. 全て実行（1→2→4→5）")
    print("0. 終了")
    
    while True:
        try:
            choice = input("\n選択 (0-6): ").strip()
            
            if choice == "0":
                print("👋 終了します")
                break
                
            elif choice == "1":
                await loader.initialize_bigquery_tables()
                
            elif choice == "2":
                await loader.load_sample_data_to_firestore()
                
            elif choice == "3":
                loader.load_data_directly_to_bigquery()
                
            elif choice == "4":
                await loader.sync_firestore_to_bigquery()
                
            elif choice == "5":
                loader.verify_bigquery_data()
                
            elif choice == "6":
                print("\n🔄 全プロセスを実行します...\n")
                
                # 1. BigQuery初期化
                if await loader.initialize_bigquery_tables():
                    # 2. Firestoreにサンプルデータ登録
                    if await loader.load_sample_data_to_firestore():
                        # 3. 同期実行
                        if await loader.sync_firestore_to_bigquery():
                            # 4. データ確認
                            loader.verify_bigquery_data()
                            print("\n🎉 全プロセス完了！")
                        else:
                            print("\n❌ 同期に失敗しました")
                    else:
                        print("\n❌ Firestoreへのデータ登録に失敗しました")
                else:
                    print("\n❌ BigQuery初期化に失敗しました")
                    
            else:
                print("❌ 無効な選択です。0-6の数字を入力してください。")
                
        except KeyboardInterrupt:
            print("\n\n👋 中断されました")
            break
        except Exception as e:
            print(f"\n❌ エラーが発生しました: {str(e)}")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    # スクリプト実行
    asyncio.run(main())