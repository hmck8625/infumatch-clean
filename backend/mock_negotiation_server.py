#!/usr/bin/env python3
"""
交渉エージェントAPIのモックサーバー
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.parse
import time

class MockNegotiationHandler(BaseHTTPRequestHandler):
    
    def do_OPTIONS(self):
        """CORS preflight request"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_POST(self):
        """POST request handler"""
        if self.path == '/api/v1/negotiation/reply-patterns':
            self.handle_reply_patterns()
        else:
            self.send_error(404, "Endpoint not found")
    
    def do_GET(self):
        """GET request handler"""
        if self.path == '/api/v1/negotiation/status':
            self.handle_status()
        elif self.path == '/health':
            self.handle_health()
        else:
            self.send_error(404, "Endpoint not found")
    
    def handle_reply_patterns(self):
        """返信パターン生成のモック"""
        try:
            # リクエストボディを読み取り
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))
            
            # 設定データを取得（モック）
            settings = self.get_mock_settings()
            
            # 設定に基づいて返信パターンをカスタマイズ
            company_name = settings.get('companyName', 'InfuMatch株式会社')
            contact_person = settings.get('contactPerson', '田中美咲')
            negotiation_tone = settings.get('negotiationSettings', {}).get('negotiationTone', 'friendly')
            budget_range = settings.get('negotiationSettings', {}).get('defaultBudgetRange', {})
            
            # モック応答データ
            mock_response = {
                "success": True,
                "content": None,
                "metadata": {
                    "reply_patterns": [
                        {
                            "pattern_type": "friendly_enthusiastic",
                            "pattern_name": "友好的・積極的",
                            "content": f"お疲れ様です！{company_name}の{contact_person}です。ご提案の件、とても魅力的ですね😊 健康志向の調味料PRということで、ぜひ詳細をお聞かせください。予算は{budget_range.get('min', 20000):,}円〜{budget_range.get('max', 100000):,}円の範囲で検討しております。よろしくお願いします！",
                            "reasoning": "設定された親しみやすいトーンで、予算範囲も含めた具体的な提案",
                            "tone": "明るい・エネルギッシュ",
                            "recommendation_score": 0.85
                        },
                        {
                            "pattern_type": "cautious_professional",
                            "pattern_name": "控えめ・慎重",
                            "content": f"お世話になっております。{company_name}の{contact_person}と申します。この度はご提案いただき、ありがとうございます。健康志向の商材ということで興味深い内容ですが、エンゲージメント率やターゲット適合性について詳しく確認させていただきたく思います。",
                            "reasoning": "設定された重視ポイント（エンゲージメント率、ターゲット適合性）を含む慎重なアプローチ",
                            "tone": "丁寧・慎重",
                            "recommendation_score": 0.92
                        },
                        {
                            "pattern_type": "business_focused",
                            "pattern_name": "ビジネス重視",
                            "content": f"ご提案ありがとうございます。{company_name}として、具体的な条件について確認させてください。予算範囲は{budget_range.get('min', 20000):,}円〜{budget_range.get('max', 100000):,}円で検討しており、エンゲージメント率と商品の適合性を重視しております。詳細な企画案をお聞かせください。",
                            "reasoning": "予算範囲と重視ポイントを明確にしたビジネス重視の返信",
                            "tone": "効率的・論理的",
                            "recommendation_score": 0.78
                        }
                    ],
                    "thread_analysis": {
                        "relationship_stage": "initial_contact",
                        "emotional_tone": "positive",
                        "main_topics": ["価格交渉", "条件確認"],
                        "urgency_level": "normal",
                        "message_count": len(request_data.get("thread_messages", []))
                    },
                    "pattern_count": 3,
                    "agent": "NegotiationAgent",
                    "action": "generate_reply_patterns"
                },
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())
            }
            
            # レスポンス送信
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response_json = json.dumps(mock_response, ensure_ascii=False, indent=2)
            self.wfile.write(response_json.encode('utf-8'))
            
            print(f"✅ 返信パターン生成リクエストを処理しました")
            
        except Exception as e:
            print(f"❌ エラー: {e}")
            self.send_error(500, f"Internal server error: {str(e)}")
    
    def handle_status(self):
        """ステータス確認のモック"""
        response = {
            "success": True,
            "status": {
                "agent_initialized": True,
                "agent_ready": True,
                "system_time": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()),
                "features": [
                    "initial_contact_generation",
                    "conversation_continuation",
                    "price_negotiation",
                    "human_like_communication",
                    "reply_patterns_generation"
                ]
            }
        }
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response_json = json.dumps(response, ensure_ascii=False, indent=2)
        self.wfile.write(response_json.encode('utf-8'))
        print("✅ ステータス確認リクエストを処理しました")
    
    def handle_health(self):
        """ヘルスチェックのモック"""
        response = {"status": "healthy", "service": "mock-negotiation-api"}
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response_json = json.dumps(response)
        self.wfile.write(response_json.encode('utf-8'))
        print("✅ ヘルスチェックリクエストを処理しました")
    
    def get_mock_settings(self):
        """設定データのモックを取得"""
        return {
            "companyName": "InfuMatch株式会社",
            "contactPerson": "田中美咲",
            "negotiationSettings": {
                "negotiationTone": "friendly",
                "specialInstructions": "親しみやすく、相手の立場を理解した交渉を心がけてください。",
                "keyPriorities": ["エンゲージメント率", "ターゲット適合性"],
                "avoidTopics": ["政治的内容", "競合他社言及"],
                "defaultBudgetRange": {"min": 20000, "max": 100000}
            },
            "products": [
                {
                    "name": "プレミアム調味料セット",
                    "category": "食品・調味料",
                    "description": "健康志向の方向けの無添加調味料"
                }
            ]
        }
    
    def log_message(self, format, *args):
        """ログメッセージをカスタマイズ"""
        print(f"🌐 {self.address_string()} - {format % args}")

def run_mock_server(port=8001):
    """モックサーバーを起動"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, MockNegotiationHandler)
    
    print(f"🚀 交渉エージェント モックサーバーを起動しました")
    print(f"📍 URL: http://localhost:{port}")
    print(f"📋 利用可能なエンドポイント:")
    print(f"   - GET  /health")
    print(f"   - GET  /api/v1/negotiation/status")
    print(f"   - POST /api/v1/negotiation/reply-patterns")
    print(f"🔄 サーバーを停止するには Ctrl+C を押してください")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print(f"\n🛑 サーバーを停止しています...")
        httpd.shutdown()
        print(f"✅ サーバーが停止されました")

if __name__ == "__main__":
    run_mock_server()