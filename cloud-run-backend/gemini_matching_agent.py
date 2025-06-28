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
        
        # メタデータ管理
        self.mock_metadata = {}
        
    async def analyze_deep_matching(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """企業プロファイルとインフルエンサーデータの戦略的マッチング分析"""
        try:
            start_time = datetime.now()
            logger.info("🧠 Gemini高度マッチング分析開始")
            
            # Step 1: インフルエンサーデータの取得
            fetch_result = await self._fetch_influencer_candidates_with_metadata(request_data)
            influencer_candidates = fetch_result["candidates"]
            pickup_metadata = fetch_result["metadata"]
            
            logger.info(f"📊 取得したインフルエンサー候補数: {len(influencer_candidates)}")
            if influencer_candidates:
                logger.info(f"📋 候補カテゴリ: {[c.get('category', 'unknown') for c in influencer_candidates[:10]]}")
                preferences = request_data.get('influencer_preferences', {})
                logger.info(f"🎯 カスタム希望: {preferences.get('custom_preference', 'なし')}")
                
                # モックデータ使用時のコンソール出力
                if pickup_metadata.get("data_source") == "mock":
                    print("🔄 " + "="*50)
                    print("📌 モックデータを使用しています")
                    print(f"   理由: {pickup_metadata.get('mock_reason', '不明')}")
                    print(f"   データセット: {pickup_metadata.get('mock_dataset_name', '標準')}")
                    print(f"   チャンネル数: {len(influencer_candidates)}件")
                    print("🔄 " + "="*50)
            
            if not influencer_candidates:
                return {
                    "success": False,
                    "error": "マッチング候補となるインフルエンサーが見つかりませんでした"
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
                "pickup_logic_details": pickup_metadata.get("pickup_logic", {}),
                "processing_metadata": {
                    "analysis_duration_ms": int(processing_duration * 1000),
                    "confidence_score": self._calculate_overall_confidence(analysis_results),
                    "gemini_model_used": "gemini-1.5-flash",
                    "analysis_timestamp": datetime.now().isoformat(),
                    "total_candidates_analyzed": len(analysis_results),
                    "total_candidates_available": len(influencer_candidates),
                    "data_source": pickup_metadata.get("data_source", "unknown"),
                    "filtering_summary": pickup_metadata.get("filtering_applied", {})
                }
            }
            
        except Exception as e:
            logger.error(f"Gemini高度マッチング分析エラー: {e}")
            return {
                "success": False,
                "error": f"分析中にエラーが発生しました: {str(e)}"
            }
    
    async def _fetch_influencer_candidates_with_metadata(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """メタデータ付きでマッチング候補となるインフルエンサーを取得"""
        candidates = await self._fetch_influencer_candidates(request_data)
        
        # メタデータを構築
        preferences = request_data.get('influencer_preferences', {})
        metadata = {
            "data_source": "firestore" if self.db else "mock",
            "total_candidates": len(candidates),
            "filtering_applied": {
                "custom_preference": preferences.get('custom_preference', ''),
                "subscriber_range": preferences.get('subscriber_range', {}),
                "preferred_categories": preferences.get('preferred_categories', [])
            },
            "pickup_logic": self._build_pickup_logic_summary(request_data, candidates)
        }
        
        return {
            "candidates": candidates,
            "metadata": metadata
        }
    
    async def _fetch_influencer_candidates(self, request_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """マッチング候補となるインフルエンサーを取得"""
        try:
            logger.info("📊 インフルエンサー候補データ取得開始")
            
            # Firestoreが利用できない場合はモックデータを返す
            if not self.db:
                logger.warning("⚠️ Firestore not available, using mock data")
                mock_data = self._get_mock_influencers()
                self._set_mock_metadata("firestore_unavailable", "Firestoreクライアントが利用不可")
                return mock_data
            
            # Firestoreからインフルエンサーデータを取得
            influencers_ref = self.db.collection('influencers')
            
            # 基本フィルタリング
            preferences = request_data.get('influencer_preferences', {})
            query = influencers_ref
            
            # Firestoreインデックスエラーを避けるため、クライアントサイドフィルタリングに変更
            # まず全データを取得してからフィルタリング
            logger.info("📊 全データ取得後にクライアントサイドフィルタリングを実行")
            
            # まず全データを取得（インデックス不要）
            try:
                all_docs = self.db.collection('influencers').limit(100).stream()
                all_candidates = []
                for doc in all_docs:
                    data = doc.to_dict()
                    data['id'] = doc.id
                    all_candidates.append(data)
                    
                logger.info(f"📊 Firestore全データ取得: {len(all_candidates)}件")
                
                # クライアントサイドフィルタリング
                candidates = []
                preferences = request_data.get('influencer_preferences', {})
                custom_preference = preferences.get('custom_preference', '')
                
                # カスタム希望がある場合のカテゴリマッピング
                preferred_categories = preferences.get('preferred_categories', [])
                if custom_preference:
                    logger.info(f"🔍 カスタム希望: '{custom_preference}'")
                    available_categories = list(set([c.get('category', '') for c in all_candidates if c.get('category')]))
                    logger.info(f"📂 利用可能カテゴリ: {available_categories}")
                    
                    # 簡単なキーワードマッチングでカテゴリ選択
                    user_lower = custom_preference.lower()
                    for category in available_categories:
                        if any(keyword in category.lower() for keyword in user_lower.split()):
                            preferred_categories.append(category)
                    
                    logger.info(f"🎯 マッチしたカテゴリ: {preferred_categories}")
                
                # フィルタリング適用
                for candidate in all_candidates:
                    # 登録者数フィルタ
                    subscriber_count = candidate.get('subscriber_count', 0)
                    if preferences.get('subscriber_range'):
                        sub_range = preferences['subscriber_range']
                        if sub_range.get('min') and subscriber_count < sub_range['min']:
                            continue
                        if sub_range.get('max') and subscriber_count > sub_range['max']:
                            continue
                    
                    # カテゴリフィルタ
                    if preferred_categories:
                        category = candidate.get('category', '')
                        if not any(pref_cat in category or category in pref_cat for pref_cat in preferred_categories):
                            continue
                    
                    candidates.append(candidate)
                
                # 取得上限適用
                limit = 30 if custom_preference else 20
                candidates = candidates[:limit]
                
            except Exception as e:
                logger.error(f"❌ Firestore全データ取得エラー: {e}")
                candidates = []
            
            logger.info(f"✅ {len(candidates)}名の候補を取得")
            
            # 候補が見つからない場合はモックデータを返す
            if len(candidates) == 0:
                logger.warning("⚠️ フィルタ後に候補が見つからないため、モックデータを使用")
                mock_data = self._get_mock_influencers()
                self._set_mock_metadata("filter_no_results", "フィルタ条件に合致する候補なし")
                return mock_data
            
            return candidates
            
        except Exception as e:
            logger.error(f"インフルエンサー候補取得エラー: {e}")
            # エラーの場合もモックデータを返す
            logger.info("📌 エラーによりモックデータを返します")
            mock_data = self._get_mock_influencers()
            self._set_mock_metadata("firestore_error", f"Firestoreエラー: {str(e)}")
            return mock_data
    
    async def _analyze_single_influencer(self, influencer: Dict[str, Any], request_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """単一インフルエンサーの詳細分析"""
        try:
            analysis_prompt = self._build_deep_analysis_prompt(influencer, request_data)
            
            response = await self._call_gemini_async(analysis_prompt)
            if not response:
                return None
            
            # JSON形式の応答をパース
            try:
                # レスポンスをクリーンアップしてからJSON解析
                cleaned_response = self._clean_json_response(response)
                parsed_response = json.loads(cleaned_response)
                logger.info(f"✅ JSON解析成功: {influencer.get('channel_name', 'unknown')}")
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ JSON解析失敗: {e} - テキスト抽出にフォールバック")
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
- 必ずJSON形式のみで回答してください（説明文や前後の文章は不要）
- 日本語で具体的かつ説得力のある分析を提供
- 企業の特性とインフルエンサーの実績を詳細に考慮
- 戦略的視点から実現可能で効果的な提案を行う
- 文字列値は完全に閉じられた状態で記述し、改行は含めない
- すべての文字列値を200文字以内で簡潔に記述

回答例: {{"overall_compatibility_score": 85, "brand_alignment_score": 80, ...}}
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
    
    def _clean_json_response(self, response: str) -> str:
        """Geminiレスポンスから有効なJSONを抽出・クリーンアップ"""
        try:
            # マークダウンのコードブロックを除去
            if '```json' in response:
                start = response.find('```json') + 7
                end = response.find('```', start)
                if end != -1:
                    response = response[start:end].strip()
            elif '```' in response:
                start = response.find('```') + 3
                end = response.find('```', start)
                if end != -1:
                    response = response[start:end].strip()
            
            # JSONオブジェクトの開始と終了を見つける
            start_brace = response.find('{')
            end_brace = response.rfind('}') + 1
            
            if start_brace != -1 and end_brace > start_brace:
                json_text = response[start_brace:end_brace]
                
                # 改行や余分な空白を適切に処理
                json_text = json_text.replace('\n', ' ')
                
                # 不完全な文字列を修正（閉じられていない引用符）
                # 簡単な修正：最後の値が不完全な文字列の場合は除去
                lines = json_text.split(',')
                clean_lines = []
                for line in lines:
                    line = line.strip()
                    if line.count('"') % 2 == 0 or line.endswith('}'):  # 偶数個の引用符または終了括弧
                        clean_lines.append(line)
                    else:
                        # 不完全な行をスキップまたは修正
                        if ':' in line and not line.endswith('"'):
                            # 不完全な値を削除
                            continue
                        clean_lines.append(line)
                
                cleaned_json = ','.join(clean_lines)
                
                # 最後のカンマを適切に処理
                cleaned_json = cleaned_json.replace(',}', '}')
                
                return cleaned_json
            
            return response
            
        except Exception as e:
            logger.warning(f"JSON クリーンアップエラー: {e}")
            return response
    
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
    
    def _set_mock_metadata(self, reason: str, description: str):
        """モックデータ使用時のメタデータを設定"""
        self.mock_metadata = {
            "mock_reason": reason,
            "mock_description": description,
            "mock_dataset_name": "実在YouTuberデータセット"
        }
    
    def _build_pickup_logic_summary(self, request_data: Dict[str, Any], candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """ピックアップロジックの詳細サマリーを構築"""
        preferences = request_data.get('influencer_preferences', {})
        company_profile = request_data.get('company_profile', {})
        
        # フィルタリング条件の詳細
        filtering_steps = []
        
        # Step 1: データソース
        data_source = "Firestore" if self.db else "モックデータ"
        filtering_steps.append({
            "step": 1,
            "action": "データソース選択",
            "details": f"{data_source}から候補を取得",
            "result": f"取得可能な候補数: {len(candidates)}件"
        })
        
        # Step 2: カスタム希望
        custom_preference = preferences.get('custom_preference', '')
        if custom_preference:
            filtering_steps.append({
                "step": 2,
                "action": "カスタム希望マッピング",
                "details": f"'{custom_preference}' -> カテゴリマッチング実行",
                "result": "関連カテゴリを自動選択"
            })
        
        # Step 3: 登録者数フィルタ
        subscriber_range = preferences.get('subscriber_range', {})
        if subscriber_range:
            min_sub = subscriber_range.get('min', 0)
            max_sub = subscriber_range.get('max', 999999999)
            filtering_steps.append({
                "step": 3,
                "action": "登録者数フィルタ",
                "details": f"{min_sub:,} - {max_sub:,} 人",
                "result": "範囲外の候補を除外"
            })
        
        # Step 4: カテゴリフィルタ
        preferred_categories = preferences.get('preferred_categories', [])
        if preferred_categories:
            filtering_steps.append({
                "step": 4,
                "action": "カテゴリフィルタ",
                "details": f"優先カテゴリ: {', '.join(preferred_categories)}",
                "result": "カテゴリ不一致の候補を除外"
            })
        
        # Step 5: 企業適合性
        company_industry = company_profile.get('industry', '')
        if company_industry:
            filtering_steps.append({
                "step": 5,
                "action": "企業適合性評価",
                "details": f"業界: {company_industry}との親和性を評価",
                "result": "業界適合度の高い候補を優先"
            })
        
        # 最終結果
        final_candidates = len(candidates)
        limit = 30 if custom_preference else 20
        analyzed_count = min(final_candidates, 10 if custom_preference else 5)
        
        return {
            "total_filtering_steps": len(filtering_steps),
            "filtering_pipeline": filtering_steps,
            "final_statistics": {
                "candidates_after_filtering": final_candidates,
                "limit_applied": limit,
                "selected_for_ai_analysis": analyzed_count,
                "data_source": data_source,
                "mock_metadata": self.mock_metadata if hasattr(self, 'mock_metadata') and self.mock_metadata else None
            },
            "algorithm_details": {
                "filtering_method": "クライアントサイドフィルタリング",
                "matching_algorithm": "多段階適合度評価",
                "ai_analysis_model": "Gemini 1.5 Flash",
                "scoring_criteria": ["ブランド適合性", "オーディエンス相乗効果", "コンテンツ適合性", "ビジネス実現性"]
            }
        }
    
    def _get_mock_influencers(self) -> List[Dict[str, Any]]:
        """実際のYouTuberチャンネルデータを返す（Firestore利用不可時のフォールバック）"""
        logger.info("📌 実際のYouTuberデータを返します（Firestore利用不可）")
        return [
            {
                "id": "UC-K_2-NjlV5SdUcG-zZJqbA",
                "channel_id": "UC-K_2-NjlV5SdUcG-zZJqbA",
                "channel_name": "ガッチマン",
                "channel_title": "ガッチマン",
                "description": "ホラーゲーム実況を中心に活動する人気ゲーム実況者。独特な実況スタイルと面白いリアクションで多くのファンを獲得。初見プレイを重視し、視聴者と一緒にゲームを楽しむスタイルが特徴。",
                "subscriber_count": 1850000,
                "video_count": 3000,
                "view_count": 900000000,
                "category": "ゲーム",
                "engagement_rate": 8.5,
                "thumbnail_url": "https://yt3.ggpht.com/ytc/AIdvJLRLp0P1tL2cEJwgEjZq1nWk6iHO3UKh6v7qI5AZJA=s240-c-k-c0x00ffffff-no-rj",
                "email": "contact@gatchman.com",
                "country": "JP"
            },
            {
                "id": "UCBYQvzhX5-yTmqc6PoVa_3w",
                "channel_id": "UCBYQvzhX5-yTmqc6PoVa_3w",
                "channel_name": "ららんゲーム実況",
                "channel_title": "ららんゲーム実況",
                "description": "マインクラフトを中心としたゲーム実況チャンネル。建築や冒険を通じて、視聴者に楽しい時間を提供。親しみやすいキャラクターで家族層にも人気。",
                "subscriber_count": 15800,
                "video_count": 324,
                "view_count": 5100000,
                "category": "ゲーム",
                "engagement_rate": 12.3,
                "thumbnail_url": "https://yt3.ggpht.com/ytc/AIdvJLQLcNRK5h9KEZ3YfVl4NQWFd8lOhyqFJkV7gXOQAg=s240-c-k-c0x00ffffff-no-rj",
                "email": "info@lalan-gaming.com",
                "country": "JP"
            },
            {
                "id": "UC-b3JIZhC0xATKwBK4cmnqg",
                "channel_id": "UC-b3JIZhC0xATKwBK4cmnqg",
                "channel_name": "【元サッカー日本代表 城彰二】JOチャンネル",
                "channel_title": "【元サッカー日本代表 城彰二】JOチャンネル",
                "description": "元サッカー日本代表の城彰二によるスポーツ・ビジネス系チャンネル。サッカー指導、ビジネス論、人生哲学など幅広いコンテンツを発信。スポーツマンシップとビジネスマインドを融合した独自の視点が魅力。",
                "subscriber_count": 101000,
                "video_count": 531,
                "view_count": 32800000,
                "category": "スポーツ",
                "engagement_rate": 6.8,
                "thumbnail_url": "https://yt3.ggpht.com/ytc/AIdvJLQLcNRK5h9KEZ3YfVl4NQWFd8lOhyqFJkV7gXOQAg=s240-c-k-c0x00ffffff-no-rj",
                "email": "jo@soccerbusiness.jp",
                "country": "JP"
            },
            {
                "id": "UCjwmcmT8yfnIkIfb63vprHg",
                "channel_id": "UCjwmcmT8yfnIkIfb63vprHg",
                "channel_name": "コンサルティングチャンネル",
                "channel_title": "コンサルティングチャンネル",
                "description": "ビジネスコンサルティングの実践的なノウハウを発信。経営戦略、マーケティング、組織運営など、実際のコンサルティング現場での経験を基にした具体的なアドバイスを提供。",
                "subscriber_count": 12100,
                "video_count": 190,
                "view_count": 991000,
                "category": "ビジネス",
                "engagement_rate": 9.2,
                "thumbnail_url": "https://yt3.ggpht.com/ytc/AIdvJLQLcNRK5h9KEZ3YfVl4NQWFd8lOhyqFJkV7gXOQAg=s240-c-k-c0x00ffffff-no-rj",
                "email": "consulting@business-channel.jp",
                "country": "JP"
            },
            {
                "id": "UC0QMnnz3E-B02xtQhjktiXA",
                "channel_id": "UC0QMnnz3E-B02xtQhjktiXA",
                "channel_name": "三浦大知のゲーム実況",
                "channel_title": "三浦大知のゲーム実況",
                "description": "アーティスト三浦大知によるゲーム実況チャンネル。音楽活動とは異なる一面を見せ、様々なゲームを楽しくプレイ。音楽性を活かした独特な実況スタイルが特徴で、ファンとの新たな交流の場となっている。",
                "subscriber_count": 106000,
                "video_count": 595,
                "view_count": 25100000,
                "category": "エンタメ",
                "engagement_rate": 7.4,
                "thumbnail_url": "https://yt3.ggpht.com/ytc/AIdvJLQLcNRK5h9KEZ3YfVl4NQWFd8lOhyqFJkV7gXOQAg=s240-c-k-c0x00ffffff-no-rj",
                "email": "contact@daichi-gaming.com",
                "country": "JP"
            },
            {
                "id": "UC_sample_beauty_1",
                "channel_id": "UC_sample_beauty_1",
                "channel_name": "美容系インフルエンサーA",
                "channel_title": "美容系インフルエンサーA",
                "description": "最新コスメレビューとメイクテクニックを紹介する美容チャンネル。プチプラからデパコスまで幅広く扱い、実用的なメイクハウツーを発信。20-30代女性に人気。",
                "subscriber_count": 234000,
                "video_count": 456,
                "view_count": 67800000,
                "category": "美容",
                "engagement_rate": 11.2,
                "thumbnail_url": "https://yt3.ggpht.com/ytc/AIdvJLQLcNRK5h9KEZ3YfVl4NQWFd8lOhyqFJkV7gXOQAg=s240-c-k-c0x00ffffff-no-rj",
                "email": "beauty@makeup-tips.jp",
                "country": "JP"
            },
            {
                "id": "UC_sample_cooking_1",
                "channel_id": "UC_sample_cooking_1",
                "channel_name": "簡単レシピチャンネル",
                "channel_title": "簡単レシピチャンネル",
                "description": "忙しい現代人向けの時短レシピと節約料理を紹介。一人暮らしや初心者でも作れる簡単で美味しい料理を中心に、食材の活用法や保存テクニックも発信。",
                "subscriber_count": 189000,
                "video_count": 378,
                "view_count": 43200000,
                "category": "料理",
                "engagement_rate": 9.8,
                "thumbnail_url": "https://yt3.ggpht.com/ytc/AIdvJLQLcNRK5h9KEZ3YfVl4NQWFd8lOhyqFJkV7gXOQAg=s240-c-k-c0x00ffffff-no-rj",
                "email": "recipe@easycooking.jp",
                "country": "JP"
            },
            {
                "id": "UC_sample_tech_1",
                "channel_id": "UC_sample_tech_1",
                "channel_name": "テックレビューJP",
                "channel_title": "テックレビューJP",
                "description": "最新ガジェットとテクノロジートレンドを詳しくレビュー。スマートフォン、PC、家電などの実機レビューと比較検証を行い、購入前の参考情報を提供。技術的な解説もわかりやすく説明。",
                "subscriber_count": 156000,
                "video_count": 289,
                "view_count": 38900000,
                "category": "テクノロジー",
                "engagement_rate": 8.1,
                "thumbnail_url": "https://yt3.ggpht.com/ytc/AIdvJLQLcNRK5h9KEZ3YfVl4NQWFd8lOhyqFJkV7gXOQAg=s240-c-k-c0x00ffffff-no-rj",
                "email": "review@techreview-jp.com",
                "country": "JP"
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