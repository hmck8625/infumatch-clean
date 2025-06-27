"""
Gmail自動監視システム
新着メールを検出して自動交渉を開始
"""
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
import logging
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import time

class GmailAutoMonitor:
    """Gmail自動監視モジュール"""
    
    def __init__(self, credentials_manager, auto_negotiation_manager):
        self.credentials_manager = credentials_manager
        self.auto_negotiation_manager = auto_negotiation_manager
        self.is_monitoring = False
        self.monitored_threads: Set[str] = set()
        self.last_check_time = None
        
        # 監視設定
        self.monitor_config = {
            "check_interval_seconds": 60,  # 1分ごとにチェック
            "max_threads_per_check": 10,   # 1回のチェックで処理する最大スレッド数
            "label_filter": "INBOX",        # 監視対象ラベル
            "exclude_labels": ["SPAM", "TRASH"],  # 除外ラベル
        }
        
        # 統計情報
        self.stats = {
            "total_checks": 0,
            "new_threads_found": 0,
            "auto_negotiations_started": 0,
            "errors": 0
        }
    
    async def start_monitoring(self, user_id: str, monitor_config: Optional[Dict] = None):
        """監視を開始"""
        if self.is_monitoring:
            print("⚠️ 既に監視中です")
            return
            
        if monitor_config:
            self.monitor_config.update(monitor_config)
            
        self.is_monitoring = True
        print(f"🔍 Gmail自動監視を開始 - ユーザー: {user_id}")
        
        # 非同期で監視ループを開始
        asyncio.create_task(self._monitoring_loop(user_id))
        
    async def stop_monitoring(self):
        """監視を停止"""
        self.is_monitoring = False
        print("🛑 Gmail自動監視を停止")
        
    async def _monitoring_loop(self, user_id: str):
        """監視メインループ"""
        while self.is_monitoring:
            try:
                await self._check_new_messages(user_id)
                await asyncio.sleep(self.monitor_config["check_interval_seconds"])
            except Exception as e:
                self.stats["errors"] += 1
                logging.error(f"監視エラー: {e}")
                await asyncio.sleep(10)  # エラー時は短い待機
                
    async def _check_new_messages(self, user_id: str):
        """新着メッセージをチェック"""
        self.stats["total_checks"] += 1
        print(f"📥 新着メッセージチェック #{self.stats['total_checks']}")
        
        try:
            # Gmail APIクライアントを作成
            service = await self._get_gmail_service(user_id)
            if not service:
                return
                
            # 新着スレッドを検索
            query = self._build_search_query()
            results = service.users().threads().list(
                userId='me',
                q=query,
                maxResults=self.monitor_config["max_threads_per_check"]
            ).execute()
            
            threads = results.get('threads', [])
            new_threads = []
            
            for thread in threads:
                thread_id = thread['id']
                if thread_id not in self.monitored_threads:
                    new_threads.append(thread_id)
                    self.monitored_threads.add(thread_id)
                    
            if new_threads:
                print(f"✨ {len(new_threads)}件の新着スレッドを検出")
                self.stats["new_threads_found"] += len(new_threads)
                
                # 各スレッドを処理
                for thread_id in new_threads:
                    await self._process_new_thread(service, user_id, thread_id)
            else:
                print("📭 新着メッセージなし")
                
            self.last_check_time = datetime.now()
            
        except Exception as e:
            logging.error(f"新着チェックエラー: {e}")
            
    async def _process_new_thread(self, service, user_id: str, thread_id: str):
        """新着スレッドを処理"""
        try:
            print(f"🔄 スレッド処理開始: {thread_id}")
            
            # スレッドの詳細を取得
            thread = service.users().threads().get(
                userId='me',
                id=thread_id
            ).execute()
            
            messages = thread.get('messages', [])
            if not messages:
                return
                
            # 最新メッセージを取得
            latest_message = messages[-1]
            
            # 自動交渉対象かチェック
            if not self._should_auto_negotiate(latest_message):
                print(f"⏭️ スレッド {thread_id} は自動交渉対象外")
                return
                
            # メッセージ内容を抽出
            message_data = self._extract_message_data(latest_message)
            
            # 会話履歴を構築
            conversation_history = self._build_conversation_history(messages)
            
            # 企業設定を取得（仮実装）
            company_settings = await self._get_company_settings(user_id)
            
            # 自動交渉を開始
            print(f"🤖 自動交渉開始: {thread_id}")
            result = await self.auto_negotiation_manager.process_auto_negotiation_round(
                thread_id=thread_id,
                new_message=message_data['content'],
                conversation_history=conversation_history,
                company_settings=company_settings,
                round_number=len(messages)
            )
            
            if result.get("success"):
                self.stats["auto_negotiations_started"] += 1
                
                # 自動送信が必要な場合
                if result.get("action") == "auto_send":
                    await self._send_auto_reply(
                        service, thread_id, result["selected_pattern"]
                    )
                    
        except Exception as e:
            logging.error(f"スレッド処理エラー {thread_id}: {e}")
            
    async def _get_gmail_service(self, user_id: str):
        """Gmail APIサービスを取得"""
        try:
            # 認証情報を取得
            creds = await self.credentials_manager.get_credentials(user_id)
            if not creds:
                return None
                
            return build('gmail', 'v1', credentials=creds)
        except Exception as e:
            logging.error(f"Gmail service取得エラー: {e}")
            return None
            
    def _build_search_query(self) -> str:
        """検索クエリを構築"""
        query_parts = [f"label:{self.monitor_config['label_filter']}"]
        
        # 除外ラベル
        for label in self.monitor_config.get("exclude_labels", []):
            query_parts.append(f"-label:{label}")
            
        # 最後のチェック以降のメール
        if self.last_check_time:
            # Gmail APIの日付フォーマット
            after_date = self.last_check_time.strftime("%Y/%m/%d")
            query_parts.append(f"after:{after_date}")
        else:
            # 初回は過去24時間
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y/%m/%d")
            query_parts.append(f"after:{yesterday}")
            
        return " ".join(query_parts)
        
    def _should_auto_negotiate(self, message: Dict) -> bool:
        """自動交渉対象かチェック"""
        # 送信者チェック
        headers = message['payload'].get('headers', [])
        from_header = next((h['value'] for h in headers if h['name'] == 'From'), '')
        
        # システムメール除外
        system_domains = ['noreply@', 'no-reply@', 'donotreply@', 'notifications@']
        if any(domain in from_header.lower() for domain in system_domains):
            return False
            
        # ラベルチェック
        label_ids = message.get('labelIds', [])
        if any(label in label_ids for label in ['SPAM', 'TRASH', 'DRAFT']):
            return False
            
        return True
        
    def _extract_message_data(self, message: Dict) -> Dict:
        """メッセージデータを抽出"""
        headers = message['payload'].get('headers', [])
        
        # ヘッダー情報を取得
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
        from_email = next((h['value'] for h in headers if h['name'] == 'From'), '')
        date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
        
        # 本文を取得
        content = self._get_message_body(message['payload'])
        
        return {
            'id': message['id'],
            'subject': subject,
            'from': from_email,
            'date': date,
            'content': content
        }
        
    def _get_message_body(self, payload: Dict) -> str:
        """メッセージ本文を取得"""
        body = ''
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body']['data']
                    body += self._decode_base64(data)
        elif payload['body'].get('data'):
            body = self._decode_base64(payload['body']['data'])
            
        return body
        
    def _decode_base64(self, data: str) -> str:
        """Base64デコード"""
        import base64
        return base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        
    def _build_conversation_history(self, messages: List[Dict]) -> List[Dict]:
        """会話履歴を構築"""
        history = []
        
        for message in messages:
            message_data = self._extract_message_data(message)
            history.append({
                'role': 'user' if self._is_incoming_message(message) else 'assistant',
                'content': message_data['content'],
                'timestamp': message_data['date']
            })
            
        return history
        
    def _is_incoming_message(self, message: Dict) -> bool:
        """受信メッセージかチェック"""
        label_ids = message.get('labelIds', [])
        return 'SENT' not in label_ids
        
    async def _get_company_settings(self, user_id: str) -> Dict:
        """企業設定を取得（仮実装）"""
        # TODO: 実際の設定取得ロジックを実装
        return {
            "companyName": "テスト企業",
            "autoNegotiationSettings": {
                "enabled": True,
                "max_rounds": 3,
                "auto_approval_threshold": 75
            }
        }
        
    async def _send_auto_reply(self, service, thread_id: str, reply_content: Dict):
        """自動返信を送信"""
        try:
            # TODO: 実際の送信ロジックを実装
            print(f"📤 自動返信送信: {thread_id}")
            print(f"   内容: {reply_content.get('content', '')[:100]}...")
        except Exception as e:
            logging.error(f"自動返信エラー: {e}")
            
    def get_monitoring_stats(self) -> Dict:
        """監視統計を取得"""
        return {
            **self.stats,
            "is_monitoring": self.is_monitoring,
            "last_check_time": self.last_check_time.isoformat() if self.last_check_time else None,
            "monitored_threads_count": len(self.monitored_threads)
        }