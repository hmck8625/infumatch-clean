#!/usr/bin/env python3
"""
AIチャンネル分析サービス

@description データ取得時にリアルタイムでAI分析を実行
- カテゴリタグ自動付与
- チャンネル概要の構造化
- 商材マッチング分析

@author InfuMatch Development Team
@version 2.0.0
"""

import json
import asyncio
import re
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

import google.generativeai as genai

# Direct API key configuration for testing
# from core.config import get_settings
# settings = get_settings()


class AdvancedChannelAnalyzer:
    """
    高度なチャンネル分析AI
    
    データ取得時にリアルタイムで以下を分析:
    1. カテゴリタグ自動付与
    2. チャンネル概要の構造化
    3. 商材マッチング分析
    """
    
    def __init__(self):
        """初期化"""
        self.api_key = "AIzaSyDtPl5WSRdxk744ha5Tlwno4iTBZVO96r4"  # settings.GEMINI_API_KEY
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        # 商材カテゴリの定義
        self.product_categories = {
            "コスメ・美容": {
                "keywords": ["化粧品", "スキンケア", "ヘアケア", "美容機器"],
                "brands": ["資生堂", "DHC", "無印良品", "ニベア"],
                "price_range": "1,000-50,000円"
            },
            "ファッション": {
                "keywords": ["服", "アクセサリー", "バッグ", "靴"],
                "brands": ["ユニクロ", "GU", "ZARA", "H&M"],
                "price_range": "2,000-30,000円"
            },
            "食品・グルメ": {
                "keywords": ["食品", "調味料", "レストラン", "キッチン用品"],
                "brands": ["味の素", "キッコーマン", "カルビー"],
                "price_range": "500-10,000円"
            },
            "テクノロジー": {
                "keywords": ["スマホ", "PC", "ガジェット", "アプリ"],
                "brands": ["Apple", "Google", "Sony", "Nintendo"],
                "price_range": "5,000-200,000円"
            },
            "健康・フィットネス": {
                "keywords": ["サプリ", "運動器具", "ヘルスケア"],
                "brands": ["DHC", "ファンケル", "Nike", "Adidas"],
                "price_range": "3,000-50,000円"
            },
            "教育・学習": {
                "keywords": ["書籍", "オンライン講座", "学習ツール"],
                "brands": ["進研ゼミ", "Z会", "スタディサプリ"],
                "price_range": "1,000-20,000円"
            },
            "ライフスタイル": {
                "keywords": ["インテリア", "日用品", "雑貨"],
                "brands": ["IKEA", "ニトリ", "無印良品"],
                "price_range": "1,000-100,000円"
            },
            "エンタメ・ホビー": {
                "keywords": ["ゲーム", "音楽", "映画", "書籍"],
                "brands": ["Nintendo", "Sony", "Netflix"],
                "price_range": "1,000-30,000円"
            }
        }
    
    async def analyze_channel_comprehensive(self, channel_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        チャンネルの包括的AI分析
        
        Args:
            channel_data: YouTube APIから取得したチャンネルデータ
            
        Returns:
            Dict: 包括的分析結果
        """
        try:
            # 1. カテゴリタグ分析
            category_analysis = await self._analyze_category_tags(channel_data)
            
            # 2. チャンネル概要分析
            summary_analysis = await self._analyze_channel_summary(channel_data)
            
            # 3. 商材マッチング分析
            product_matching = await self._analyze_product_matching(channel_data)
            
            # 4. オーディエンス分析
            audience_analysis = await self._analyze_audience_profile(channel_data)
            
            # 5. ブランドセーフティ分析
            brand_safety = await self._analyze_brand_safety(channel_data)
            
            # 統合結果
            comprehensive_analysis = {
                "channel_id": channel_data.get("channel_id"),
                "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
                "category_tags": category_analysis,
                "channel_summary": summary_analysis,
                "product_matching": product_matching,
                "audience_profile": audience_analysis,
                "brand_safety": brand_safety,
                "analysis_confidence": self._calculate_overall_confidence([
                    category_analysis, summary_analysis, product_matching
                ])
            }
            
            return comprehensive_analysis
            
        except Exception as e:
            print(f"❌ 包括的分析エラー: {e}")
            return self._fallback_analysis(channel_data)
    
    async def _analyze_category_tags(self, channel_data: Dict[str, Any]) -> Dict[str, Any]:
        """カテゴリタグ自動付与"""
        try:
            prompt = self._create_category_prompt()
            input_text = self._prepare_channel_text(channel_data)
            
            response = await self._call_gemini_api(prompt, input_text)
            
            if response:
                return self._parse_category_response(response)
            else:
                return self._fallback_category_tags(channel_data)
                
        except Exception as e:
            print(f"❌ カテゴリ分析エラー: {e}")
            return self._fallback_category_tags(channel_data)
    
    async def _analyze_channel_summary(self, channel_data: Dict[str, Any]) -> Dict[str, Any]:
        """チャンネル概要の構造化分析"""
        try:
            prompt = self._create_summary_prompt()
            input_text = self._prepare_channel_text(channel_data)
            
            response = await self._call_gemini_api(prompt, input_text)
            
            if response:
                return self._parse_summary_response(response)
            else:
                return self._fallback_summary(channel_data)
                
        except Exception as e:
            print(f"❌ 概要分析エラー: {e}")
            return self._fallback_summary(channel_data)
    
    async def _analyze_product_matching(self, channel_data: Dict[str, Any]) -> Dict[str, Any]:
        """商材マッチング分析"""
        try:
            prompt = self._create_product_matching_prompt()
            input_text = self._prepare_channel_text(channel_data)
            
            response = await self._call_gemini_api(prompt, input_text)
            
            if response:
                return self._parse_product_matching_response(response)
            else:
                return self._fallback_product_matching(channel_data)
                
        except Exception as e:
            print(f"❌ 商材分析エラー: {e}")
            return self._fallback_product_matching(channel_data)
    
    async def _analyze_audience_profile(self, channel_data: Dict[str, Any]) -> Dict[str, Any]:
        """オーディエンス分析"""
        subscriber_count = channel_data.get("subscriber_count", 0)
        engagement_rate = channel_data.get("engagement_estimate", 0)
        
        # 統計的分析
        if subscriber_count < 50000:
            audience_size = "小規模（高エンゲージメント期待）"
        elif subscriber_count < 200000:
            audience_size = "中規模（バランス型）"
        else:
            audience_size = "大規模（リーチ重視）"
        
        engagement_level = "高" if engagement_rate > 5 else "中" if engagement_rate > 2 else "低"
        
        return {
            "audience_size": audience_size,
            "engagement_level": engagement_level,
            "estimated_demographics": self._estimate_demographics(channel_data),
            "reach_potential": self._calculate_reach_potential(channel_data)
        }
    
    async def _analyze_brand_safety(self, channel_data: Dict[str, Any]) -> Dict[str, Any]:
        """ブランドセーフティ分析"""
        try:
            prompt = self._create_brand_safety_prompt()
            input_text = self._prepare_channel_text(channel_data)
            
            response = await self._call_gemini_api(prompt, input_text)
            
            if response:
                return self._parse_brand_safety_response(response)
            else:
                return self._fallback_brand_safety(channel_data)
                
        except Exception as e:
            print(f"❌ ブランドセーフティ分析エラー: {e}")
            return self._fallback_brand_safety(channel_data)
    
    def _create_category_prompt(self) -> str:
        """カテゴリ分析用プロンプト"""
        return """
あなたはYouTubeチャンネルのカテゴリ分析の専門家です。
以下のチャンネル情報を分析し、適切なカテゴリタグを付与してください。

分析項目:
1. 主要カテゴリ（1つ）
2. サブカテゴリ（最大3つ）
3. コンテンツテーマ（最大5つ）
4. 対象年齢層
5. 信頼度スコア（0.0-1.0）

出力形式（JSON）:
{
  "primary_category": "メインカテゴリ",
  "sub_categories": ["サブカテゴリ1", "サブカテゴリ2"],
  "content_themes": ["テーマ1", "テーマ2", "テーマ3"],
  "target_age_group": "年齢層",
  "confidence_score": 0.95
}

チャンネル情報:
"""
    
    def _create_summary_prompt(self) -> str:
        """概要分析用プロンプト"""
        return """
あなたはマーケティング分析の専門家です。
以下のYouTubeチャンネル情報から、企業が知りたい重要な情報を構造化して抽出してください。

分析項目:
1. チャンネルの特徴（2-3文）
2. コンテンツスタイル
3. 更新頻度の推定
4. 専門性レベル
5. エンターテイメント性
6. 教育的価値

出力形式（JSON）:
{
  "channel_description": "チャンネルの特徴説明",
  "content_style": "コンテンツスタイル",
  "posting_frequency": "更新頻度推定",
  "expertise_level": "専門性レベル（高/中/低）",
  "entertainment_value": "エンタメ性（高/中/低）",
  "educational_value": "教育価値（高/中/低）"
}

チャンネル情報:
"""
    
    def _create_product_matching_prompt(self) -> str:
        """商材マッチング分析用プロンプト"""
        product_info = json.dumps(self.product_categories, ensure_ascii=False, indent=2)
        
        return f"""
あなたは商品マーケティングの専門家です。
以下のYouTubeチャンネル情報を分析し、どのような商材・ブランドとのコラボレーションが効果的かを判定してください。

商材カテゴリ:
{product_info}

分析項目:
1. 最適商材カテゴリ（上位3つ）
2. 推奨商品価格帯
3. マッチング理由
4. コラボレーション形式の提案
5. 期待効果

出力形式（JSON）:
{{
  "recommended_products": [
    {{
      "category": "商材カテゴリ",
      "price_range": "価格帯",
      "match_score": 0.95,
      "reasoning": "マッチング理由"
    }}
  ],
  "collaboration_formats": ["PR動画", "レビュー", "使用紹介"],
  "expected_impact": "期待される効果",
  "target_conversion": "想定コンバージョン率"
}}

チャンネル情報:
"""
    
    def _create_brand_safety_prompt(self) -> str:
        """ブランドセーフティ分析用プロンプト"""
        return """
あなたはブランドセーフティの専門家です。
以下のYouTubeチャンネル情報を分析し、企業コラボレーションの安全性を評価してください。

分析項目:
1. コンテンツの適切性
2. 炎上リスク
3. ブランドイメージへの影響
4. コンプライアンス適合性
5. 総合安全性スコア

出力形式（JSON）:
{
  "content_appropriateness": "適切性レベル（高/中/低）",
  "controversy_risk": "炎上リスク（低/中/高）",
  "brand_image_impact": "ブランドイメージ影響（正/中性/負）",
  "compliance_score": 0.95,
  "overall_safety_score": 0.90,
  "safety_notes": "安全性に関する注意事項"
}

チャンネル情報:
"""
    
    def _prepare_channel_text(self, channel_data: Dict[str, Any]) -> str:
        """チャンネル情報をテキスト形式で準備"""
        title = channel_data.get("channel_title", "")
        description = channel_data.get("description", "")
        subscriber_count = channel_data.get("subscriber_count", 0)
        video_count = channel_data.get("video_count", 0)
        category = channel_data.get("category", "")
        
        return f"""
チャンネル名: {title}
チャンネル概要: {description}
登録者数: {subscriber_count:,}人
動画数: {video_count}本
既存カテゴリ: {category}
"""
    
    async def _call_gemini_api(self, prompt: str, input_text: str, max_retries: int = 3) -> Optional[str]:
        """Gemini API呼び出し"""
        full_prompt = prompt + "\n" + input_text
        
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(
                    full_prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.1,
                        max_output_tokens=2048,
                    )
                )
                
                if response and response.text:
                    return response.text.strip()
                    
            except Exception as e:
                print(f"⚠️ Gemini API試行 {attempt + 1} 失敗: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                continue
        
        return None
    
    def _parse_category_response(self, response: str) -> Dict[str, Any]:
        """カテゴリ分析レスポンスをパース"""
        try:
            # JSONを抽出
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return self._fallback_category_tags({})
    
    def _parse_summary_response(self, response: str) -> Dict[str, Any]:
        """概要分析レスポンスをパース"""
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return self._fallback_summary({})
    
    def _parse_product_matching_response(self, response: str) -> Dict[str, Any]:
        """商材マッチングレスポンスをパース"""
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return self._fallback_product_matching({})
    
    def _parse_brand_safety_response(self, response: str) -> Dict[str, Any]:
        """ブランドセーフティレスポンスをパース"""
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        return self._fallback_brand_safety({})
    
    def _fallback_category_tags(self, channel_data: Dict[str, Any]) -> Dict[str, Any]:
        """フォールバック: カテゴリタグ"""
        category = channel_data.get("category", "その他")
        return {
            "primary_category": category,
            "sub_categories": [category],
            "content_themes": ["一般"],
            "target_age_group": "20-40代",
            "confidence_score": 0.5
        }
    
    def _fallback_summary(self, channel_data: Dict[str, Any]) -> Dict[str, Any]:
        """フォールバック: チャンネル概要"""
        return {
            "channel_description": "詳細分析が必要なチャンネルです",
            "content_style": "一般的なスタイル",
            "posting_frequency": "不明",
            "expertise_level": "中",
            "entertainment_value": "中",
            "educational_value": "中"
        }
    
    def _fallback_product_matching(self, channel_data: Dict[str, Any]) -> Dict[str, Any]:
        """フォールバック: 商材マッチング"""
        return {
            "recommended_products": [
                {
                    "category": "ライフスタイル",
                    "price_range": "1,000-10,000円",
                    "match_score": 0.6,
                    "reasoning": "一般的な商材との親和性"
                }
            ],
            "collaboration_formats": ["PR動画", "商品紹介"],
            "expected_impact": "中程度の効果が期待",
            "target_conversion": "2-5%"
        }
    
    def _fallback_brand_safety(self, channel_data: Dict[str, Any]) -> Dict[str, Any]:
        """フォールバック: ブランドセーフティ"""
        return {
            "content_appropriateness": "中",
            "controversy_risk": "低",
            "brand_image_impact": "中性",
            "compliance_score": 0.8,
            "overall_safety_score": 0.8,
            "safety_notes": "標準的な安全性レベル"
        }
    
    def _estimate_demographics(self, channel_data: Dict[str, Any]) -> Dict[str, str]:
        """推定人口統計"""
        category = channel_data.get("category", "")
        
        demographics_map = {
            "美容・コスメ": {"age": "20-35歳", "gender": "女性70%", "income": "中～高"},
            "gaming": {"age": "15-30歳", "gender": "男性60%", "income": "中"},
            "料理・グルメ": {"age": "25-45歳", "gender": "女性60%", "income": "中～高"},
            "ライフスタイル": {"age": "20-40歳", "gender": "女性55%", "income": "中"},
            "教育・学習": {"age": "20-50歳", "gender": "男女半々", "income": "中～高"}
        }
        
        return demographics_map.get(category, {"age": "20-40歳", "gender": "男女半々", "income": "中"})
    
    def _calculate_reach_potential(self, channel_data: Dict[str, Any]) -> str:
        """リーチポテンシャル計算"""
        subscribers = channel_data.get("subscriber_count", 0)
        engagement = channel_data.get("engagement_estimate", 0)
        
        if subscribers > 100000 and engagement > 3:
            return "非常に高い"
        elif subscribers > 50000 and engagement > 2:
            return "高い"
        elif subscribers > 10000 and engagement > 1:
            return "中程度"
        else:
            return "限定的"
    
    def _calculate_overall_confidence(self, analyses: List[Dict]) -> float:
        """全体の信頼度スコア計算"""
        confidence_scores = []
        for analysis in analyses:
            if isinstance(analysis, dict):
                confidence_scores.append(analysis.get("confidence_score", 0.5))
        
        return sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.5
    
    def _fallback_analysis(self, channel_data: Dict[str, Any]) -> Dict[str, Any]:
        """フォールバック: 全体分析"""
        return {
            "channel_id": channel_data.get("channel_id"),
            "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
            "category_tags": self._fallback_category_tags(channel_data),
            "channel_summary": self._fallback_summary(channel_data),
            "product_matching": self._fallback_product_matching(channel_data),
            "audience_profile": self._analyze_audience_profile(channel_data),
            "brand_safety": self._fallback_brand_safety(channel_data),
            "analysis_confidence": 0.5
        }