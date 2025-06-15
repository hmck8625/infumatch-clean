"""
AIエージェント基底クラス

@description 全AIエージェントの共通機能とインターフェース
Vertex AI と Google Agentspace の統合基盤

@author InfuMatch Development Team
@version 1.0.0
"""

import logging
import json
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from dataclasses import dataclass

try:
    import vertexai
    from vertexai.language_models import TextGenerationModel, ChatModel
    from vertexai.generative_models import GenerativeModel
    VERTEX_AVAILABLE = True
except ImportError:
    VERTEX_AVAILABLE = False

import google.generativeai as genai
import google.auth
from google.oauth2 import service_account

from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class AgentConfig:
    """
    エージェント設定
    
    各エージェントの動作パラメータを定義
    """
    
    name: str
    model_name: str = "gemini-1.5-pro"
    temperature: float = 0.7
    max_output_tokens: int = 2048
    top_p: float = 0.9
    top_k: int = 40
    safety_settings: Optional[Dict] = None
    system_instruction: Optional[str] = None
    
    def __post_init__(self):
        """初期化後処理"""
        if self.safety_settings is None:
            # デフォルトの安全設定
            self.safety_settings = {
                "HARM_CATEGORY_HATE_SPEECH": "BLOCK_MEDIUM_AND_ABOVE",
                "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_MEDIUM_AND_ABOVE",
                "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_MEDIUM_AND_ABOVE",
                "HARM_CATEGORY_HARASSMENT": "BLOCK_MEDIUM_AND_ABOVE",
            }


class BaseAgent(ABC):
    """
    AIエージェント基底クラス
    
    全エージェントの共通機能を提供
    - Vertex AI の初期化と管理
    - プロンプト生成とレスポンス処理
    - エラーハンドリング
    - ログ記録
    """
    
    def __init__(self, config: AgentConfig):
        """
        エージェントの初期化
        
        Args:
            config: エージェント設定
        """
        self.config = config
        self.model = None
        self.use_vertex = False
        self._initialize_ai()
        
        logger.info(f"🤖 Initialized agent: {self.config.name}")
    
    def _initialize_ai(self) -> None:
        """AI サービスの初期化（Vertex AI または Gemini API）"""
        try:
            # まずVertex AI を試行
            if VERTEX_AVAILABLE:
                try:
                    self._initialize_vertex_ai()
                    self._initialize_vertex_model()
                    self.use_vertex = True
                    logger.info("✅ Using Vertex AI")
                    return
                except Exception as e:
                    logger.warning(f"⚠️ Vertex AI failed, falling back to Gemini API: {e}")
            
            # Gemini API を使用
            self._initialize_gemini_api()
            logger.info("✅ Using Gemini API")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize AI services: {e}")
            raise
    
    def _initialize_vertex_ai(self) -> None:
        """Vertex AI の初期化"""
        # 認証設定
        if settings.GOOGLE_APPLICATION_CREDENTIALS and settings.is_development:
            credentials = service_account.Credentials.from_service_account_file(
                settings.GOOGLE_APPLICATION_CREDENTIALS
            )
            vertexai.init(
                project=settings.GOOGLE_CLOUD_PROJECT_ID,
                location=settings.GOOGLE_CLOUD_REGION,
                credentials=credentials
            )
        else:
            vertexai.init(
                project=settings.GOOGLE_CLOUD_PROJECT_ID,
                location=settings.GOOGLE_CLOUD_REGION
            )
    
    def _initialize_vertex_model(self) -> None:
        """Vertex AI モデルの初期化"""
        self.model = GenerativeModel(
            model_name=self.config.model_name,
            system_instruction=self.config.system_instruction,
        )
        logger.info(f"✅ Vertex AI Model {self.config.model_name} initialized")
    
    def _initialize_gemini_api(self) -> None:
        """Gemini API の初期化"""
        # API キー設定
        api_key = getattr(settings, 'GEMINI_API_KEY', None)
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in settings")
        
        genai.configure(api_key=api_key)
        
        # モデル名をGemini API用に変換
        model_name = self.config.model_name
        if model_name.startswith('gemini-1.5-pro'):
            model_name = 'gemini-1.5-pro'
        elif model_name.startswith('gemini-1.5-flash'):
            model_name = 'gemini-1.5-flash'
        
        generation_config = {
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
            "top_k": self.config.top_k,
            "max_output_tokens": self.config.max_output_tokens,
        }
        
        self.model = genai.GenerativeModel(
            model_name=model_name,
            generation_config=generation_config,
            system_instruction=self.config.system_instruction
        )
        logger.info(f"✅ Gemini API Model {model_name} initialized")
    
    async def generate_response(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        AIレスポンスを生成
        
        Args:
            prompt: 入力プロンプト
            context: 追加コンテキスト
            **kwargs: 追加パラメータ
            
        Returns:
            Dict: 生成結果
        """
        try:
            # プロンプトの前処理
            formatted_prompt = await self._format_prompt(prompt, context)
            
            # 生成設定
            generation_config = {
                "temperature": kwargs.get("temperature", self.config.temperature),
                "max_output_tokens": kwargs.get("max_output_tokens", self.config.max_output_tokens),
                "top_p": kwargs.get("top_p", self.config.top_p),
                "top_k": kwargs.get("top_k", self.config.top_k),
            }
            
            # AI生成実行
            logger.info(f"🤖 Generating response with {self.config.name}")
            
            if self.use_vertex:
                # Vertex AI使用
                response = await asyncio.get_event_loop().run_in_executor(
                    None, 
                    lambda: self.model.generate_content(
                        formatted_prompt,
                        generation_config=generation_config,
                        safety_settings=self.config.safety_settings
                    )
                )
            else:
                # Gemini API使用
                response = await asyncio.get_event_loop().run_in_executor(
                    None, 
                    lambda: self.model.generate_content(formatted_prompt)
                )
            
            # レスポンス処理
            result = await self._process_response(response, context)
            
            logger.info(f"✅ Response generated successfully by {self.config.name}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to generate response: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent": self.config.name,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _format_prompt(
        self, 
        prompt: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        プロンプトのフォーマット
        
        Args:
            prompt: 基本プロンプト
            context: コンテキスト情報
            
        Returns:
            str: フォーマット済みプロンプト
        """
        # 基本的な前処理（サブクラスでオーバーライド可能）
        formatted = prompt
        
        if context:
            # コンテキスト情報を追加
            context_str = self._context_to_string(context)
            formatted = f"{context_str}\n\n{prompt}"
        
        return formatted
    
    async def _process_response(
        self, 
        response: Any, 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        AIレスポンスの後処理
        
        Args:
            response: AI生成レスポンス
            context: コンテキスト情報
            
        Returns:
            Dict: 処理済み結果
        """
        try:
            # レスポンステキストを取得
            response_text = response.text if hasattr(response, 'text') else str(response)
            
            # 基本的な結果構造
            result = {
                "success": True,
                "content": response_text,
                "agent": self.config.name,
                "model": self.config.model_name,
                "timestamp": datetime.utcnow().isoformat(),
                "tokens_used": self._estimate_tokens(response_text),
            }
            
            # 安全性フィルター情報
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'safety_ratings'):
                    result["safety_ratings"] = candidate.safety_ratings
            
            # JSONパースを試行（構造化出力の場合）
            try:
                parsed_content = json.loads(response_text)
                result["parsed_content"] = parsed_content
                result["content_type"] = "json"
            except (json.JSONDecodeError, ValueError):
                result["content_type"] = "text"
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to process response: {e}")
            return {
                "success": False,
                "error": f"Response processing failed: {str(e)}",
                "agent": self.config.name,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _context_to_string(self, context: Dict[str, Any]) -> str:
        """
        コンテキスト辞書を文字列に変換
        
        Args:
            context: コンテキスト辞書
            
        Returns:
            str: 文字列化されたコンテキスト
        """
        context_lines = []
        
        for key, value in context.items():
            if isinstance(value, (dict, list)):
                value_str = json.dumps(value, ensure_ascii=False, indent=2)
            else:
                value_str = str(value)
            
            context_lines.append(f"## {key}:\n{value_str}")
        
        return "\n\n".join(context_lines)
    
    def _estimate_tokens(self, text: str) -> int:
        """
        トークン数の概算
        
        Args:
            text: 対象テキスト
            
        Returns:
            int: 推定トークン数
        """
        # 簡易的な推定（日本語は文字数の約1.5倍）
        char_count = len(text)
        estimated_tokens = int(char_count * 1.5) if any('\u3040' <= c <= '\u309F' or '\u30A0' <= c <= '\u30FF' for c in text) else char_count // 4
        return max(estimated_tokens, 1)
    
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        エージェント固有の処理を実行
        
        Args:
            input_data: 入力データ
            
        Returns:
            Dict: 処理結果
        """
        pass
    
    def get_agent_info(self) -> Dict[str, Any]:
        """
        エージェント情報を取得
        
        Returns:
            Dict: エージェント情報
        """
        return {
            "name": self.config.name,
            "model": self.config.model_name,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_output_tokens,
            "capabilities": self.get_capabilities(),
            "status": "ready" if self.model else "not_initialized"
        }
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """
        エージェントの機能一覧を取得
        
        Returns:
            List[str]: 機能リスト
        """
        pass


class AgentManager:
    """
    エージェント管理クラス
    
    複数のエージェントの生成・管理・協調処理
    """
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self._initialized = False
    
    async def initialize_agents(self) -> None:
        """全エージェントの初期化"""
        if self._initialized:
            return
        
        try:
            logger.info("🚀 Initializing AI agents...")
            
            # 各エージェントを初期化（後で実装）
            # self.agents["preprocessor"] = DataPreprocessorAgent(...)
            # self.agents["recommendation"] = RecommendationAgent(...)
            # self.agents["negotiation"] = NegotiationAgent(...)
            
            self._initialized = True
            logger.info("✅ All agents initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize agents: {e}")
            raise
    
    def get_agent(self, agent_name: str) -> Optional[BaseAgent]:
        """
        指定されたエージェントを取得
        
        Args:
            agent_name: エージェント名
            
        Returns:
            Optional[BaseAgent]: エージェントインスタンス
        """
        return self.agents.get(agent_name)
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """
        登録済みエージェントの一覧を取得
        
        Returns:
            List[Dict]: エージェント情報のリスト
        """
        return [agent.get_agent_info() for agent in self.agents.values()]
    
    async def process_with_agent(
        self, 
        agent_name: str, 
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        指定エージェントで処理を実行
        
        Args:
            agent_name: エージェント名
            input_data: 入力データ
            
        Returns:
            Dict: 処理結果
        """
        agent = self.get_agent(agent_name)
        
        if not agent:
            return {
                "success": False,
                "error": f"Agent '{agent_name}' not found",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        return await agent.process(input_data)


# グローバルエージェントマネージャー
agent_manager = AgentManager()