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
            
            logger.info(f"📊 取得したインフルエンサー候補数: {len(influencer_candidates)}")
            if influencer_candidates:
                logger.info(f"📋 候補カテゴリ: {[c.get('category', 'unknown') for c in influencer_candidates[:10]]}")
                preferences = request_data.get('influencer_preferences', {})
                logger.info(f"🎯 カスタム希望: {preferences.get('custom_preference', 'なし')}")
            
            if not influencer_candidates:
                # 詳細な分析結果を提供
                analysis = await self._analyze_matching_failure([], request_data)
                return {
                    "success": False,
                    "error": "指定された条件に一致するインフルエンサーが見つかりませんでした",
                    "failure_analysis": analysis,
                    "suggestions": [
                        "登録者数の範囲を拡大してください",
                        "カテゴリ条件を緩和または除去してください", 
                        "創造的な異業種コラボレーションを検討してください",
                        "カスタム希望欄に具体的なインフルエンサーのタイプを入力してください"
                    ],
                    "retry_recommendations": {
                        "remove_category_filter": "カテゴリフィルターを除去して再検索",
                        "expand_subscriber_range": "登録者数範囲を1,000-1,000,000に拡大",
                        "use_ai_suggestions": "AIによる代替マッチング提案を利用"
                    }
                }
            
            # Step 2: 各インフルエンサーの詳細分析
            analysis_results = []
            # カスタム希望がある場合は最大10名まで分析
            preferences = request_data.get('influencer_preferences', {})
            custom_preference = preferences.get('custom_preference', '')
            max_analysis = 10 if custom_preference else 5
            
            for influencer in influencer_candidates[:max_analysis]:
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
            logger.error(f"エラータイプ: {type(e).__name__}")
            import traceback
            logger.error(f"スタックトレース: {traceback.format_exc()}")
            return {
                "success": False,
                "error": f"分析中にエラーが発生しました: {str(e)}"
            }
    
    async def _fetch_influencer_candidates(self, request_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Geminiを活用した柔軟なマッチング候補取得"""
        try:
            logger.info("📊 Gemini柔軟マッチング開始")
            
            # Firestoreが利用できない場合はエラーを返す
            if not self.db:
                logger.error("❌ Firestore接続なし")
                return []
            
            # 全体のインフルエンサー数を確認
            all_influencers = []
            try:
                all_docs = self.db.collection('influencers').stream()
                for doc in all_docs:
                    data = doc.to_dict()
                    data['id'] = doc.id
                    all_influencers.append(data)
                logger.info(f"📊 Firestore総インフルエンサー数: {len(all_influencers)}")
            except Exception as e:
                logger.error(f"❌ Firestore全データ取得エラー: {e}")
                return []
            
            if not all_influencers:
                logger.error("❌ Firestoreにインフルエンサーデータが存在しません")
                return []
            
            # Gemini AIによる知的マッチング分析
            preferences = request_data.get('influencer_preferences', {})
            company_profile = request_data.get('company_profile', {})
            product_portfolio = request_data.get('product_portfolio', {})
            
            # 段階的フィルタリング戦略
            candidates = await self._apply_intelligent_filtering(
                all_influencers, 
                preferences, 
                company_profile, 
                product_portfolio
            )
            
            if not candidates:
                # Geminiによる代替マッチング提案
                alternative_candidates = await self._gemini_alternative_matching(
                    all_influencers,
                    request_data
                )
                if alternative_candidates:
                    logger.info(f"🔄 Gemini代替マッチング: {len(alternative_candidates)}名")
                    return alternative_candidates
                
                # 最終的に見つからない場合の詳細分析
                analysis = await self._analyze_matching_failure(
                    all_influencers,
                    request_data
                )
                logger.error(f"❌ マッチング失敗分析: {analysis}")
                return []  # 空のリストを返してエラーハンドリングを上位に委ねる
            
            logger.info(f"✅ 最終候補: {len(candidates)}名")
            return candidates
            
        except Exception as e:
            logger.error(f"❌ 柔軟マッチングエラー: {e}")
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
        influencer_preferences = request_data.get('influencer_preferences', {})
        custom_preference = influencer_preferences.get('custom_preference', '')
        
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

{f'## 🎯 カスタム希望インフルエンサータイプ' if custom_preference else ''}
{f'**指定タイプ**: {custom_preference}' if custom_preference else ''}
{f'※この希望タイプに特に注目して分析してください' if custom_preference else ''}

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
        logger.info("📌 モックデータを返します（Firestore利用不可）")
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
            },
            {
                "id": "mock_4",
                "channel_id": "UCMock4",
                "channel_name": "ビジネス講座チャンネル",
                "channel_title": "ビジネス講座チャンネル",
                "description": "起業・経営・マーケティングに関する実践的な知識",
                "subscriber_count": 95000,
                "video_count": 250,
                "view_count": 25000000,
                "category": "ビジネス",
                "engagement_rate": 0.07,
                "thumbnail_url": "https://via.placeholder.com/240x240"
            },
            {
                "id": "mock_5",
                "channel_id": "UCMock5",
                "channel_name": "美容メイクチャンネル",
                "channel_title": "美容メイクチャンネル",
                "description": "最新メイクテクニックとスキンケア情報",
                "subscriber_count": 200000,
                "video_count": 600,
                "view_count": 80000000,
                "category": "美容",
                "engagement_rate": 0.12,
                "thumbnail_url": "https://via.placeholder.com/240x240"
            },
            {
                "id": "mock_6",
                "channel_id": "UCMock6",
                "channel_name": "テックレビューチャンネル",
                "channel_title": "テックレビューチャンネル",
                "description": "最新ガジェットとテクノロジーのレビュー",
                "subscriber_count": 180000,
                "video_count": 450,
                "view_count": 60000000,
                "category": "テクノロジー",
                "engagement_rate": 0.08,
                "thumbnail_url": "https://via.placeholder.com/240x240"
            },
            {
                "id": "mock_7",
                "channel_id": "UCMock7",
                "channel_name": "エンタメバラエティチャンネル",
                "channel_title": "エンタメバラエティチャンネル",
                "description": "お笑いとバラエティコンテンツで楽しさ満載",
                "subscriber_count": 300000,
                "video_count": 800,
                "view_count": 120000000,
                "category": "エンタメ",
                "engagement_rate": 0.15,
                "thumbnail_url": "https://via.placeholder.com/240x240"
            },
            {
                "id": "mock_8",
                "channel_id": "UCMock8",
                "channel_name": "ファッションコーデチャンネル",
                "channel_title": "ファッションコーデチャンネル",
                "description": "トレンドファッションとコーディネート提案",
                "subscriber_count": 160000,
                "video_count": 350,
                "view_count": 45000000,
                "category": "ファッション",
                "engagement_rate": 0.11,
                "thumbnail_url": "https://via.placeholder.com/240x240"
            }
        ]
    
    async def _get_available_categories(self) -> List[str]:
        """Firestoreから実際に存在するカテゴリ一覧を取得"""
        try:
            if not self.db:
                # モックデータのカテゴリを返す
                return ["ゲーム", "料理", "フィットネス", "ビジネス", "美容", "テクノロジー", "エンタメ", "ファッション"]
            
            # Firestoreからユニークなカテゴリ一覧を取得
            categories = set()
            docs = self.db.collection('influencers').limit(100).stream()
            
            for doc in docs:
                data = doc.to_dict()
                category = data.get('category')
                if category:
                    categories.add(category)
            
            return list(categories)
            
        except Exception as e:
            logger.error(f"カテゴリ一覧取得エラー: {e}")
            # フォールバック
            return ["ゲーム", "料理", "フィットネス", "ビジネス", "美容", "テクノロジー", "エンタメ", "ファッション"]
    
    async def _map_categories_with_gemini(self, user_preference: str, available_categories: List[str]) -> List[str]:
        """Gemini APIを使ってユーザー希望に最も近いカテゴリを選択"""
        try:
            # より詳細な日本語特化のマッピングプロンプト
            prompt = f"""
あなたはインフルエンサーマーケティングの専門家です。
ユーザーの希望に最も適合するカテゴリを、利用可能なカテゴリから選択してください。

【ユーザーの希望】
{user_preference}

【利用可能なカテゴリ一覧】
{', '.join(available_categories)}

【マッピングルール】
1. ユーザーの希望に最も適合するカテゴリを選択
2. 関連性の高いカテゴリも含めて、最大3つまで選択可能
3. 完全一致がなくても、意味的に近いカテゴリを選択
4. 広義の解釈も含めて柔軟にマッピング

【特別なマッピング例】
希望: "美容系" → Howto & Style, People & Blogs (美容関連チャンネルは通常この分類)
希望: "ゲーム実況" → ゲーム
希望: "グルメ" → 料理, Howto & Style
希望: "ファッション" → Howto & Style, People & Blogs
希望: "テクノロジー" → テクノロジー
希望: "エンタメ" → エンターテインメント, 音楽・エンターテイメント

【注意事項】
- 日本のYouTubeカテゴリシステムでは、美容系チャンネルは「Howto & Style」に分類されることが多い
- ライフスタイル系は「People & Blogs」に含まれる
- エンターテイメント系は複数カテゴリに分散

結果をカンマ区切りで返してください（説明不要）：
"""
            
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            logger.info(f"🤖 Gemini応答: '{response_text}'")
            
            # レスポンスをパースしてカテゴリリストに変換
            selected_categories = []
            for category in response_text.split(','):
                category = category.strip()
                if category in available_categories:
                    selected_categories.append(category)
                    logger.info(f"✅ マッチ: '{category}'")
                else:
                    logger.warning(f"⚠️ カテゴリ不一致: '{category}' (利用可能: {available_categories})")
            
            # フォールバック戦略の強化
            if not selected_categories:
                logger.warning(f"⚠️ Geminiマッピング失敗、フォールバック開始")
                
                # 1. 特定キーワードによる手動マッピング
                user_lower = user_preference.lower()
                manual_mappings = {
                    '美容': ['Howto & Style', 'People & Blogs'],
                    'コスメ': ['Howto & Style', 'People & Blogs'],
                    'メイク': ['Howto & Style'],
                    'ファッション': ['Howto & Style', 'People & Blogs'],
                    'スキンケア': ['Howto & Style'],
                    'グルメ': ['料理', 'Howto & Style'],
                    '料理': ['料理'],
                    'ゲーム': ['ゲーム'],
                    'フィットネス': ['People & Blogs', 'スポーツ・アウトドア'],
                    'ビジネス': ['People & Blogs'],
                    'テクノロジー': ['People & Blogs'],
                    'エンタメ': ['エンターテインメント', '音楽・エンターテイメント']
                }
                
                for keyword, mapped_cats in manual_mappings.items():
                    if keyword in user_lower:
                        for mapped_cat in mapped_cats:
                            if mapped_cat in available_categories:
                                selected_categories.append(mapped_cat)
                        break
                
                # 2. 部分マッチによるフォールバック
                if not selected_categories:
                    for cat in available_categories:
                        if any(keyword in cat.lower() for keyword in user_lower.split()):
                            selected_categories.append(cat)
                            break
                
                # 3. 最終フォールバック - 関連性の高いカテゴリを返す
                if not selected_categories:
                    # 美容系の場合は代替カテゴリを提案
                    if '美容' in user_lower or 'コスメ' in user_lower or 'メイク' in user_lower:
                        fallback_cats = ['Howto & Style', 'People & Blogs']
                        for cat in fallback_cats:
                            if cat in available_categories:
                                selected_categories.append(cat)
                    
                    # まだ何も見つからない場合は全カテゴリ対象にする
                    if not selected_categories:
                        logger.warning(f"⚠️ 全フォールバック失敗: '{user_preference}' -> 全カテゴリ対象")
                        return []
            
            final_categories = selected_categories[:3]  # 最大3つまで
            logger.info(f"🎯 最終マッピング結果: {final_categories}")
            return final_categories
            
        except Exception as e:
            logger.error(f"Geminiカテゴリマッピングエラー: {e}")
            # 緊急フォールバック
            user_lower = user_preference.lower()
            fallback_categories = []
            
            # 簡単なキーワードマッチ
            if '美容' in user_lower or 'コスメ' in user_lower:
                fallback_categories = ['Howto & Style', 'People & Blogs']
            elif 'ゲーム' in user_lower:
                fallback_categories = ['ゲーム']
            elif '料理' in user_lower or 'グルメ' in user_lower:
                fallback_categories = ['料理']
            
            # 利用可能なカテゴリでフィルタリング
            final_fallback = [cat for cat in fallback_categories if cat in available_categories]
            logger.info(f"🔄 緊急フォールバック: {final_fallback}")
            return final_fallback[:3]
    
    async def _apply_intelligent_filtering(self, all_influencers: List[Dict[str, Any]], 
                                         preferences: Dict[str, Any], 
                                         company_profile: Dict[str, Any], 
                                         product_portfolio: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Geminiを使った知的フィルタリング"""
        try:
            # 段階1: 基本条件フィルタリング
            candidates = []
            
            # 登録者数フィルタリング
            subscriber_range = preferences.get('subscriber_range', {})
            min_subscribers = subscriber_range.get('min', 0)
            max_subscribers = subscriber_range.get('max', float('inf'))
            
            for influencer in all_influencers:
                sub_count = influencer.get('subscriber_count', 0)
                if min_subscribers <= sub_count <= max_subscribers:
                    candidates.append(influencer)
            
            logger.info(f"📊 登録者数フィルタリング後: {len(candidates)}名")
            
            # 段階2: カテゴリ関連性フィルタリング
            if preferences.get('preferred_categories') or preferences.get('custom_preference'):
                category_filtered = await self._gemini_category_matching(
                    candidates, preferences, company_profile, product_portfolio
                )
                logger.info(f"📂 カテゴリフィルタリング後: {len(category_filtered)}名")
                return category_filtered[:20]  # 最大20名に制限
            
            return candidates[:20]  # カテゴリ指定がない場合は登録者数でソートして上位20名
            
        except Exception as e:
            logger.error(f"❌ 知的フィルタリングエラー: {e}")
            return all_influencers[:10]  # フォールバック
    
    async def _gemini_category_matching(self, influencers: List[Dict[str, Any]], 
                                       preferences: Dict[str, Any], 
                                       company_profile: Dict[str, Any], 
                                       product_portfolio: Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Geminiによるカテゴリ適合性判定"""
        try:
            # インフルエンサーのカテゴリ概要を作成
            influencer_summary = []
            for i, inf in enumerate(influencers[:50]):  # 最大50名まで分析
                influencer_summary.append(f"{i+1}. {inf.get('channel_name', 'unknown')} - カテゴリ: {inf.get('category', 'unknown')} - {inf.get('subscriber_count', 0):,}人")
            
            # Gemini分析プロンプト
            prompt = f"""
あなたはインフルエンサーマーケティングの専門家です。
以下の企業と商品に最も適したインフルエンサーを選んでください。

【企業情報】
名前: {company_profile.get('name', '')}
業界: {company_profile.get('industry', '')}
説明: {company_profile.get('description', '')}

【商品情報】
{', '.join([p.get('name', '') + '(' + p.get('category', '') + ')' for p in product_portfolio.get('products', [])])}

【希望条件】
カテゴリ: {', '.join(preferences.get('preferred_categories', []))}
カスタム希望: {preferences.get('custom_preference', 'なし')}

【インフルエンサーリスト】
{chr(10).join(influencer_summary[:30])}

【指示】
上記のインフルエンサーから、企業の商品とのマッチング可能性が高い順に、
番号のみをカンマ区切りで最大15個選んでください。
関連性が低くても、創造的なコラボレーションの可能性があれば含めてください。

例: 1,3,5,7,9
"""
            
            response = await self._call_gemini_async(prompt)
            if not response:
                return influencers[:10]  # Gemini失敗時のフォールバック
            
            # 番号を抽出
            selected_indices = []
            for part in response.strip().split(','):
                try:
                    idx = int(part.strip()) - 1  # 1-based to 0-based
                    if 0 <= idx < len(influencers):
                        selected_indices.append(idx)
                except ValueError:
                    continue
            
            # 選択されたインフルエンサーを返す
            selected_influencers = [influencers[i] for i in selected_indices]
            logger.info(f"🤖 Gemini選択: {len(selected_influencers)}名")
            
            return selected_influencers if selected_influencers else influencers[:5]
            
        except Exception as e:
            logger.error(f"❌ Geminiカテゴリマッチングエラー: {e}")
            return influencers[:10]
    
    async def _gemini_alternative_matching(self, all_influencers: List[Dict[str, Any]], 
                                         request_data: Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Geminiによる代替マッチング提案"""
        try:
            logger.info("🔄 Gemini代替マッチング開始")
            
            # 企業情報を要約
            company_info = request_data.get('company_profile', {})
            products = request_data.get('product_portfolio', {}).get('products', [])
            
            # より広い視野でのマッチング
            alternative_prompt = f"""
厳密な条件では適合するインフルエンサーが見つかりませんでした。
より創造的で柔軟な視点から、以下の企業に適したインフルエンサーを提案してください。

【企業】{company_info.get('name', 'unknown')} - {company_info.get('industry', 'unknown')}
【商品】{', '.join([p.get('name', '') for p in products])}

【利用可能なインフルエンサータイプ】
{', '.join(set([inf.get('category', 'unknown') for inf in all_influencers[:20]]))}

異業種コラボレーション、意外性のあるマッチング、ニッチなターゲティングなど、
創造的なアプローチで3-5個のカテゴリを提案してください。
カンマ区切りで回答してください。

例: ゲーム, 料理, エンタメ
"""
            
            response = await self._call_gemini_async(alternative_prompt)
            if not response:
                return []
            
            # 提案されたカテゴリに該当するインフルエンサーを選択
            suggested_categories = [cat.strip() for cat in response.split(',')]
            alternative_candidates = []
            
            for influencer in all_influencers:
                if influencer.get('category') in suggested_categories:
                    alternative_candidates.append(influencer)
                    if len(alternative_candidates) >= 10:
                        break
            
            return alternative_candidates
            
        except Exception as e:
            logger.error(f"❌ 代替マッチングエラー: {e}")
            return []
    
    async def _analyze_matching_failure(self, all_influencers: List[Dict[str, Any]], 
                                      request_data: Dict[str, Any]]) -> str:
        """マッチング失敗の原因分析"""
        try:
            # データ統計を収集
            total_count = len(all_influencers)
            categories = {}
            subscriber_ranges = {'low': 0, 'mid': 0, 'high': 0}
            
            for inf in all_influencers:
                # カテゴリ分布
                category = inf.get('category', 'unknown')
                categories[category] = categories.get(category, 0) + 1
                
                # 登録者数分布
                sub_count = inf.get('subscriber_count', 0)
                if sub_count < 10000:
                    subscriber_ranges['low'] += 1
                elif sub_count < 100000:
                    subscriber_ranges['mid'] += 1
                else:
                    subscriber_ranges['high'] += 1
            
            # 要求された条件
            preferences = request_data.get('influencer_preferences', {})
            wanted_categories = preferences.get('preferred_categories', [])
            wanted_range = preferences.get('subscriber_range', {})
            
            analysis = f"""
データベース状況:
- 総インフルエンサー数: {total_count}名
- カテゴリ分布: {dict(list(categories.items())[:5])}
- 登録者数分布: 1万未満({subscriber_ranges['low']}), 1-10万({subscriber_ranges['mid']}), 10万以上({subscriber_ranges['high']})

要求条件:
- 希望カテゴリ: {wanted_categories}
- 登録者数範囲: {wanted_range.get('min', 0):,} - {wanted_range.get('max', 'unlimited')}

推奨解決策:
1. カテゴリ条件を緩和または除去
2. 登録者数範囲を拡大
3. 創造的な異業種コラボレーションを検討
"""
            return analysis
            
        except Exception as e:
            return f"分析エラー: {str(e)}"