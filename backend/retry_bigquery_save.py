#!/usr/bin/env python3
"""
BigQuery再保存テストスクリプト

@description 修正されたスキーマで追加チャンネルをBigQueryに保存
"""

import json
import asyncio
from datetime import datetime, timezone
from google.cloud import bigquery
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from add_10_channels import TenChannelAdder

async def main():
    """修正されたスキーマでBigQuery保存をテスト"""
    print("🔄 BigQuery保存テスト（修正スキーマ）")
    print("=" * 50)
    
    # 最新のJSONファイルを読み込み
    try:
        with open('backend/additional_10_channels_20250615_194153.json', 'r', encoding='utf-8') as f:
            channels = json.load(f)
        
        print(f"📁 JSONファイル読み込み: {len(channels)} チャンネル")
        
        # TenChannelAdderインスタンス作成
        adder = TenChannelAdder()
        
        # BigQueryに保存
        success = await adder.save_to_bigquery(channels)
        
        if success:
            print("✅ BigQuery保存成功！")
        else:
            print("❌ BigQuery保存失敗")
            
    except Exception as e:
        print(f"❌ エラー: {e}")

if __name__ == "__main__":
    asyncio.run(main())