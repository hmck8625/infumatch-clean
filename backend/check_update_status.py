#!/usr/bin/env python3
"""
更新状況確認

@description 現在の更新状況を確認
"""

import json
from google.cloud import bigquery

def check_update_status():
    """更新状況を確認"""
    try:
        client = bigquery.Client(project="hackathon-462905")
        
        query = """
        SELECT 
            channel_id,
            channel_title,
            ai_analysis,
            updated_at
        FROM `hackathon-462905.infumatch_data.influencers`
        WHERE is_active = true
        ORDER BY subscriber_count DESC
        """
        
        query_job = client.query(query)
        results = query_job.result()
        
        total_channels = 0
        updated_channels = 0
        old_format_channels = 0
        
        updated_list = []
        old_format_list = []
        
        for row in results:
            total_channels += 1
            
            if row.ai_analysis:
                try:
                    ai_data = json.loads(row.ai_analysis)
                    if 'advanced_analysis' in ai_data:
                        updated_channels += 1
                        updated_list.append(row.channel_title)
                    else:
                        old_format_channels += 1
                        old_format_list.append(row.channel_title)
                except:
                    old_format_channels += 1
                    old_format_list.append(row.channel_title)
            else:
                old_format_channels += 1
                old_format_list.append(row.channel_title)
        
        print("📊 現在の更新状況")
        print("=" * 60)
        print(f"総チャンネル数: {total_channels}")
        print(f"新形式AI分析済み: {updated_channels} ({updated_channels/total_channels*100:.1f}%)")
        print(f"旧形式/未更新: {old_format_channels} ({old_format_channels/total_channels*100:.1f}%)")
        print()
        
        print("✅ 新形式AI分析済み:")
        for i, ch in enumerate(updated_list, 1):
            print(f"  {i:2d}. {ch}")
        print()
        
        if old_format_list:
            print("🔄 未更新:")
            for i, ch in enumerate(old_format_list, 1):
                print(f"  {i:2d}. {ch}")
        else:
            print("🎉 全チャンネルが新形式AI分析済みです！")
        
    except Exception as e:
        print(f"❌ 確認エラー: {e}")

if __name__ == "__main__":
    check_update_status()