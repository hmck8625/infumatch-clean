#!/usr/bin/env python3
"""
シンプルなFirestoreテスト用FastAPIサーバー
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional

# 環境変数設定（Cloud Runでは自動的に認証される）
# os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/Users/hamazakidaisuke/Desktop/プロジェクト/250614_hac_iftool/hackathon-462905-7d72a76d3742.json'

app = FastAPI(title="Firestore Test API")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Firestore Test API", "status": "running"}

@app.get("/api/v1/influencers")
async def get_firestore_influencers(
    keyword: str = None,
    category: str = None,
    min_subscribers: int = None,
    max_subscribers: int = None
):
    """Firestoreから直接インフルエンサーデータを取得（フィルタ対応）"""
    try:
        from google.cloud import firestore
        
        # Firestoreクライアント初期化
        db = firestore.Client(project="hackathon-462905")
        
        # データ取得 - influencersコレクションを使用
        collection_ref = db.collection('influencers')
        
        # フィルタ適用
        query = collection_ref
        
        # カテゴリフィルタ
        if category and category != 'all':
            query = query.where('category', '==', category)
        
        # 登録者数フィルタ
        if min_subscribers is not None:
            query = query.where('subscriber_count', '>=', min_subscribers)
        if max_subscribers is not None:
            query = query.where('subscriber_count', '<=', max_subscribers)
        
        # 最大50件に制限
        docs = query.limit(50).stream()
        
        results = []
        for doc in docs:
            data = doc.to_dict()
            # APIレスポンス形式に変換（influencersコレクション構造対応）
            result = {
                "id": data.get('channel_id', doc.id),
                "name": data.get('channel_title', 'Unknown Channel'),
                "channelId": data.get('channel_id', ''),
                "subscriberCount": data.get('subscriber_count', 0),
                "viewCount": data.get('view_count', 0),
                "videoCount": data.get('video_count', 0),
                "category": data.get('category', 'その他'),
                "description": data.get('description', ''),
                "thumbnailUrl": f"https://via.placeholder.com/120x120?text={data.get('channel_title', 'Channel')[:10]}",
                "engagementRate": data.get('engagement_metrics', {}).get('engagement_rate', 0.0),
                "email": data.get('contact_info', {}).get('primary_email'),
                # 追加情報
                "country": data.get('country', 'JP'),
                "language": data.get('language', 'ja'),
                "status": data.get('status', 'active'),
                "aiAnalysis": data.get('ai_analysis', {}).get('advanced', {}),
                "brandSafetyScore": data.get('brand_safety_score', 0.0),
                "contentQualityScore": data.get('content_quality_score', 0.0)
            }
            results.append(result)
        
        # キーワード検索（フロントエンド側で実行）
        if keyword and keyword.strip():
            keyword_lower = keyword.lower()
            filtered_results = []
            for result in results:
                # 名前、説明、カテゴリで検索
                searchable_text = f"{result.get('name', '')} {result.get('description', '')} {result.get('category', '')}".lower()
                if keyword_lower in searchable_text:
                    filtered_results.append(result)
            results = filtered_results
        
        print(f"✅ Firestore: {len(results)} influencers found (keyword: {keyword}, category: {category}, min_subs: {min_subscribers}, max_subs: {max_subscribers})")
        return results
        
    except Exception as e:
        print(f"❌ Firestore error: {e}")
        # フォールバック：サンプルデータ
        return [
            {
                "id": "UC1234567890",
                "name": "[SAMPLE] Firestore接続エラー",
                "channelId": "UC1234567890",
                "subscriberCount": 8500,
                "viewCount": 1250000,
                "videoCount": 156,
                "category": "テクノロジー",
                "description": f"[SAMPLE DATA] Firestoreに接続できませんでした: {str(e)}",
                "thumbnailUrl": "https://via.placeholder.com/120x120?text=ERROR",
                "engagementRate": 4.5,
                "email": "sample@example.com"
            }
        ]

# リクエストモデル
class CollaborationProposalRequest(BaseModel):
    influencer: Dict[str, Any]
    user_settings: Optional[Dict[str, Any]] = None

class CollaborationProposalResponse(BaseModel):
    success: bool
    message: str
    metadata: Optional[Dict[str, Any]] = None

@app.post("/api/v1/collaboration-proposal", response_model=CollaborationProposalResponse)
async def generate_collaboration_proposal(request: CollaborationProposalRequest):
    """AI交渉エージェントを使用してコラボ提案メッセージを生成"""
    try:
        # AI交渉エージェントのインポート
        try:
            from services.ai_agents.negotiation_agent import NegotiationAgent
        except ImportError as e:
            print(f"⚠️ AI agent import failed: {e}")
            # フォールバック: 簡単なテンプレートベースのメッセージ
            return await generate_fallback_message(request)
        
        # 交渉エージェントインスタンス作成
        agent = NegotiationAgent()
        
        # ユーザー設定からキャンペーン情報を構築
        user_settings = request.user_settings or {}
        campaign_info = {
            "product_name": user_settings.get("productName", "弊社商品"),
            "budget_min": user_settings.get("budgetMin", 20000),
            "budget_max": user_settings.get("budgetMax", 50000),
            "campaign_type": user_settings.get("campaignType", "商品紹介"),
            "company_name": user_settings.get("companyName", "弊社"),
            "target_audience": user_settings.get("targetAudience", "一般消費者")
        }
        
        # エージェント処理実行
        result = await agent.process({
            "action": "generate_initial_email",
            "influencer": request.influencer,
            "campaign": campaign_info
        })
        
        if result.get("success"):
            return CollaborationProposalResponse(
                success=True,
                message=result.get("email_content", ""),
                metadata={
                    "personalization_score": result.get("personalization_score"),
                    "agent": result.get("agent"),
                    "campaign_info": campaign_info
                }
            )
        else:
            print(f"❌ AI agent failed: {result.get('error')}")
            # フォールバック処理
            return await generate_fallback_message(request)
            
    except Exception as e:
        print(f"❌ Collaboration proposal error: {e}")
        # フォールバック処理
        return await generate_fallback_message(request)

async def generate_fallback_message(request: CollaborationProposalRequest):
    """フォールバック用のシンプルなメッセージ生成"""
    influencer = request.influencer
    user_settings = request.user_settings or {}
    
    channel_name = influencer.get("name", "YouTuber様")
    subscriber_count = influencer.get("subscriberCount", 0)
    category = influencer.get("category", "")
    product_name = user_settings.get("productName", "弊社商品")
    company_name = user_settings.get("companyName", "弊社")
    
    fallback_message = f"""【コラボレーションのご提案】{channel_name}様へ

{channel_name}様

いつも素晴らしい{category}コンテンツを楽しく拝見させていただいております。
{subscriber_count:,}人の登録者様に愛されるチャンネル運営、本当に素晴らしいですね。

この度、{company_name}より{product_name}のご紹介に関して、コラボレーションのご提案をさせていただきたくご連絡いたしました。

{channel_name}様のコンテンツと弊社商品の親和性が高く、視聴者の皆様にも喜んでいただけるのではないかと考えております。

詳細につきましては、以下の点についてご相談させていただければと思います：
・商品紹介の内容・形式について
・スケジュールについて
・報酬についてのご相談

もしご興味をお持ちいただけましたら、まずはお気軽にご返信いただけますでしょうか。

何卒よろしくお願いいたします。

{company_name}
"""
    
    return CollaborationProposalResponse(
        success=True,
        message=fallback_message,
        metadata={
            "type": "fallback_template",
            "personalization_score": 0.7,
            "campaign_info": user_settings
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)