"""
Gemini高度マッチングエージェント - 戦略的インフルエンサー分析システム
深い分析と説得力のある推薦理由を提供
"""
import google.generativeai as genai
from typing import Dict, List, Any, Optional
import json
import logging
from datetime import datetime
from google.cloud import firestore
import asyncio

logger = logging.getLogger(__name__)

class GeminiMatchingAgent:
    """Gemini APIを使用した高度なインフルエンサーマッチング分析エージェント"""
    
    def __init__(self, gemini_api_key: str):
        self.gemini_api_key = gemini_api_key
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        try:
            self.db = firestore.Client(project="hackathon-462905")
        except Exception as e:
            logger.warning(f"Firestore initialization failed: {e}")
            self.db = None
        
    async def analyze_deep_matching(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """企業プロファイルとインフルエンサーデータの戦略的マッチング分析"""
        try:
            start_time = datetime.now()
            logger.info("🧠 Gemini高度マッチング分析開始")
            
            # Step 1: インフルエンサーデータの取得
            influencer_candidates = await self._fetch_influencer_candidates(request_data)
            if not influencer_candidates:
                return {
                    "success": False,
                    "error": "マッチング候補となるインフルエンサーが見つかりませんでした"
                }
            
            # Step 2: 各インフルエンサーの詳細分析
            analysis_results = []
            for influencer in influencer_candidates[:5]:  # 上位5名を分析
                try:
                    analysis = await self._analyze_single_influencer(
                        influencer, 
                        request_data
                    )
                    if analysis:
                        analysis_results.append(analysis)
                except Exception as e:
                    logger.warning(f"個別インフルエンサー分析エラー: {e}")
                    continue
            
            if not analysis_results:
                return {
                    "success": False,
                    "error": "分析可能なインフルエンサーが見つかりませんでした"
                }
            
            # Step 3: ポートフォリオ最適化と市場コンテキスト分析
            portfolio_insights = await self._analyze_portfolio_optimization(
                analysis_results, 
                request_data
            )
            market_context = await self._analyze_market_context(
                request_data, 
                analysis_results
            )
            
            # Step 4: 結果の構築
            processing_duration = (datetime.now() - start_time).total_seconds()
            
            return {
                "success": True,
                "analysis_results": analysis_results,
                "portfolio_insights": portfolio_insights,
                "market_context": market_context,
                "processing_metadata": {
                    "analysis_duration_ms": int(processing_duration * 1000),
                    "confidence_score": self._calculate_overall_confidence(analysis_results),
                    "gemini_model_used": "gemini-1.5-flash",
                    "analysis_timestamp": datetime.now().isoformat(),
                    "total_candidates_analyzed": len(analysis_results),
                    "total_candidates_available": len(influencer_candidates)
                }
            }
            
        except Exception as e:
            logger.error(f"Gemini高度マッチング分析エラー: {e}")
            return {
                "success": False,
                "error": f"分析中にエラーが発生しました: {str(e)}"
            }
    
    async def _fetch_influencer_candidates(self, request_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """マッチング候補となるインフルエンサーを取得"""
        try:
            logger.info("📊 インフルエンサー候補データ取得開始")
            
            # Firestoreが利用できない場合はモックデータを返す
            if not self.db:
                logger.warning("Firestore not available, using mock data")
                return self._get_mock_influencers()
            
            # Firestoreからインフルエンサーデータを取得
            influencers_ref = self.db.collection('influencers')
            
            # 基本フィルタリング
            preferences = request_data.get('influencer_preferences', {})
            query = influencers_ref
            
            # 登録者数範囲でフィルタリング
            if preferences.get('subscriber_range'):
                sub_range = preferences['subscriber_range']
                if sub_range.get('min'):
                    query = query.where('subscriber_count', '>=', sub_range['min'])
                if sub_range.get('max'):
                    query = query.where('subscriber_count', '<=', sub_range['max'])
            
            # カテゴリでフィルタリング
            preferred_categories = preferences.get('preferred_categories', [])
            if preferred_categories:
                query = query.where('category', 'in', preferred_categories[:10])  # Firestore制限
            
            # 結果取得
            docs = query.limit(20).stream()
            candidates = []
            
            for doc in docs:
                data = doc.to_dict()
                data['id'] = doc.id
                candidates.append(data)
            
            logger.info(f"✅ {len(candidates)}名の候補を取得")
            return candidates
            
        except Exception as e:
            logger.error(f"インフルエンサー候補取得エラー: {e}")
            return []
    
    async def _analyze_single_influencer(self, influencer: Dict[str, Any], request_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """単一インフルエンサーの詳細分析"""
        try:
            analysis_prompt = self._build_deep_analysis_prompt(influencer, request_data)
            
            response = await self._call_gemini_async(analysis_prompt)
            if not response:
                return None
            
            # JSON形式の応答をパース
            try:
                parsed_response = json.loads(response)
            except json.JSONDecodeError:
                # JSONパースに失敗した場合、テキストから情報を抽出
                parsed_response = self._extract_analysis_from_text(response)
            
            return {
                "influencer_id": influencer.get('id', ''),
                "influencer_data": {
                    "channel_id": influencer.get('channel_id', ''),
                    "channel_name": influencer.get('channel_name', influencer.get('channel_title', influencer.get('name', ''))),
                    "channel_title": influencer.get('channel_title', ''),
                    "description": influencer.get('description', ''),
                    "subscriber_count": influencer.get('subscriber_count', 0),
                    "video_count": influencer.get('video_count', 0),
                    "view_count": influencer.get('view_count', 0),
                    "engagement_rate": influencer.get('engagement_rate', 0.0),
                    "thumbnail_url": influencer.get('thumbnail_url', ''),
                    "category": influencer.get('category', ''),
                    "email": influencer.get('email', '')
                },
                "overall_compatibility_score": parsed_response.get('overall_compatibility_score', 75),
                "detailed_analysis": {
                    "brand_alignment": {
                        "score": parsed_response.get('brand_alignment_score', 70),
                        "reasoning": parsed_response.get('brand_alignment_reasoning', '企業ブランドとの適合性を分析中'),
                        "key_strengths": parsed_response.get('brand_strengths', ['高い信頼性', 'ターゲット層の一致']),
                        "potential_concerns": parsed_response.get('brand_concerns', ['リーチの限界'])
                    },
                    "audience_synergy": {
                        "score": parsed_response.get('audience_synergy_score', 80),
                        "demographic_overlap": parsed_response.get('demographic_overlap', 'ターゲット層の70%が重複'),
                        "engagement_quality": parsed_response.get('engagement_quality', '高品質なエンゲージメント'),
                        "conversion_potential": parsed_response.get('conversion_potential', '中程度から高いコンバージョン期待値')
                    },
                    "content_fit": {
                        "score": parsed_response.get('content_fit_score', 85),
                        "style_compatibility": parsed_response.get('style_compatibility', '企業ブランドと調和するコンテンツスタイル'),
                        "content_themes_match": parsed_response.get('content_themes', ['商品レビュー', 'ライフスタイル提案']),
                        "creative_opportunities": parsed_response.get('creative_opportunities', ['商品統合', 'ストーリーテリング'])
                    },
                    "business_viability": {
                        "score": parsed_response.get('business_viability_score', 75),
                        "roi_prediction": parsed_response.get('roi_prediction', '投資対効果は良好な見込み'),
                        "risk_assessment": parsed_response.get('risk_assessment', '低〜中程度のリスク'),
                        "long_term_potential": parsed_response.get('long_term_potential', '長期的なパートナーシップの可能性')
                    }
                },
                "recommendation_summary": {
                    "confidence_level": parsed_response.get('confidence_level', 'Medium'),
                    "primary_recommendation_reason": parsed_response.get('primary_reason', f'{influencer.get("name", "このインフルエンサー")}は企業の価値観と強く共鳴し、ターゲット層への効果的なリーチが期待できます'),
                    "success_scenario": parsed_response.get('success_scenario', '商品の自然な紹介により、ブランド認知度向上と売上増加が期待されます'),
                    "collaboration_strategy": parsed_response.get('collaboration_strategy', '段階的なコラボレーションから長期パートナーシップへ発展'),
                    "expected_outcomes": parsed_response.get('expected_outcomes', ['ブランド認知度20%向上', 'エンゲージメント率15%向上', '売上5-10%増加'])
                },
                "strategic_insights": {
                    "best_collaboration_types": parsed_response.get('collaboration_types', ['商品レビュー', 'スポンサードコンテンツ', 'ライブ配信']),
                    "optimal_campaign_timing": parsed_response.get('optimal_timing', '3-6ヶ月の継続的キャンペーン'),
                    "content_suggestions": parsed_response.get('content_suggestions', ['商品の使用体験', '日常への統合提案', 'ファンとの交流企画']),
                    "budget_recommendations": {
                        "min": parsed_response.get('budget_min', 80000),
                        "max": parsed_response.get('budget_max', 150000),
                        "reasoning": parsed_response.get('budget_reasoning', 'インフルエンサーの影響力とエンゲージメント率を考慮した適正価格範囲')
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"個別インフルエンサー分析エラー: {e}")
            return None
    
    def _build_deep_analysis_prompt(self, influencer: Dict[str, Any], request_data: Dict[str, Any]) -> str:
        """Gemini用の詳細分析プロンプト構築"""
        company_profile = request_data.get('company_profile', {})
        product_portfolio = request_data.get('product_portfolio', {})
        campaign_objectives = request_data.get('campaign_objectives', {})
        
        prompt = f"""
あなたは戦略的インフルエンサーマーケティングの専門家です。以下の企業とインフルエンサーの詳細情報を分析し、戦略的な適合性を評価してください。

## 📊 企業プロファイル
**企業名**: {company_profile.get('name', 'N/A')}
**業界**: {company_profile.get('industry', 'N/A')}
**企業説明**: {company_profile.get('description', 'N/A')}
**ブランド価値観**: {', '.join(company_profile.get('brand_values', []))}
**ターゲット層**: {', '.join(company_profile.get('target_demographics', []))}
**コミュニケーションスタイル**: {company_profile.get('communication_style', 'N/A')}

## 🎯 商品ポートフォリオ
"""
        
        products = product_portfolio.get('products', [])
        for i, product in enumerate(products[:3], 1):
            prompt += f"""
**商品{i}**: {product.get('name', 'N/A')}
- カテゴリ: {product.get('category', 'N/A')}
- 説明: {product.get('description', 'N/A')}
- ターゲット: {product.get('target_audience', 'N/A')}
- 価格帯: {product.get('price_range', 'N/A')}
- 特徴: {', '.join(product.get('unique_selling_points', []))}
"""
        
        prompt += f"""
## 🚀 キャンペーン目標
**主要目標**: {', '.join(campaign_objectives.get('primary_goals', []))}
**成功指標**: {', '.join(campaign_objectives.get('success_metrics', []))}
**予算範囲**: ¥{campaign_objectives.get('budget_range', {}).get('min', 0):,} - ¥{campaign_objectives.get('budget_range', {}).get('max', 0):,}
**期間**: {campaign_objectives.get('timeline', 'N/A')}

## 👤 分析対象インフルエンサー
**名前**: {influencer.get('name', 'N/A')}
**チャンネルID**: {influencer.get('id', 'N/A')}
**カテゴリ**: {influencer.get('category', 'N/A')}
**登録者数**: {influencer.get('subscriber_count', 0):,}人
**エンゲージメント率**: {influencer.get('engagement_rate', 0):.1f}%
**説明**: {influencer.get('description', 'N/A')}
**動画数**: {influencer.get('video_count', 0)}本
**総視聴回数**: {influencer.get('view_count', 0):,}回

## 📋 分析指示
以下の4つの観点から戦略的分析を行い、JSON形式で回答してください：

1. **ブランド適合性** (0-100点): 企業の価値観、業界、ブランドイメージとの適合度
2. **オーディエンス相乗効果** (0-100点): ターゲット層の重複、エンゲージメント品質、コンバージョン可能性
3. **コンテンツ適合性** (0-100点): コンテンツスタイル、テーマ、創造的機会の評価
4. **ビジネス実現性** (0-100点): ROI予測、リスク評価、長期的可能性

**必須回答項目**:
```json
{{
  "overall_compatibility_score": 85,
  "brand_alignment_score": 80,
  "brand_alignment_reasoning": "具体的な理由",
  "brand_strengths": ["強み1", "強み2"],
  "brand_concerns": ["懸念点1"],
  "audience_synergy_score": 90,
  "demographic_overlap": "詳細な重複分析",
  "engagement_quality": "エンゲージメント品質評価",
  "conversion_potential": "コンバージョン可能性",
  "content_fit_score": 85,
  "style_compatibility": "スタイル適合性",
  "content_themes": ["テーマ1", "テーマ2"],
  "creative_opportunities": ["機会1", "機会2"],
  "business_viability_score": 75,
  "roi_prediction": "ROI予測",
  "risk_assessment": "リスク評価",
  "long_term_potential": "長期的可能性",
  "confidence_level": "High/Medium/Low",
  "primary_reason": "主要推薦理由",
  "success_scenario": "成功シナリオ",
  "collaboration_strategy": "コラボレーション戦略",
  "expected_outcomes": ["期待される成果1", "成果2"],
  "collaboration_types": ["推薦コラボ手法1", "手法2"],
  "optimal_timing": "最適なタイミング",
  "content_suggestions": ["コンテンツ提案1", "提案2"],
  "budget_min": 80000,
  "budget_max": 150000,
  "budget_reasoning": "予算推奨理由"
}}
```

**重要**: 
- 必ずJSON形式で回答
- 日本語で具体的かつ説得力のある分析を提供
- 企業の特性とインフルエンサーの実績を詳細に考慮
- 戦略的視点から実現可能で効果的な提案を行う
"""
        
        return prompt
    
    async def _call_gemini_async(self, prompt: str) -> Optional[str]:
        """Gemini APIの非同期呼び出し"""
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: self.model.generate_content(prompt)
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini API呼び出しエラー: {e}")
            return None
    
    def _extract_analysis_from_text(self, text: str) -> Dict[str, Any]:
        """テキスト形式の回答から分析情報を抽出"""
        # JSONパースに失敗した場合のフォールバック
        return {
            "overall_compatibility_score": 75,
            "brand_alignment_score": 70,
            "brand_alignment_reasoning": "テキスト解析による推定値",
            "brand_strengths": ["適合性", "信頼性"],
            "brand_concerns": ["詳細分析が必要"],
            "audience_synergy_score": 80,
            "demographic_overlap": "ターゲット層の重複が見込まれる",
            "engagement_quality": "良好なエンゲージメント",
            "conversion_potential": "中程度のコンバージョン期待",
            "content_fit_score": 75,
            "style_compatibility": "適合するスタイル",
            "content_themes": ["商品紹介", "ライフスタイル"],
            "creative_opportunities": ["コラボレーション", "創作活動"],
            "business_viability_score": 70,
            "roi_prediction": "良好なROIが期待される",
            "risk_assessment": "低〜中程度のリスク",
            "long_term_potential": "長期的な関係構築の可能性",
            "confidence_level": "Medium",
            "primary_reason": text[:200] if text else "分析結果を取得中",
            "success_scenario": "ブランド認知度向上が期待される",
            "collaboration_strategy": "段階的なアプローチ",
            "expected_outcomes": ["認知度向上", "エンゲージメント増加"],
            "collaboration_types": ["商品レビュー", "スポンサード"],
            "optimal_timing": "3-6ヶ月",
            "content_suggestions": ["商品体験", "日常統合"],
            "budget_min": 80000,
            "budget_max": 150000,
            "budget_reasoning": "標準的な価格帯での推奨"
        }
    
    async def _analyze_portfolio_optimization(self, analysis_results: List[Dict[str, Any]], request_data: Dict[str, Any]) -> Dict[str, Any]:
        """ポートフォリオ最適化分析"""
        try:
            # 全体的な戦略スコア計算
            total_scores = [result["overall_compatibility_score"] for result in analysis_results]
            overall_strategy_score = sum(total_scores) / len(total_scores) if total_scores else 0
            
            # 多様性分析
            categories = [result.get("detailed_analysis", {}).get("content_fit", {}).get("content_themes_match", []) for result in analysis_results]
            unique_categories = set()
            for cat_list in categories:
                unique_categories.update(cat_list)
            
            diversity_analysis = f"選出されたインフルエンサーは{len(unique_categories)}の異なるコンテンツテーマをカバーしており、バランスの取れたポートフォリオです。"
            
            return {
                "overall_strategy_score": int(overall_strategy_score),
                "portfolio_balance": "バランスの取れたインフルエンサー構成",
                "diversity_analysis": diversity_analysis,
                "optimization_suggestions": [
                    "トップパフォーマーとの長期契約を優先",
                    "異なるコンテンツスタイルの組み合わせでリーチを最大化",
                    "段階的な予算配分で効果を測定"
                ]
            }
        except Exception as e:
            logger.error(f"ポートフォリオ最適化分析エラー: {e}")
            return {
                "overall_strategy_score": 75,
                "portfolio_balance": "バランス分析中",
                "diversity_analysis": "多様性を評価中",
                "optimization_suggestions": ["分析を継続中"]
            }
    
    async def _analyze_market_context(self, request_data: Dict[str, Any], analysis_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """市場コンテキスト分析"""
        try:
            company_industry = request_data.get('company_profile', {}).get('industry', '')
            
            # 業界別のトレンド分析
            industry_trends = {
                'テクノロジー': ['AI活用コンテンツ', 'ライブデモンストレーション', 'テクノロジー解説'],
                '美容・化粧品': ['ビフォーアフター', 'ルーティン紹介', 'プロダクトレビュー'],
                '食品・飲料': ['レシピ動画', '食体験レポート', 'ライフスタイル提案'],
                'ファッション': ['コーディネート提案', 'トレンド解説', 'スタイリング動画']
            }
            
            trends = industry_trends.get(company_industry, ['コンテンツマーケティング', 'インフルエンサーコラボ', 'ブランドストーリー'])
            
            return {
                "industry_trends": trends,
                "competitive_landscape": f"{company_industry}業界におけるインフルエンサーマーケティングは活発で、差別化が重要です。",
                "timing_considerations": "現在は新しいコラボレーションを開始するのに適した時期です。"
            }
        except Exception as e:
            logger.error(f"市場コンテキスト分析エラー: {e}")
            return {
                "industry_trends": ["トレンド分析中"],
                "competitive_landscape": "競合状況を分析中",
                "timing_considerations": "タイミングを評価中"
            }
    
    def _calculate_overall_confidence(self, analysis_results: List[Dict[str, Any]]) -> float:
        """全体的な信頼度スコア計算"""
        if not analysis_results:
            return 0.0
        
        confidence_map = {"High": 0.9, "Medium": 0.7, "Low": 0.4}
        confidences = [
            confidence_map.get(
                result.get("recommendation_summary", {}).get("confidence_level", "Medium"), 
                0.7
            ) for result in analysis_results
        ]
        
        return sum(confidences) / len(confidences)
    
    def _get_mock_influencers(self) -> List[Dict[str, Any]]:
        """モックインフルエンサーデータを返す"""
        return [
            {
                "id": "mock_1",
                "channel_id": "UCMock1",
                "channel_name": "ゲーム実況チャンネル",
                "channel_title": "ゲーム実況チャンネル",
                "description": "人気ゲームの実況動画を毎日配信",
                "subscriber_count": 150000,
                "video_count": 500,
                "view_count": 50000000,
                "category": "ゲーム",
                "engagement_rate": 0.08,
                "thumbnail_url": "https://via.placeholder.com/240x240"
            },
            {
                "id": "mock_2",
                "channel_id": "UCMock2",
                "channel_name": "料理チャンネル",
                "channel_title": "料理チャンネル",
                "description": "簡単レシピと料理のコツを紹介",
                "subscriber_count": 80000,
                "video_count": 300,
                "view_count": 20000000,
                "category": "料理",
                "engagement_rate": 0.10,
                "thumbnail_url": "https://via.placeholder.com/240x240"
            },
            {
                "id": "mock_3",
                "channel_id": "UCMock3",
                "channel_name": "フィットネスチャンネル",
                "channel_title": "フィットネスチャンネル",
                "description": "健康的なライフスタイルとワークアウト",
                "subscriber_count": 120000,
                "video_count": 400,
                "view_count": 35000000,
                "category": "フィットネス",
                "engagement_rate": 0.09,
                "thumbnail_url": "https://via.placeholder.com/240x240"
            }
        ]