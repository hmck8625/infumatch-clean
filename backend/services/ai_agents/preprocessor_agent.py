"""
データ前処理エージェント（仮動作版）

@description YouTube チャンネルデータの分析・カテゴライズ・品質評価
メール抽出、エンゲージメント分析、コンテンツ分類を担当

@author InfuMatch Development Team
@version 1.0.0
"""

import logging
import json
import re
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import statistics

from .base_agent import BaseAgent, AgentConfig

logger = logging.getLogger(__name__)


class DataPreprocessorAgent(BaseAgent):
    """
    データ前処理エージェント
    
    YouTube チャンネルデータの分析・カテゴライズ・品質評価を実行
    """
    
    def __init__(self):
        """データ前処理エージェントの初期化"""
        config = AgentConfig(
            name="DataPreprocessorAgent",
            model_name="gemini-1.5-pro",
            temperature=0.3,  # 分析用に低めに設定
            max_output_tokens=2048,
            system_instruction=self._get_system_instruction()
        )
        super().__init__(config)
        
        # カテゴリ分類のキーワード辞書
        self.category_keywords = {
            "美容・ファッション": [
                "メイク", "コスメ", "スキンケア", "ファッション", "ヘアアレンジ",
                "makeup", "beauty", "fashion", "style", "cosmetics"
            ],
            "料理・グルメ": [
                "料理", "レシピ", "グルメ", "食べ歩き", "クッキング", "フード",
                "cooking", "recipe", "food", "gourmet", "餃子", "ラーメン"
            ],
            "ゲーム": [
                "ゲーム", "実況", "プレイ", "攻略", "gaming", "play", "stream",
                "apex", "valorant", "minecraft", "fortnite"
            ],
            "ライフスタイル": [
                "vlog", "日常", "ライフスタイル", "暮らし", "生活", "日記",
                "lifestyle", "daily", "routine"
            ],
            "エンタメ": [
                "エンタメ", "バラエティ", "お笑い", "comedy", "entertainment",
                "funny", "まとめ", "reaction", "リアクション"
            ],
            "教育・学習": [
                "教育", "学習", "勉強", "講座", "tutorial", "study", "education",
                "解説", "how to", "レッスン"
            ],
            "音楽": [
                "音楽", "歌", "楽器", "music", "song", "cover", "カバー",
                "ピアノ", "ギター", "弾き語り"
            ],
            "旅行": [
                "旅行", "観光", "travel", "trip", "海外", "国内", "グルメ旅"
            ]
        }
    
    def _get_system_instruction(self) -> str:
        """システムインストラクションを取得"""
        return """
あなたはYouTubeチャンネルデータの分析エキスパートです。

## 主な任務
1. チャンネル説明文からコンテンツカテゴリを特定
2. エンゲージメント率の分析と評価
3. ビジネス協業の可能性を評価
4. データ品質スコアの算出
5. インフルエンサーとしての適性判定

## 分析観点
- コンテンツの一貫性
- オーディエンスとの関係性
- 商用利用の可能性
- データの完全性と信頼性
- マーケティング価値

## 出力形式
分析結果は構造化されたJSONで返してください。
定性的な評価と定量的な指標を組み合わせて提供してください。
"""
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        データ前処理のメイン関数
        
        Args:
            input_data: 入力データ
            
        Returns:
            Dict: 処理結果
        """
        try:
            action = input_data.get("action", "analyze_channel")
            
            if action == "analyze_channel":
                return await self.analyze_channel(input_data)
            elif action == "categorize_channels":
                return await self.categorize_channels(input_data)
            elif action == "evaluate_quality":
                return await self.evaluate_data_quality(input_data)
            elif action == "extract_insights":
                return await self.extract_business_insights(input_data)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}"
                }
                
        except Exception as e:
            logger.error(f"❌ Data preprocessing failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def analyze_channel(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        チャンネル分析を実行
        
        Args:
            data: チャンネル情報
            
        Returns:
            Dict: 分析結果
        """
        try:
            channel = data.get("channel", {})
            
            # 基本情報の抽出
            channel_name = channel.get("channel_name", "")
            description = channel.get("description", "")
            subscriber_count = channel.get("subscriber_count", 0)
            video_count = channel.get("video_count", 0)
            view_count = channel.get("view_count", 0)
            
            # 各種分析を実行
            content_analysis = await self._analyze_content_type(description, channel_name)
            engagement_analysis = self._calculate_engagement_metrics(channel)
            business_potential = await self._evaluate_business_potential(channel)
            audience_analysis = await self._analyze_target_audience(description)
            
            # 総合評価
            overall_score = self._calculate_overall_score({
                "content": content_analysis,
                "engagement": engagement_analysis,
                "business": business_potential,
                "audience": audience_analysis
            })
            
            return {
                "success": True,
                "analysis": {
                    "channel_id": channel.get("channel_id"),
                    "content_analysis": content_analysis,
                    "engagement_analysis": engagement_analysis,
                    "business_potential": business_potential,
                    "audience_analysis": audience_analysis,
                    "overall_score": overall_score,
                    "recommendations": await self._generate_recommendations(
                        content_analysis, engagement_analysis, business_potential
                    )
                },
                "agent": self.config.name,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Channel analysis failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _analyze_content_type(self, description: str, channel_name: str) -> Dict[str, Any]:
        """
        コンテンツタイプの分析
        
        Args:
            description: チャンネル説明文
            channel_name: チャンネル名
            
        Returns:
            Dict: コンテンツ分析結果
        """
        # キーワードベースの分類
        keyword_scores = {}
        combined_text = (description + " " + channel_name).lower()
        
        for category, keywords in self.category_keywords.items():
            score = 0
            matched_keywords = []
            
            for keyword in keywords:
                if keyword.lower() in combined_text:
                    score += 1
                    matched_keywords.append(keyword)
            
            if score > 0:
                keyword_scores[category] = {
                    "score": score,
                    "matched_keywords": matched_keywords,
                    "confidence": min(score / len(keywords), 1.0)
                }
        
        # AIによる詳細分析
        prompt = f"""
        以下のYouTubeチャンネル情報を分析して、コンテンツの特徴を判定してください：
        
        ## チャンネル名
        {channel_name}
        
        ## 説明文
        {description}
        
        ## 分析項目
        1. 主要なコンテンツカテゴリ
        2. コンテンツの専門性レベル
        3. 更新頻度の推定
        4. ターゲット年齢層
        5. コンテンツの独自性
        
        JSONで返してください：
        {{
            "primary_category": "メインカテゴリ",
            "secondary_categories": ["サブカテゴリ1", "サブカテゴリ2"],
            "specialization_level": "high/medium/low",
            "estimated_upload_frequency": "daily/weekly/monthly",
            "target_age_group": "10-20/20-30/30-40/40+",
            "uniqueness_score": 0.0-1.0,
            "content_quality_indicators": ["指標1", "指標2"]
        }}
        """
        
        ai_response = await self.generate_response(prompt)
        
        if ai_response.get("success") and ai_response.get("parsed_content"):
            ai_analysis = ai_response["parsed_content"]
        else:
            ai_analysis = {}
        
        return {
            "keyword_classification": keyword_scores,
            "ai_analysis": ai_analysis,
            "primary_category": self._determine_primary_category(keyword_scores),
            "category_confidence": self._calculate_category_confidence(keyword_scores)
        }
    
    def _calculate_engagement_metrics(self, channel: Dict[str, Any]) -> Dict[str, Any]:
        """
        エンゲージメント指標の計算
        
        Args:
            channel: チャンネル情報
            
        Returns:
            Dict: エンゲージメント分析結果
        """
        subscriber_count = channel.get("subscriber_count", 0)
        video_count = channel.get("video_count", 0)
        view_count = channel.get("view_count", 0)
        
        # 基本指標の計算
        avg_views_per_video = view_count / max(video_count, 1)
        view_to_subscriber_ratio = avg_views_per_video / max(subscriber_count, 1)
        videos_per_subscriber = video_count / max(subscriber_count, 1)
        
        # エンゲージメント率の評価
        engagement_rate = view_to_subscriber_ratio * 100
        
        # スコア化
        engagement_score = self._score_engagement_rate(engagement_rate)
        consistency_score = self._score_content_consistency(video_count, view_count)
        growth_potential = self._estimate_growth_potential(channel)
        
        return {
            "basic_metrics": {
                "avg_views_per_video": round(avg_views_per_video),
                "view_to_subscriber_ratio": round(view_to_subscriber_ratio, 4),
                "videos_per_subscriber": round(videos_per_subscriber, 6),
                "engagement_rate_percent": round(engagement_rate, 2)
            },
            "scores": {
                "engagement_score": engagement_score,
                "consistency_score": consistency_score,
                "growth_potential": growth_potential
            },
            "evaluation": self._evaluate_engagement_level(engagement_rate),
            "benchmarks": self._get_engagement_benchmarks(subscriber_count)
        }
    
    async def _evaluate_business_potential(self, channel: Dict[str, Any]) -> Dict[str, Any]:
        """
        ビジネスポテンシャルの評価
        
        Args:
            channel: チャンネル情報
            
        Returns:
            Dict: ビジネス評価結果
        """
        emails = channel.get("emails", [])
        has_business_email = channel.get("has_business_email", False)
        description = channel.get("description", "")
        
        # メール情報の評価
        email_score = self._evaluate_email_accessibility(emails)
        
        # 商業的利用の兆候を検出
        commercial_indicators = self._detect_commercial_indicators(description)
        
        # 協業の実績を確認
        collaboration_history = self._analyze_collaboration_history(description)
        
        # AIによる総合評価
        prompt = f"""
        YouTubeチャンネルのビジネス協業ポテンシャルを評価してください：
        
        ## チャンネル情報
        - 登録者数: {channel.get('subscriber_count', 0):,}人
        - ビジネスメール: {'あり' if has_business_email else 'なし'}
        - 説明文: {description[:500]}...
        
        ## 評価観点
        1. 企業とのコラボ経験
        2. プロモーション受入れの姿勢
        3. オーディエンスの商品購買意欲
        4. チャンネルの信頼性
        5. 長期パートナーシップの可能性
        
        1-10点で評価してJSONで返してください：
        {{
            "collaboration_readiness": 評価点,
            "audience_commercial_value": 評価点,
            "channel_credibility": 評価点,
            "partnership_potential": 評価点,
            "overall_business_score": 評価点,
            "risk_factors": ["リスク要因1", "リスク要因2"],
            "advantages": ["強み1", "強み2"]
        }}
        """
        
        ai_response = await self.generate_response(prompt)
        ai_evaluation = ai_response.get("parsed_content", {}) if ai_response.get("success") else {}
        
        return {
            "email_accessibility": email_score,
            "commercial_indicators": commercial_indicators,
            "collaboration_history": collaboration_history,
            "ai_evaluation": ai_evaluation,
            "business_readiness_score": self._calculate_business_readiness(
                email_score, commercial_indicators, ai_evaluation
            )
        }
    
    async def _analyze_target_audience(self, description: str) -> Dict[str, Any]:
        """
        ターゲットオーディエンスの分析
        
        Args:
            description: チャンネル説明文
            
        Returns:
            Dict: オーディエンス分析結果
        """
        prompt = f"""
        YouTubeチャンネルの説明文から、ターゲットオーディエンスを分析してください：
        
        ## 説明文
        {description}
        
        ## 分析項目
        1. 主要な視聴者層（年齢・性別）
        2. 関心事・趣味
        3. 購買力レベル
        4. ライフスタイル
        5. マーケティング価値
        
        JSONで返してください：
        {{
            "primary_demographics": {{
                "age_range": "主要年齢層",
                "gender_split": "性別比率の推定",
                "location": "地域特性"
            }},
            "interests": ["関心事1", "関心事2"],
            "purchasing_power": "high/medium/low",
            "lifestyle_characteristics": ["特徴1", "特徴2"],
            "marketing_value": {{
                "brand_affinity": 0.0-1.0,
                "influence_level": 0.0-1.0,
                "commercial_receptivity": 0.0-1.0
            }}
        }}
        """
        
        ai_response = await self.generate_response(prompt)
        
        return {
            "ai_analysis": ai_response.get("parsed_content", {}),
            "demographic_score": self._calculate_demographic_appeal(description),
            "market_segment": self._identify_market_segment(description)
        }
    
    def _determine_primary_category(self, keyword_scores: Dict[str, Any]) -> str:
        """主要カテゴリの決定"""
        if not keyword_scores:
            return "その他"
        
        # 最高スコアのカテゴリを選択
        best_category = max(keyword_scores.items(), key=lambda x: x[1]["score"])
        return best_category[0] if best_category[1]["score"] > 0 else "その他"
    
    def _calculate_category_confidence(self, keyword_scores: Dict[str, Any]) -> float:
        """カテゴリ分類の信頼度計算"""
        if not keyword_scores:
            return 0.0
        
        scores = [data["score"] for data in keyword_scores.values()]
        max_score = max(scores) if scores else 0
        total_score = sum(scores)
        
        # 最高スコアが全体に占める割合で信頼度を算出
        confidence = max_score / max(total_score, 1)
        return round(confidence, 2)
    
    def _score_engagement_rate(self, engagement_rate: float) -> float:
        """エンゲージメント率のスコア化"""
        if engagement_rate >= 10.0:
            return 1.0
        elif engagement_rate >= 5.0:
            return 0.8
        elif engagement_rate >= 2.0:
            return 0.6
        elif engagement_rate >= 1.0:
            return 0.4
        else:
            return 0.2
    
    def _score_content_consistency(self, video_count: int, view_count: int) -> float:
        """コンテンツ一貫性のスコア化"""
        if video_count == 0:
            return 0.0
        
        # 動画数が多いほど、ビューの分散が小さいほど高スコア
        consistency_factor = min(video_count / 50, 1.0)  # 50本を基準
        
        # 単純化した一貫性スコア
        return consistency_factor * 0.8 + 0.2
    
    def _estimate_growth_potential(self, channel: Dict[str, Any]) -> float:
        """成長ポテンシャルの推定"""
        subscriber_count = channel.get("subscriber_count", 0)
        video_count = channel.get("video_count", 0)
        
        # マイクロインフルエンサーの成長余地を評価
        if 1000 <= subscriber_count <= 10000:
            base_score = 0.8  # 高い成長余地
        elif 10000 <= subscriber_count <= 50000:
            base_score = 0.6  # 中程度の成長余地
        else:
            base_score = 0.4  # 限定的な成長余地
        
        # 動画数による補正
        video_factor = min(video_count / 100, 1.0)
        
        return round(base_score * video_factor, 2)
    
    def _evaluate_engagement_level(self, engagement_rate: float) -> str:
        """エンゲージメントレベルの評価"""
        if engagement_rate >= 10.0:
            return "非常に高い"
        elif engagement_rate >= 5.0:
            return "高い"
        elif engagement_rate >= 2.0:
            return "標準"
        elif engagement_rate >= 1.0:
            return "やや低い"
        else:
            return "低い"
    
    def _get_engagement_benchmarks(self, subscriber_count: int) -> Dict[str, float]:
        """登録者数別のエンゲージメントベンチマーク"""
        if subscriber_count < 10000:
            return {"excellent": 8.0, "good": 4.0, "average": 2.0}
        elif subscriber_count < 50000:
            return {"excellent": 6.0, "good": 3.0, "average": 1.5}
        else:
            return {"excellent": 4.0, "good": 2.0, "average": 1.0}
    
    def _evaluate_email_accessibility(self, emails: List[Dict[str, Any]]) -> float:
        """メールアクセシビリティの評価"""
        if not emails:
            return 0.0
        
        # ビジネスメールの有無と優先度で評価
        business_emails = [e for e in emails if e.get("is_business", False)]
        
        if business_emails:
            # 最高優先度のビジネスメールのスコア
            max_priority = max(e.get("priority", 0) for e in business_emails)
            return min(max_priority / 10.0, 1.0)
        else:
            # 一般メールがある場合の最低スコア
            return 0.3
    
    def _detect_commercial_indicators(self, description: str) -> Dict[str, Any]:
        """商業的利用の兆候を検出"""
        commercial_keywords = [
            "コラボ", "PR", "広告", "スポンサー", "プロモーション", "タイアップ",
            "collaboration", "sponsored", "partnership", "business"
        ]
        
        description_lower = description.lower()
        detected_keywords = [kw for kw in commercial_keywords if kw.lower() in description_lower]
        
        return {
            "has_commercial_keywords": len(detected_keywords) > 0,
            "detected_keywords": detected_keywords,
            "commercial_readiness_score": min(len(detected_keywords) / 5.0, 1.0)
        }
    
    def _analyze_collaboration_history(self, description: str) -> Dict[str, Any]:
        """協業履歴の分析"""
        # 企業名や商品名のパターンを検索
        brand_patterns = [
            r"@\w+",  # メンション
            r"#\w+",  # ハッシュタグ
            r"株式会社\w+",  # 日本企業
            r"\w+\s*×\s*\w+",  # コラボ表記
        ]
        
        collaborations = []
        for pattern in brand_patterns:
            matches = re.findall(pattern, description)
            collaborations.extend(matches)
        
        return {
            "potential_collaborations": collaborations,
            "collaboration_count": len(collaborations),
            "collaboration_experience_score": min(len(collaborations) / 3.0, 1.0)
        }
    
    def _calculate_business_readiness(
        self, 
        email_score: float, 
        commercial_indicators: Dict[str, Any], 
        ai_evaluation: Dict[str, Any]
    ) -> float:
        """ビジネス準備度の総合計算"""
        # 各要素の重み付け
        email_weight = 0.4
        commercial_weight = 0.3
        ai_weight = 0.3
        
        commercial_score = commercial_indicators.get("commercial_readiness_score", 0.0)
        ai_score = ai_evaluation.get("overall_business_score", 5) / 10.0
        
        total_score = (
            email_score * email_weight +
            commercial_score * commercial_weight +
            ai_score * ai_weight
        )
        
        return round(total_score, 2)
    
    def _calculate_demographic_appeal(self, description: str) -> float:
        """人口統計学的魅力度の計算"""
        # 簡易的な評価ロジック
        appeal_keywords = [
            "女性", "男性", "学生", "社会人", "主婦", "若者", "シニア",
            "ファミリー", "カップル", "一人暮らし"
        ]
        
        description_lower = description.lower()
        matched = sum(1 for kw in appeal_keywords if kw in description_lower)
        
        return min(matched / 3.0, 1.0)
    
    def _identify_market_segment(self, description: str) -> str:
        """市場セグメントの特定"""
        segments = {
            "ライフスタイル": ["日常", "暮らし", "生活"],
            "エンタメ": ["エンタメ", "面白い", "笑い"],
            "教育": ["勉強", "学習", "講座"],
            "ファッション": ["ファッション", "おしゃれ", "コーデ"],
            "グルメ": ["料理", "食べ物", "グルメ"]
        }
        
        description_lower = description.lower()
        
        for segment, keywords in segments.items():
            if any(kw in description_lower for kw in keywords):
                return segment
        
        return "一般"
    
    def _calculate_overall_score(self, analysis_results: Dict[str, Any]) -> float:
        """総合スコアの計算"""
        # 各分析結果から代表スコアを抽出
        content_score = analysis_results["content"].get("category_confidence", 0.0)
        
        engagement_scores = analysis_results["engagement"]["scores"]
        engagement_score = statistics.mean([
            engagement_scores["engagement_score"],
            engagement_scores["consistency_score"],
            engagement_scores["growth_potential"]
        ])
        
        business_score = analysis_results["business"].get("business_readiness_score", 0.0)
        
        audience_score = analysis_results["audience"].get("demographic_score", 0.0)
        
        # 重み付き平均
        weights = {"content": 0.2, "engagement": 0.4, "business": 0.3, "audience": 0.1}
        
        overall = (
            content_score * weights["content"] +
            engagement_score * weights["engagement"] +
            business_score * weights["business"] +
            audience_score * weights["audience"]
        )
        
        return round(overall, 2)
    
    async def _generate_recommendations(
        self, 
        content_analysis: Dict[str, Any], 
        engagement_analysis: Dict[str, Any], 
        business_potential: Dict[str, Any]
    ) -> List[str]:
        """改善提案の生成"""
        recommendations = []
        
        # エンゲージメント率に基づく提案
        engagement_rate = engagement_analysis["basic_metrics"]["engagement_rate_percent"]
        if engagement_rate < 2.0:
            recommendations.append("エンゲージメント率向上のため、視聴者との交流を増やすことを推奨")
        
        # ビジネスメールに基づく提案
        if not business_potential.get("email_accessibility", 0) > 0.5:
            recommendations.append("ビジネス連絡先を明確にすることでコラボ機会を増やせます")
        
        # カテゴリ特定に基づく提案
        if content_analysis.get("category_confidence", 0) < 0.5:
            recommendations.append("コンテンツの専門性を明確化することで、ターゲットオーディエンスを絞り込めます")
        
        return recommendations
    
    async def categorize_channels(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """複数チャンネルの一括カテゴライズ"""
        channels = data.get("channels", [])
        
        categorized_results = []
        
        for channel in channels:
            try:
                analysis_result = await self.analyze_channel({"channel": channel})
                if analysis_result.get("success"):
                    categorized_results.append({
                        "channel_id": channel.get("channel_id"),
                        "channel_name": channel.get("channel_name"),
                        "category": analysis_result["analysis"]["content_analysis"]["primary_category"],
                        "confidence": analysis_result["analysis"]["content_analysis"]["category_confidence"],
                        "overall_score": analysis_result["analysis"]["overall_score"]
                    })
            except Exception as e:
                logger.error(f"❌ Failed to categorize channel {channel.get('channel_id')}: {e}")
                continue
        
        return {
            "success": True,
            "categorized_channels": categorized_results,
            "total_processed": len(categorized_results),
            "agent": self.config.name,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def evaluate_data_quality(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """データ品質評価"""
        channel = data.get("channel", {})
        
        quality_checks = {
            "basic_info_completeness": self._check_basic_info(channel),
            "statistical_validity": self._check_statistics(channel),
            "email_quality": self._check_email_quality(channel),
            "content_richness": self._check_content_richness(channel)
        }
        
        overall_quality = statistics.mean(quality_checks.values())
        
        return {
            "success": True,
            "quality_assessment": {
                "individual_checks": quality_checks,
                "overall_quality_score": round(overall_quality, 2),
                "quality_grade": self._grade_quality(overall_quality),
                "improvement_suggestions": self._generate_quality_improvements(quality_checks)
            },
            "agent": self.config.name,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _check_basic_info(self, channel: Dict[str, Any]) -> float:
        """基本情報の完全性チェック"""
        required_fields = ["channel_name", "description", "thumbnail_url"]
        present_fields = sum(1 for field in required_fields if channel.get(field))
        return present_fields / len(required_fields)
    
    def _check_statistics(self, channel: Dict[str, Any]) -> float:
        """統計情報の妥当性チェック"""
        subscriber_count = channel.get("subscriber_count", 0)
        video_count = channel.get("video_count", 0)
        view_count = channel.get("view_count", 0)
        
        if subscriber_count == 0 or video_count == 0:
            return 0.0
        
        # 基本的な妥当性チェック
        avg_views = view_count / video_count
        reasonable_ratio = 0.1 <= avg_views / subscriber_count <= 10.0
        
        return 1.0 if reasonable_ratio else 0.5
    
    def _check_email_quality(self, channel: Dict[str, Any]) -> float:
        """メール品質チェック"""
        emails = channel.get("emails", [])
        if not emails:
            return 0.0
        
        has_business_email = any(e.get("is_business", False) for e in emails)
        return 1.0 if has_business_email else 0.5
    
    def _check_content_richness(self, channel: Dict[str, Any]) -> float:
        """コンテンツ充実度チェック"""
        description = channel.get("description", "")
        video_count = channel.get("video_count", 0)
        
        description_score = min(len(description) / 200, 1.0)  # 200文字を基準
        video_score = min(video_count / 50, 1.0)  # 50本を基準
        
        return (description_score + video_score) / 2
    
    def _grade_quality(self, score: float) -> str:
        """品質グレードの判定"""
        if score >= 0.9:
            return "A"
        elif score >= 0.7:
            return "B"
        elif score >= 0.5:
            return "C"
        else:
            return "D"
    
    def _generate_quality_improvements(self, quality_checks: Dict[str, float]) -> List[str]:
        """品質改善提案の生成"""
        improvements = []
        
        if quality_checks["basic_info_completeness"] < 0.8:
            improvements.append("基本情報（名前、説明、サムネイル）の完全性を向上")
        
        if quality_checks["statistical_validity"] < 0.8:
            improvements.append("統計データの妥当性確認と再取得")
        
        if quality_checks["email_quality"] < 0.5:
            improvements.append("ビジネス連絡先の取得")
        
        if quality_checks["content_richness"] < 0.6:
            improvements.append("チャンネル情報の充実化")
        
        return improvements
    
    async def extract_business_insights(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """ビジネスインサイトの抽出"""
        channels = data.get("channels", [])
        
        if not channels:
            return {"success": False, "error": "No channels provided"}
        
        # 集計分析
        total_channels = len(channels)
        with_business_emails = sum(1 for ch in channels if ch.get("has_business_email", False))
        avg_engagement = statistics.mean([ch.get("engagement_rate", 0) for ch in channels])
        
        # カテゴリ分布
        categories = {}
        for channel in channels:
            # 簡易カテゴリ分類
            description = channel.get("description", "").lower()
            category = "その他"
            for cat, keywords in self.category_keywords.items():
                if any(kw.lower() in description for kw in keywords):
                    category = cat
                    break
            categories[category] = categories.get(category, 0) + 1
        
        return {
            "success": True,
            "business_insights": {
                "summary_statistics": {
                    "total_channels_analyzed": total_channels,
                    "channels_with_business_email": with_business_emails,
                    "business_email_rate": round(with_business_emails / total_channels, 2),
                    "average_engagement_rate": round(avg_engagement, 2)
                },
                "category_distribution": categories,
                "top_opportunities": self._identify_top_opportunities(channels),
                "market_trends": self._analyze_market_trends(channels)
            },
            "agent": self.config.name,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _identify_top_opportunities(self, channels: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """トップ機会の特定"""
        # ビジネスメールありかつ高エンゲージメントのチャンネル
        opportunities = []
        
        for channel in channels:
            if (channel.get("has_business_email", False) and 
                channel.get("engagement_rate", 0) > 3.0):
                opportunities.append({
                    "channel_id": channel.get("channel_id"),
                    "channel_name": channel.get("channel_name"),
                    "subscriber_count": channel.get("subscriber_count", 0),
                    "engagement_rate": channel.get("engagement_rate", 0),
                    "opportunity_score": self._calculate_opportunity_score(channel)
                })
        
        # スコア順でソート
        opportunities.sort(key=lambda x: x["opportunity_score"], reverse=True)
        return opportunities[:10]  # トップ10
    
    def _calculate_opportunity_score(self, channel: Dict[str, Any]) -> float:
        """機会スコアの計算"""
        subscriber_count = channel.get("subscriber_count", 0)
        engagement_rate = channel.get("engagement_rate", 0)
        has_business_email = channel.get("has_business_email", False)
        
        # 基本スコア
        subscriber_score = min(subscriber_count / 50000, 1.0)
        engagement_score = min(engagement_rate / 10.0, 1.0)
        email_score = 1.0 if has_business_email else 0.0
        
        return (subscriber_score * 0.4 + engagement_score * 0.4 + email_score * 0.2)
    
    def _analyze_market_trends(self, channels: List[Dict[str, Any]]) -> Dict[str, Any]:
        """市場トレンドの分析"""
        # 登録者数の分布
        subscriber_ranges = {
            "1K-5K": sum(1 for ch in channels if 1000 <= ch.get("subscriber_count", 0) < 5000),
            "5K-10K": sum(1 for ch in channels if 5000 <= ch.get("subscriber_count", 0) < 10000),
            "10K-50K": sum(1 for ch in channels if 10000 <= ch.get("subscriber_count", 0) < 50000),
            "50K+": sum(1 for ch in channels if ch.get("subscriber_count", 0) >= 50000)
        }
        
        # エンゲージメント率の傾向
        engagement_rates = [ch.get("engagement_rate", 0) for ch in channels if ch.get("engagement_rate", 0) > 0]
        avg_engagement = statistics.mean(engagement_rates) if engagement_rates else 0
        median_engagement = statistics.median(engagement_rates) if engagement_rates else 0
        
        return {
            "subscriber_distribution": subscriber_ranges,
            "engagement_trends": {
                "average_engagement_rate": round(avg_engagement, 2),
                "median_engagement_rate": round(median_engagement, 2),
                "high_engagement_count": sum(1 for rate in engagement_rates if rate > 5.0)
            },
            "business_readiness": {
                "channels_with_emails": sum(1 for ch in channels if ch.get("emails")),
                "business_email_adoption": sum(1 for ch in channels if ch.get("has_business_email", False))
            }
        }
    
    def get_capabilities(self) -> List[str]:
        """エージェントの機能一覧"""
        return [
            "チャンネルコンテンツ分析",
            "カテゴリ自動分類",
            "エンゲージメント率評価",
            "ビジネスポテンシャル評価",
            "データ品質チェック",
            "ターゲットオーディエンス分析",
            "改善提案生成",
            "市場トレンド分析"
        ]