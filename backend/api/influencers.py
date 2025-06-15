from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from services.database_service import database_service

router = APIRouter()

# モデル定義
class Influencer(BaseModel):
    id: str
    name: str
    channelId: str
    subscriberCount: int
    viewCount: int
    videoCount: int
    category: str
    description: str
    thumbnailUrl: str
    engagementRate: float
    email: Optional[str] = None

# モックデータ
mock_influencers = [
    Influencer(
        id="1",
        name="Tech Review Japan",
        channelId="UC1234567890",
        subscriberCount=8500,
        viewCount=1250000,
        videoCount=156,
        category="テクノロジー",
        description="最新のガジェットレビューと技術解説を行うチャンネル",
        thumbnailUrl="https://via.placeholder.com/120x120",
        engagementRate=4.5,
        email="techreview@example.com"
    ),
    Influencer(
        id="2",
        name="料理研究家ゆうこ",
        channelId="UC2345678901",
        subscriberCount=5200,
        viewCount=890000,
        videoCount=243,
        category="料理",
        description="簡単で美味しい家庭料理のレシピを紹介",
        thumbnailUrl="https://via.placeholder.com/120x120",
        engagementRate=5.2,
        email="yuko.cooking@example.com"
    ),
    Influencer(
        id="3",
        name="Fitness Life Tokyo",
        channelId="UC3456789012",
        subscriberCount=3800,
        viewCount=567000,
        videoCount=89,
        category="フィットネス",
        description="自宅でできるトレーニングとヘルシーライフスタイル",
        thumbnailUrl="https://via.placeholder.com/120x120",
        engagementRate=6.1,
        email="fitness.tokyo@example.com"
    ),
    Influencer(
        id="4",
        name="ビューティー研究所",
        channelId="UC4567890123",
        subscriberCount=9200,
        viewCount=2100000,
        videoCount=312,
        category="美容",
        description="メイクアップチュートリアルとスキンケア情報",
        thumbnailUrl="https://via.placeholder.com/120x120",
        engagementRate=3.8,
        email="beauty.lab@example.com"
    ),
    Influencer(
        id="5",
        name="ゲーム実況チャンネル",
        channelId="UC5678901234",
        subscriberCount=7600,
        viewCount=1890000,
        videoCount=428,
        category="ゲーム",
        description="最新ゲームの実況プレイと攻略情報",
        thumbnailUrl="https://via.placeholder.com/120x120",
        engagementRate=4.2,
        email="game.channel@example.com"
    ),
]

@router.get("/api/v1/influencers", response_model=List[Dict[str, Any]])
async def get_influencers(
    keyword: Optional[str] = Query(None, description="検索キーワード"),
    category: Optional[str] = Query(None, description="カテゴリー"),
    min_subscribers: Optional[int] = Query(None, description="最小登録者数"),
    max_subscribers: Optional[int] = Query(None, description="最大登録者数"),
    limit: int = Query(50, description="取得件数上限")
):
    """インフルエンサー検索API - 実データベース連携"""
    try:
        # データベースサービスからインフルエンサーデータを取得
        results = await database_service.get_influencers(
            keyword=keyword,
            category=category, 
            min_subscribers=min_subscribers,
            max_subscribers=max_subscribers,
            limit=limit
        )
        
        return results
        
    except Exception as e:
        # エラー時はログ出力してHTTPエラーを返す
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to get influencers: {e}")
        raise HTTPException(status_code=500, detail="インフルエンサーデータの取得に失敗しました")

@router.get("/api/v1/influencers/{influencer_id}", response_model=Dict[str, Any])
async def get_influencer_detail(influencer_id: str):
    """インフルエンサー詳細取得API - 実データベース連携"""
    try:
        # データベースサービスから特定のインフルエンサーを取得
        result = await database_service.get_influencer_by_id(influencer_id)
        
        if result is None:
            raise HTTPException(status_code=404, detail="インフルエンサーが見つかりません")
        
        return result
        
    except HTTPException:
        # HTTPExceptionはそのまま再発生
        raise
    except Exception as e:
        # その他のエラーは500エラーとして処理
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to get influencer detail: {e}")
        raise HTTPException(status_code=500, detail="インフルエンサー詳細の取得に失敗しました")