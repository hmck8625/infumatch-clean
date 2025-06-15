"""
データ統合サービス - Firestore ↔ BigQuery 同期

@description Firestoreリアルタイムデータと BigQuery分析データの統合管理
ETL処理、データ同期、分析データ生成を提供

@author InfuMatch Development Team
@version 1.0.0
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone, timedelta
import json

from core.database import get_firestore_client, DatabaseCollections, DatabaseHelper
from core.bigquery_client import get_bigquery_client, BigQueryTables, get_bigquery_analytics
from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class DataIntegrationService:
    """
    Firestore と BigQuery の統合管理サービス
    
    リアルタイムデータ(Firestore)と分析データ(BigQuery)の同期を管理
    """
    
    def __init__(self):
        self.firestore_client = get_firestore_client()
        self.bigquery_client = get_bigquery_client()
        self.db_helper = DatabaseHelper()
        self.analytics = get_bigquery_analytics()
    
    async def sync_influencers_to_bigquery(self, batch_size: int = 100) -> Dict[str, Any]:
        """
        インフルエンサーデータをFirestoreからBigQueryに同期
        
        Args:
            batch_size: バッチサイズ
            
        Returns:
            Dict: 同期結果
        """
        logger.info("🔄 Starting influencer data sync to BigQuery")
        
        try:
            # Firestoreから最新データを取得
            influencers = await self.db_helper.get_all_documents(
                collection=DatabaseCollections.INFLUENCERS,
                limit=1000  # 一度に最大1000件
            )
            
            if not influencers:
                logger.info("📭 No influencers found in Firestore")
                return {'synced_count': 0, 'error': None}
            
            logger.info(f"📊 Found {len(influencers)} influencers to sync")
            
            # BigQuery用データ形式に変換
            bigquery_rows = []
            for influencer in influencers:
                row = self._convert_influencer_to_bigquery_format(influencer)
                if row:
                    bigquery_rows.append(row)
            
            # バッチでBigQueryに挿入
            synced_count = 0
            failed_count = 0
            
            for i in range(0, len(bigquery_rows), batch_size):
                batch = bigquery_rows[i:i + batch_size]
                
                success = self.bigquery_client.insert_rows(
                    table_name=BigQueryTables.INFLUENCERS,
                    rows=batch
                )
                
                if success:
                    synced_count += len(batch)
                    logger.info(f"✅ Synced batch {i//batch_size + 1}: {len(batch)} records")
                else:
                    failed_count += len(batch)
                    logger.error(f"❌ Failed to sync batch {i//batch_size + 1}")
                
                # 少し待機してAPI制限を避ける
                await asyncio.sleep(0.5)
            
            return {
                'synced_count': synced_count,
                'failed_count': failed_count,
                'total_processed': len(bigquery_rows),
                'error': None
            }
            
        except Exception as e:
            logger.error(f"❌ Influencer sync failed: {str(e)}")
            return {
                'synced_count': 0,
                'failed_count': 0,
                'total_processed': 0,
                'error': str(e)
            }
    
    def _convert_influencer_to_bigquery_format(self, influencer: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """インフルエンサーデータをBigQuery形式に変換"""
        try:
            # 必須フィールドのチェック
            if not influencer.get('channel_id'):
                return None
            
            # 日付文字列をタイムスタンプに変換
            created_at = self._parse_timestamp(influencer.get('created_at'))
            updated_at = self._parse_timestamp(influencer.get('updated_at', influencer.get('created_at')))
            
            return {
                'influencer_id': influencer.get('channel_id'),
                'channel_id': influencer.get('channel_id'),
                'channel_title': influencer.get('channel_title', ''),
                'description': influencer.get('description', ''),
                'subscriber_count': int(influencer.get('subscriber_count', 0)),
                'video_count': int(influencer.get('video_count', 0)),
                'view_count': int(influencer.get('view_count', 0)),
                'category': influencer.get('category', ''),
                'country': influencer.get('country', ''),
                'language': influencer.get('language', ''),
                'contact_email': influencer.get('contact_info', {}).get('email', ''),
                'social_links': json.dumps(influencer.get('social_links', {})),
                'ai_analysis': json.dumps(influencer.get('ai_analysis', {})),
                'created_at': created_at,
                'updated_at': updated_at,
                'is_active': influencer.get('status', 'active') == 'active',
            }
        except Exception as e:
            logger.error(f"❌ Failed to convert influencer {influencer.get('channel_id')}: {str(e)}")
            return None
    
    async def sync_campaigns_to_bigquery(self, batch_size: int = 100) -> Dict[str, Any]:
        """
        キャンペーンデータをFirestoreからBigQueryに同期
        """
        logger.info("🔄 Starting campaign data sync to BigQuery")
        
        try:
            # Firestoreからキャンペーンデータを取得
            campaigns = await self.db_helper.get_all_documents(
                collection=DatabaseCollections.CAMPAIGNS,
                limit=1000
            )
            
            if not campaigns:
                logger.info("📭 No campaigns found in Firestore")
                return {'synced_count': 0, 'error': None}
            
            logger.info(f"📊 Found {len(campaigns)} campaigns to sync")
            
            # BigQuery用データ形式に変換
            bigquery_rows = []
            for campaign in campaigns:
                row = self._convert_campaign_to_bigquery_format(campaign)
                if row:
                    bigquery_rows.append(row)
            
            # バッチでBigQueryに挿入
            synced_count = 0
            failed_count = 0
            
            for i in range(0, len(bigquery_rows), batch_size):
                batch = bigquery_rows[i:i + batch_size]
                
                success = self.bigquery_client.insert_rows(
                    table_name=BigQueryTables.CAMPAIGNS,
                    rows=batch
                )
                
                if success:
                    synced_count += len(batch)
                else:
                    failed_count += len(batch)
            
            return {
                'synced_count': synced_count,
                'failed_count': failed_count,
                'total_processed': len(bigquery_rows),
                'error': None
            }
            
        except Exception as e:
            logger.error(f"❌ Campaign sync failed: {str(e)}")
            return {
                'synced_count': 0,
                'failed_count': 0,
                'error': str(e)
            }
    
    def _convert_campaign_to_bigquery_format(self, campaign: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """キャンペーンデータをBigQuery形式に変換"""
        try:
            if not campaign.get('campaign_id'):
                return None
            
            created_at = self._parse_timestamp(campaign.get('created_at'))
            updated_at = self._parse_timestamp(campaign.get('updated_at', campaign.get('created_at')))
            
            # 日付文字列をDATEに変換
            start_date = self._parse_date(campaign.get('start_date'))
            end_date = self._parse_date(campaign.get('end_date'))
            
            return {
                'campaign_id': campaign.get('campaign_id'),
                'company_id': campaign.get('company_id', ''),
                'title': campaign.get('title', ''),
                'description': campaign.get('description', ''),
                'budget': float(campaign.get('budget', 0)),
                'target_category': campaign.get('target_category', ''),
                'target_demographics': json.dumps(campaign.get('target_demographics', {})),
                'requirements': json.dumps(campaign.get('requirements', {})),
                'status': campaign.get('status', 'draft'),
                'start_date': start_date,
                'end_date': end_date,
                'created_at': created_at,
                'updated_at': updated_at,
            }
        except Exception as e:
            logger.error(f"❌ Failed to convert campaign {campaign.get('campaign_id')}: {str(e)}")
            return None
    
    async def generate_daily_metrics(self, target_date: datetime = None) -> Dict[str, Any]:
        """
        日次メトリクスの生成とBigQueryへの保存
        
        Args:
            target_date: 対象日付（None の場合は前日）
            
        Returns:
            Dict: 生成結果
        """
        if target_date is None:
            target_date = datetime.now(timezone.utc) - timedelta(days=1)
        
        logger.info(f"📊 Generating daily metrics for {target_date.date()}")
        
        try:
            # 各種メトリクスを並行して計算
            tasks = [
                self._calculate_influencer_metrics(target_date),
                self._calculate_campaign_metrics(target_date),
                self._calculate_negotiation_metrics(target_date),
                self._calculate_engagement_metrics(target_date),
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 結果を統合
            daily_metrics = []
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"❌ Metric calculation {i} failed: {str(result)}")
                    continue
                
                if result:
                    daily_metrics.extend(result)
            
            # BigQueryに保存
            if daily_metrics:
                success = self.bigquery_client.insert_rows(
                    table_name=BigQueryTables.DAILY_METRICS,
                    rows=daily_metrics
                )
                
                if success:
                    logger.info(f"✅ Saved {len(daily_metrics)} daily metrics to BigQuery")
                    return {
                        'metrics_generated': len(daily_metrics),
                        'target_date': target_date.date().isoformat(),
                        'success': True
                    }
                else:
                    return {
                        'metrics_generated': 0,
                        'error': 'Failed to save to BigQuery',
                        'success': False
                    }
            else:
                return {
                    'metrics_generated': 0,
                    'error': 'No metrics calculated',
                    'success': False
                }
                
        except Exception as e:
            logger.error(f"❌ Daily metrics generation failed: {str(e)}")
            return {
                'metrics_generated': 0,
                'error': str(e),
                'success': False
            }
    
    async def _calculate_influencer_metrics(self, target_date: datetime) -> List[Dict[str, Any]]:
        """インフルエンサー関連メトリクスの計算"""
        try:
            # アクティブなインフルエンサー数を取得
            active_influencers = await self.db_helper.query_documents(
                collection=DatabaseCollections.INFLUENCERS,
                conditions=[('status', '==', 'active')]
            )
            
            # カテゴリ別の分布を計算
            category_counts = {}
            total_engagement = 0
            engagement_count = 0
            
            for influencer in active_influencers:
                category = influencer.get('category', 'unknown')
                category_counts[category] = category_counts.get(category, 0) + 1
                
                # エンゲージメント率の計算
                ai_analysis = influencer.get('ai_analysis', {})
                if isinstance(ai_analysis, dict) and 'engagement_rate' in ai_analysis:
                    total_engagement += float(ai_analysis['engagement_rate'])
                    engagement_count += 1
            
            # メトリクスを構築
            metrics = []
            
            # 全体メトリクス
            avg_engagement = total_engagement / engagement_count if engagement_count > 0 else 0
            
            metrics.append({
                'date': target_date.date().isoformat(),
                'metric_type': 'influencer_overview',
                'category': 'all',
                'total_influencers': len(active_influencers),
                'active_campaigns': 0,  # 後で他のタスクで設定
                'completed_negotiations': 0,  # 後で他のタスクで設定
                'avg_engagement_rate': round(avg_engagement, 4),
                'total_revenue': 0,  # 後で他のタスクで設定
                'growth_metrics': json.dumps({
                    'new_influencers_today': 0,  # 実装要
                    'category_distribution': category_counts
                }),
                'created_at': datetime.now(timezone.utc).isoformat(),
            })
            
            # カテゴリ別メトリクス
            for category, count in category_counts.items():
                metrics.append({
                    'date': target_date.date().isoformat(),
                    'metric_type': 'category_breakdown',
                    'category': category,
                    'total_influencers': count,
                    'active_campaigns': 0,
                    'completed_negotiations': 0,
                    'avg_engagement_rate': 0,
                    'total_revenue': 0,
                    'growth_metrics': json.dumps({}),
                    'created_at': datetime.now(timezone.utc).isoformat(),
                })
            
            return metrics
            
        except Exception as e:
            logger.error(f"❌ Influencer metrics calculation failed: {str(e)}")
            return []
    
    async def _calculate_campaign_metrics(self, target_date: datetime) -> List[Dict[str, Any]]:
        """キャンペーン関連メトリクスの計算"""
        try:
            # アクティブなキャンペーン数を取得
            active_campaigns = await self.db_helper.query_documents(
                collection=DatabaseCollections.CAMPAIGNS,
                conditions=[('status', '==', 'active')]
            )
            
            # 今日作成されたキャンペーン
            today_campaigns = await self.db_helper.query_documents(
                collection=DatabaseCollections.CAMPAIGNS,
                conditions=[
                    ('created_at', '>=', target_date.isoformat()),
                    ('created_at', '<', (target_date + timedelta(days=1)).isoformat())
                ]
            )
            
            return [{
                'date': target_date.date().isoformat(),
                'metric_type': 'campaign_overview',
                'category': 'all',
                'total_influencers': 0,
                'active_campaigns': len(active_campaigns),
                'completed_negotiations': 0,
                'avg_engagement_rate': 0,
                'total_revenue': 0,
                'growth_metrics': json.dumps({
                    'new_campaigns_today': len(today_campaigns),
                    'campaigns_by_status': {}  # 実装要
                }),
                'created_at': datetime.now(timezone.utc).isoformat(),
            }]
            
        except Exception as e:
            logger.error(f"❌ Campaign metrics calculation failed: {str(e)}")
            return []
    
    async def _calculate_negotiation_metrics(self, target_date: datetime) -> List[Dict[str, Any]]:
        """交渉関連メトリクスの計算"""
        try:
            # 今日完了した交渉
            completed_negotiations = await self.db_helper.query_documents(
                collection=DatabaseCollections.NEGOTIATIONS,
                conditions=[
                    ('status', '==', 'completed'),
                    ('completed_at', '>=', target_date.isoformat()),
                    ('completed_at', '<', (target_date + timedelta(days=1)).isoformat())
                ]
            )
            
            # 売上計算
            total_revenue = sum(
                float(neg.get('final_amount', 0)) 
                for neg in completed_negotiations
            )
            
            return [{
                'date': target_date.date().isoformat(),
                'metric_type': 'negotiation_overview',
                'category': 'all',
                'total_influencers': 0,
                'active_campaigns': 0,
                'completed_negotiations': len(completed_negotiations),
                'avg_engagement_rate': 0,
                'total_revenue': total_revenue,
                'growth_metrics': json.dumps({
                    'avg_deal_size': total_revenue / len(completed_negotiations) if completed_negotiations else 0,
                    'negotiation_success_rate': 0  # 実装要
                }),
                'created_at': datetime.now(timezone.utc).isoformat(),
            }]
            
        except Exception as e:
            logger.error(f"❌ Negotiation metrics calculation failed: {str(e)}")
            return []
    
    async def _calculate_engagement_metrics(self, target_date: datetime) -> List[Dict[str, Any]]:
        """エンゲージメント関連メトリクスの計算"""
        # 現在のFirestoreデータから平均エンゲージメント率を計算
        # 実装は後で追加
        return []
    
    def _parse_timestamp(self, timestamp_str: str) -> str:
        """タイムスタンプ文字列をBigQuery形式に変換"""
        if not timestamp_str:
            return datetime.now(timezone.utc).isoformat()
        
        try:
            # 既にISO形式の場合
            if 'T' in timestamp_str:
                return timestamp_str
            
            # その他の形式を試行
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return dt.isoformat()
        except:
            return datetime.now(timezone.utc).isoformat()
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """日付文字列をBigQuery DATE形式に変換"""
        if not date_str:
            return None
        
        try:
            # ISO日付形式
            if 'T' in date_str:
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                return dt.date().isoformat()
            else:
                # すでに日付形式
                return datetime.fromisoformat(date_str).date().isoformat()
        except:
            return None
    
    async def full_sync(self) -> Dict[str, Any]:
        """
        完全同期 - 全データをFirestoreからBigQueryに同期
        """
        logger.info("🔄 Starting full data sync")
        
        start_time = datetime.now(timezone.utc)
        
        # 並行してすべての同期を実行
        tasks = [
            self.sync_influencers_to_bigquery(),
            self.sync_campaigns_to_bigquery(),
            self.generate_daily_metrics(),
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()
        
        # 結果を集計
        total_synced = 0
        total_failed = 0
        errors = []
        
        sync_types = ['influencers', 'campaigns', 'daily_metrics']
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                errors.append(f"{sync_types[i]}: {str(result)}")
            elif isinstance(result, dict):
                total_synced += result.get('synced_count', result.get('metrics_generated', 0))
                total_failed += result.get('failed_count', 0)
                if result.get('error'):
                    errors.append(f"{sync_types[i]}: {result['error']}")
        
        return {
            'total_synced': total_synced,
            'total_failed': total_failed,
            'duration_seconds': duration,
            'errors': errors,
            'success': len(errors) == 0,
            'completed_at': end_time.isoformat()
        }


# 便利な関数
def get_data_integration_service() -> DataIntegrationService:
    """データ統合サービスのインスタンスを取得"""
    return DataIntegrationService()


# 定期実行用の関数
async def run_daily_sync():
    """日次データ同期の実行"""
    service = get_data_integration_service()
    result = await service.full_sync()
    
    logger.info(f"📊 Daily sync completed:")
    logger.info(f"  - Synced: {result['total_synced']} records")
    logger.info(f"  - Failed: {result['total_failed']} records")
    logger.info(f"  - Duration: {result['duration_seconds']:.2f} seconds")
    
    if result['errors']:
        logger.error(f"  - Errors: {result['errors']}")
    
    return result


if __name__ == "__main__":
    # テスト実行
    asyncio.run(run_daily_sync())