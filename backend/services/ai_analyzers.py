"""
AI分析サービス

@description Vertex AI/Gemini を活用した高度な分析機能
カテゴリ分析、トレンド分析、メール抽出の AI エージェント

@author InfuMatch Development Team  
@version 1.0.0
"""

import logging
import asyncio
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta

import google.generativeai as genai
# from google.cloud import aiplatform  # 使用しない場合はコメントアウト
# from google.oauth2 import service_account  # 使用しない場合はコメントアウト

from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class GeminiClient:
    """
    Gemini API クライアント
    
    高精度な自然言語処理による分析
    """
    
    def __init__(self):
        """初期化"""
        self.api_key = settings.GEMINI_API_KEY
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        # 安全設定
        self.safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH", 
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ]
        
        logger.info("✅ Gemini client initialized")
    
    async def analyze_text(
        self,
        prompt: str,
        text: str,
        max_retries: int = 3
    ) -> Optional[str]:
        """
        テキスト分析の実行
        
        Args:
            prompt: 分析指示プロンプト
            text: 分析対象テキスト
            max_retries: 最大リトライ回数
            
        Returns:
            Optional[str]: 分析結果
        """
        full_prompt = f"{prompt}\n\n分析対象:\n{text}"
        
        for attempt in range(max_retries):
            try:
                response = await asyncio.to_thread(
                    self.model.generate_content,
                    full_prompt,
                    safety_settings=self.safety_settings,
                    generation_config={
                        'temperature': 0.1,  # 一貫性を重視
                        'top_p': 0.8,
                        'top_k': 40,
                        'max_output_tokens': 2048,
                    }
                )
                
                if response.text:
                    return response.text.strip()
                else:
                    logger.warning("⚠️ Empty response from Gemini")
                    
            except Exception as e:
                logger.warning(f"⚠️ Gemini API attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # 指数バックオフ
                continue
        
        logger.error("❌ All Gemini API attempts failed")
        return None


class CategoryAnalyzer:
    """
    YouTubeチャンネルのカテゴリ分析エージェント
    
    AI を活用した高精度カテゴリ判定とサブカテゴリ特定
    """
    
    def __init__(self):
        """初期化"""
        self.gemini = GeminiClient()
        
        # 主要カテゴリの定義
        self.main_categories = {
            'beauty': {
                'name': 'ビューティー・コスメ',
                'subcategories': ['メイク', 'スキンケア', 'ヘアケア', 'ネイル', '香水']
            },
            'gaming': {
                'name': 'ゲーム',
                'subcategories': ['実況', '攻略', 'レビュー', 'eスポーツ', 'レトロゲーム']
            },
            'cooking': {
                'name': '料理・グルメ',
                'subcategories': ['レシピ', 'ベーキング', 'レストラン', 'お酒', '食レポ']
            },
            'tech': {
                'name': 'テクノロジー',
                'subcategories': ['ガジェット', 'レビュー', 'プログラミング', 'AI', 'スマホ']
            },
            'lifestyle': {
                'name': 'ライフスタイル',
                'subcategories': ['VLOG', '日常', 'ミニマリスト', 'インテリア', 'ペット']
            },
            'education': {
                'name': '教育・学習',
                'subcategories': ['語学', '勉強法', '資格', '歴史', '科学']
            },
            'fitness': {
                'name': 'フィットネス・健康',
                'subcategories': ['筋トレ', 'ヨガ', 'ダイエット', '健康食品', 'ランニング']
            },
            'fashion': {
                'name': 'ファッション',
                'subcategories': ['コーディネート', 'ブランド', 'プチプラ', 'アクセサリー', '古着']
            },
            'travel': {
                'name': '旅行',
                'subcategories': ['海外旅行', '国内旅行', 'グルメ旅', '一人旅', 'バックパック']
            },
            'business': {
                'name': 'ビジネス・起業',
                'subcategories': ['起業', '投資', 'マーケティング', '副業', 'キャリア']
            }
        }
    
    async def analyze_channel_category(
        self,
        channel_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        チャンネルの詳細カテゴリ分析
        
        Args:
            channel_data: チャンネル情報
            
        Returns:
            Dict: カテゴリ分析結果
        """
        try:
            # 分析用テキストの準備
            analysis_text = self._prepare_analysis_text(channel_data)
            
            # プロンプト作成
            prompt = self._create_category_prompt()
            
            # AI分析実行
            result = await self.gemini.analyze_text(prompt, analysis_text)
            
            if not result:
                return self._fallback_category_analysis(channel_data)
            
            # 結果パース
            analysis = self._parse_category_result(result)
            
            # 信頼度計算
            confidence = self._calculate_confidence(analysis, channel_data)
            analysis['confidence'] = confidence
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Category analysis failed: {e}")
            return self._fallback_category_analysis(channel_data)
    
    def _prepare_analysis_text(self, channel_data: Dict[str, Any]) -> str:
        """分析用テキストの準備"""
        texts = []
        
        # チャンネル名
        if channel_data.get('channel_name'):
            texts.append(f"チャンネル名: {channel_data['channel_name']}")
        
        # 説明文
        if channel_data.get('description'):
            # 長すぎる場合は先頭部分のみ
            desc = channel_data['description'][:1000]
            texts.append(f"説明文: {desc}")
        
        # 最新動画のタイトル
        if channel_data.get('recent_videos'):
            video_titles = [v.get('title', '') for v in channel_data['recent_videos'][:5]]
            if video_titles:
                texts.append(f"最新動画: {', '.join(video_titles)}")
        
        # カスタムURL
        if channel_data.get('custom_url'):
            texts.append(f"URL: {channel_data['custom_url']}")
        
        return '\n'.join(texts)
    
    def _create_category_prompt(self) -> str:
        """カテゴリ分析用プロンプト作成"""
        categories_list = '\n'.join([
            f"- {key}: {value['name']} ({', '.join(value['subcategories'])})"
            for key, value in self.main_categories.items()
        ])
        
        return f"""
あなたは YouTube チャンネルの専門分析者です。
以下のチャンネル情報から、最も適切なカテゴリとサブカテゴリを判定してください。

利用可能なカテゴリ:
{categories_list}

分析指示:
1. メインカテゴリを1つ選択（上記から必ず選択）
2. サブカテゴリを1-3個特定
3. カテゴリの理由を具体的に説明
4. コラボレーション適性度を5段階評価
5. ターゲット層を推定

出力形式（JSON）:
{{
    "main_category": "カテゴリキー",
    "main_category_name": "カテゴリ名",
    "sub_categories": ["サブカテゴリ1", "サブカテゴリ2"],
    "reasoning": "判定理由の詳細説明",
    "collaboration_score": 4,
    "target_audience": "ターゲット層の説明",
    "content_style": "コンテンツスタイルの特徴",
    "brand_collaboration_potential": "ブランドコラボの可能性"
}}
"""
    
    def _parse_category_result(self, result: str) -> Dict[str, Any]:
        """AI分析結果のパース"""
        try:
            # JSON部分を抽出
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        
        # JSONパースに失敗した場合、テキストから情報抽出
        return self._extract_from_text(result)
    
    def _extract_from_text(self, text: str) -> Dict[str, Any]:
        """テキストから情報抽出（フォールバック）"""
        # 基本的なテキスト解析
        main_category = 'lifestyle'  # デフォルト
        
        # キーワードベースの簡易判定
        for category, info in self.main_categories.items():
            for subcategory in info['subcategories']:
                if subcategory.lower() in text.lower():
                    main_category = category
                    break
        
        return {
            'main_category': main_category,
            'main_category_name': self.main_categories[main_category]['name'],
            'sub_categories': ['一般'],
            'reasoning': 'テキスト解析による推定',
            'collaboration_score': 3,
            'target_audience': '不明',
            'content_style': '不明',
            'brand_collaboration_potential': '要詳細分析'
        }
    
    def _calculate_confidence(
        self,
        analysis: Dict[str, Any],
        channel_data: Dict[str, Any]
    ) -> float:
        """分析結果の信頼度計算"""
        confidence = 0.0
        
        # 説明文の長さ
        desc_length = len(channel_data.get('description', ''))
        if desc_length > 100:
            confidence += 0.3
        elif desc_length > 50:
            confidence += 0.2
        
        # 動画数
        video_count = channel_data.get('video_count', 0)
        if video_count > 50:
            confidence += 0.2
        elif video_count > 10:
            confidence += 0.1
        
        # カテゴリ判定の一貫性
        if analysis.get('reasoning') and len(analysis['reasoning']) > 50:
            confidence += 0.3
        
        # サブカテゴリの数
        sub_cats = analysis.get('sub_categories', [])
        if 1 <= len(sub_cats) <= 3:
            confidence += 0.2
        
        return round(min(confidence, 1.0), 2)
    
    def _fallback_category_analysis(self, channel_data: Dict[str, Any]) -> Dict[str, Any]:
        """フォールバック分析"""
        return {
            'main_category': 'lifestyle',
            'main_category_name': 'ライフスタイル',
            'sub_categories': ['一般'],
            'reasoning': '自動分析が利用できないため、デフォルトカテゴリを設定',
            'collaboration_score': 3,
            'target_audience': '詳細分析が必要',
            'content_style': '要手動確認',
            'brand_collaboration_potential': '要詳細分析',
            'confidence': 0.1
        }


class AdvancedEmailExtractor:
    """
    AI強化メール抽出エージェント
    
    Gemini を活用した高精度メールアドレス抽出
    """
    
    def __init__(self):
        """初期化"""
        self.gemini = GeminiClient()
    
    async def extract_business_emails(
        self,
        channel_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        ビジネス用メールアドレスの高精度抽出
        
        Args:
            channel_data: チャンネル情報
            
        Returns:
            List[Dict]: 抽出されたメールアドレス情報
        """
        try:
            # 分析テキスト準備
            text = channel_data.get('description', '')
            if not text:
                return []
            
            # AIプロンプト作成
            prompt = self._create_email_extraction_prompt()
            
            # AI分析実行
            result = await self.gemini.analyze_text(prompt, text)
            
            if not result:
                return []
            
            # 結果パース
            emails = self._parse_email_result(result)
            
            return emails
            
        except Exception as e:
            logger.error(f"❌ Advanced email extraction failed: {e}")
            return []
    
    def _create_email_extraction_prompt(self) -> str:
        """メール抽出用プロンプト"""
        return """
あなたはメールアドレス抽出の専門家です。
以下のYouTubeチャンネル説明文から、ビジネス用のメールアドレスを抽出してください。

抽出条件:
1. ビジネス・コラボレーション用のメールアドレスのみ
2. 個人的なメールは除外
3. 信頼度を1-10で評価
4. 用途を特定（お仕事依頼、コラボ、PR等）

出力形式（JSON配列）:
[
    {
        "email": "メールアドレス",
        "confidence": 8,
        "purpose": "お仕事依頼",
        "context": "周辺テキスト",
        "is_primary": true
    }
]

メールアドレスが見つからない場合は空の配列 [] を返してください。
"""
    
    def _parse_email_result(self, result: str) -> List[Dict[str, Any]]:
        """AI分析結果のパース"""
        try:
            # JSON部分を抽出
            json_match = re.search(r'\[.*\]', result, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                emails = json.loads(json_str)
                
                # 結果の検証
                validated_emails = []
                for email_info in emails:
                    if self._validate_email_info(email_info):
                        validated_emails.append(email_info)
                
                return validated_emails
        except json.JSONDecodeError:
            pass
        
        return []
    
    def _validate_email_info(self, email_info: Dict[str, Any]) -> bool:
        """メール情報の検証"""
        # 必須フィールドの確認
        if not all(key in email_info for key in ['email', 'confidence']):
            return False
        
        # メールアドレス形式の確認
        email = email_info['email']
        email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        if not email_pattern.match(email):
            return False
        
        # 信頼度の確認
        confidence = email_info['confidence']
        if not isinstance(confidence, (int, float)) or not (1 <= confidence <= 10):
            return False
        
        return True


class TrendAnalyzer:
    """
    トレンド分析エージェント
    
    YouTubeチャンネルのトレンド分析と将来性予測
    """
    
    def __init__(self):
        """初期化"""
        self.gemini = GeminiClient()
    
    async def analyze_growth_trend(
        self,
        channel_data: Dict[str, Any],
        historical_data: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        成長トレンド分析
        
        Args:
            channel_data: 現在のチャンネル情報
            historical_data: 過去のデータ（オプション）
            
        Returns:
            Dict: トレンド分析結果
        """
        try:
            # 分析データ準備
            analysis_data = self._prepare_trend_data(channel_data, historical_data)
            
            # プロンプト作成
            prompt = self._create_trend_prompt()
            
            # AI分析実行
            result = await self.gemini.analyze_text(prompt, analysis_data)
            
            if not result:
                return self._fallback_trend_analysis()
            
            # 結果パース
            trend_analysis = self._parse_trend_result(result)
            
            return trend_analysis
            
        except Exception as e:
            logger.error(f"❌ Trend analysis failed: {e}")
            return self._fallback_trend_analysis()
    
    def _prepare_trend_data(
        self,
        channel_data: Dict[str, Any],
        historical_data: List[Dict[str, Any]] = None
    ) -> str:
        """トレンド分析用データ準備"""
        data_points = []
        
        # 現在の統計
        data_points.append(f"登録者数: {channel_data.get('subscriber_count', 0):,}")
        data_points.append(f"動画数: {channel_data.get('video_count', 0):,}")
        data_points.append(f"総再生回数: {channel_data.get('view_count', 0):,}")
        data_points.append(f"エンゲージメント率: {channel_data.get('engagement_rate', 0)}%")
        
        # チャンネル開設日
        if channel_data.get('published_at'):
            data_points.append(f"開設日: {channel_data['published_at']}")
        
        # 最新動画情報
        if channel_data.get('recent_videos'):
            video_info = []
            for video in channel_data['recent_videos'][:3]:
                video_info.append(f"「{video.get('title', '')}」({video.get('published_at', '')})")
            data_points.append(f"最新動画: {', '.join(video_info)}")
        
        return '\n'.join(data_points)
    
    def _create_trend_prompt(self) -> str:
        """トレンド分析用プロンプト"""
        return """
あなたはYouTubeチャンネルの成長トレンド分析の専門家です。
以下のチャンネルデータから、成長性と将来性を分析してください。

分析項目:
1. 成長段階の判定（導入期/成長期/成熟期/衰退期）
2. 成長率の推定
3. コンテンツトレンドへの適応度
4. ブランドコラボレーションの最適タイミング
5. 今後6ヶ月の成長予測

出力形式（JSON）:
{
    "growth_stage": "成長期",
    "growth_rate": "高成長",
    "trend_adaptation": 8,
    "collaboration_timing": "最適",
    "future_prediction": {
        "6_months": {
            "subscriber_growth": "+25%",
            "engagement_trend": "上昇",
            "risk_factors": ["リスク要因"]
        }
    },
    "recommendations": ["推奨事項1", "推奨事項2"]
}
"""
    
    def _parse_trend_result(self, result: str) -> Dict[str, Any]:
        """トレンド分析結果のパース"""
        try:
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        
        return self._fallback_trend_analysis()
    
    def _fallback_trend_analysis(self) -> Dict[str, Any]:
        """フォールバックトレンド分析"""
        return {
            'growth_stage': '不明',
            'growth_rate': '要分析',
            'trend_adaptation': 5,
            'collaboration_timing': '要検討',
            'future_prediction': {
                '6_months': {
                    'subscriber_growth': '不明',
                    'engagement_trend': '要観察',
                    'risk_factors': ['データ不足']
                }
            },
            'recommendations': ['詳細分析が必要']
        }


# 統合AI分析サービス
class IntegratedAIAnalyzer:
    """
    統合AI分析サービス
    
    すべてのAI分析機能を統合して実行
    """
    
    def __init__(self):
        """初期化"""
        self.category_analyzer = CategoryAnalyzer()
        self.email_extractor = AdvancedEmailExtractor()
        self.trend_analyzer = TrendAnalyzer()
    
    async def comprehensive_analysis(
        self,
        channel_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        チャンネルの包括的AI分析
        
        Args:
            channel_data: チャンネル情報
            
        Returns:
            Dict: 包括的分析結果
        """
        logger.info(f"🤖 Starting comprehensive AI analysis for {channel_data.get('channel_name', 'Unknown')}")
        
        try:
            # 並行して各種分析を実行
            tasks = [
                self.category_analyzer.analyze_channel_category(channel_data),
                self.email_extractor.extract_business_emails(channel_data),
                self.trend_analyzer.analyze_growth_trend(channel_data)
            ]
            
            category_result, email_result, trend_result = await asyncio.gather(*tasks)
            
            # 総合スコア計算
            overall_score = self._calculate_overall_score(
                category_result,
                email_result,
                trend_result,
                channel_data
            )
            
            return {
                'channel_id': channel_data.get('channel_id'),
                'analysis_timestamp': datetime.utcnow().isoformat(),
                'category_analysis': category_result,
                'email_analysis': email_result,
                'trend_analysis': trend_result,
                'overall_score': overall_score,
                'recommendation': self._generate_recommendation(
                    category_result, email_result, trend_result, overall_score
                )
            }
            
        except Exception as e:
            logger.error(f"❌ Comprehensive analysis failed: {e}")
            return {
                'error': str(e),
                'analysis_timestamp': datetime.utcnow().isoformat()
            }
    
    def _calculate_overall_score(
        self,
        category_result: Dict[str, Any],
        email_result: List[Dict[str, Any]],
        trend_result: Dict[str, Any],
        channel_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """総合スコア計算"""
        scores = {}
        
        # カテゴリスコア
        collaboration_score = category_result.get('collaboration_score', 3)
        confidence = category_result.get('confidence', 0.5)
        scores['category_score'] = collaboration_score * confidence
        
        # メールスコア
        if email_result:
            avg_confidence = sum(e.get('confidence', 5) for e in email_result) / len(email_result)
            scores['contactability_score'] = min(avg_confidence, 10)
        else:
            scores['contactability_score'] = 0
        
        # トレンドスコア
        trend_adaptation = trend_result.get('trend_adaptation', 5)
        scores['trend_score'] = trend_adaptation
        
        # チャンネル規模スコア
        subscriber_count = channel_data.get('subscriber_count', 0)
        if subscriber_count >= 100000:
            scores['scale_score'] = 10
        elif subscriber_count >= 10000:
            scores['scale_score'] = 8
        elif subscriber_count >= 1000:
            scores['scale_score'] = 6
        else:
            scores['scale_score'] = 3
        
        # 総合スコア
        overall = (
            scores['category_score'] * 0.3 +
            scores['contactability_score'] * 0.3 +
            scores['trend_score'] * 0.2 +
            scores['scale_score'] * 0.2
        )
        
        scores['overall'] = round(overall, 2)
        scores['grade'] = self._score_to_grade(overall)
        
        return scores
    
    def _score_to_grade(self, score: float) -> str:
        """スコアをグレードに変換"""
        if score >= 8.5:
            return 'S'
        elif score >= 7.5:
            return 'A'
        elif score >= 6.5:
            return 'B'
        elif score >= 5.5:
            return 'C'
        else:
            return 'D'
    
    def _generate_recommendation(
        self,
        category_result: Dict[str, Any],
        email_result: List[Dict[str, Any]],
        trend_result: Dict[str, Any],
        overall_score: Dict[str, Any]
    ) -> str:
        """推奨事項生成"""
        recommendations = []
        
        grade = overall_score.get('grade', 'D')
        
        if grade in ['S', 'A']:
            recommendations.append("高い協業価値を持つ優良チャンネルです")
        elif grade == 'B':
            recommendations.append("協業価値があるチャンネルです")
        else:
            recommendations.append("慎重な検討が必要なチャンネルです")
        
        # メール連絡可能性
        if email_result:
            recommendations.append("ビジネスメールでの連絡が可能です")
        else:
            recommendations.append("直接連絡手段の確認が必要です")
        
        # トレンド状況
        growth_stage = trend_result.get('growth_stage', '')
        if growth_stage == '成長期':
            recommendations.append("成長期にあり、協業に最適なタイミングです")
        
        return ' / '.join(recommendations)


if __name__ == "__main__":
    # テスト実行
    async def test_analysis():
        analyzer = IntegratedAIAnalyzer()
        
        test_channel = {
            'channel_id': 'test123',
            'channel_name': 'テストチャンネル',
            'description': 'メイクアップチュートリアルを投稿しています。お仕事のご依頼は business@example.com まで。',
            'subscriber_count': 50000,
            'video_count': 100,
            'view_count': 5000000,
            'engagement_rate': 3.5
        }
        
        result = await analyzer.comprehensive_analysis(test_channel)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    asyncio.run(test_analysis())