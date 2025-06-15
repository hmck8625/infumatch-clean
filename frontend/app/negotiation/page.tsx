'use client';

import { useState, useEffect } from 'react';
import { useSession } from 'next-auth/react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  MessageSquare, 
  Send, 
  Bot, 
  Mail, 
  DollarSign, 
  User, 
  Calendar,
  CheckCircle,
  AlertCircle,
  Loader2
} from 'lucide-react';
import { GmailService, EmailThread } from '@/lib/gmail';

interface NegotiationAgent {
  name: string;
  status: 'ready' | 'processing' | 'waiting';
  lastAction?: string;
  personality: {
    name: string;
    role: string;
    company: string;
  };
}

interface NegotiationSession {
  id: string;
  influencerName: string;
  influencerEmail: string;
  campaignName: string;
  status: 'active' | 'paused' | 'completed';
  stage: 'initial_contact' | 'warming_up' | 'price_negotiation' | 'finalizing';
  lastUpdate: string;
  proposedPrice?: number;
  agreedPrice?: number;
}

export default function NegotiationPage() {
  const { data: session } = useSession();
  const [agent, setAgent] = useState<NegotiationAgent>({
    name: 'NegotiationAgent',
    status: 'ready',
    personality: {
      name: '田中美咲',
      role: 'インフルエンサーマーケティング担当',
      company: '株式会社InfuMatch'
    }
  });

  const [sessions, setSessions] = useState<NegotiationSession[]>([]);
  const [emailThreads, setEmailThreads] = useState<EmailThread[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedSession, setSelectedSession] = useState<string | null>(null);
  const [newContactForm, setNewContactForm] = useState({
    influencerName: '',
    influencerEmail: '',
    campaignName: '',
    productName: '',
    budgetMin: '',
    budgetMax: ''
  });

  // Gmail統合の状態
  const [gmailConnected, setGmailConnected] = useState(false);
  const [lastEmailCheck, setLastEmailCheck] = useState<Date | null>(null);

  useEffect(() => {
    if (session?.accessToken) {
      setGmailConnected(true);
      loadEmailThreads();
    }
  }, [session]);

  const loadEmailThreads = async () => {
    if (!session?.accessToken) return;

    try {
      setIsLoading(true);
      const gmailService = new GmailService(session.accessToken);
      const threads = await gmailService.getInfluencerThreads();
      setEmailThreads(threads);
      setLastEmailCheck(new Date());
    } catch (error) {
      console.error('メール取得エラー:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const generateInitialContact = async () => {
    if (!newContactForm.influencerName || !newContactForm.influencerEmail) {
      alert('インフルエンサー名とメールアドレスを入力してください');
      return;
    }

    try {
      setIsLoading(true);
      setAgent(prev => ({ ...prev, status: 'processing', lastAction: '初回コンタクト生成中...' }));

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/negotiation/initial-contact`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          influencer: {
            channel_name: newContactForm.influencerName,
            email: newContactForm.influencerEmail,
            subscriber_count: 50000, // 仮の数値
            categories: ['一般']
          },
          campaign: {
            product_name: newContactForm.productName,
            budget_min: parseInt(newContactForm.budgetMin) || 0,
            budget_max: parseInt(newContactForm.budgetMax) || 0,
            campaign_type: '商品紹介'
          }
        })
      });

      const result = await response.json();
      
      if (result.success) {
        // Gmail経由でメール送信
        await sendEmailViaGmail(
          newContactForm.influencerEmail,
          '【InfuMatch】コラボレーションのご提案',
          result.content
        );

        // セッション作成
        const newSession: NegotiationSession = {
          id: Date.now().toString(),
          influencerName: newContactForm.influencerName,
          influencerEmail: newContactForm.influencerEmail,
          campaignName: newContactForm.campaignName,
          status: 'active',
          stage: 'initial_contact',
          lastUpdate: new Date().toISOString()
        };
        setSessions(prev => [...prev, newSession]);

        // フォームリセット
        setNewContactForm({
          influencerName: '',
          influencerEmail: '',
          campaignName: '',
          productName: '',
          budgetMin: '',
          budgetMax: ''
        });

        setAgent(prev => ({ ...prev, status: 'ready', lastAction: '初回コンタクト送信完了' }));
      } else {
        throw new Error(result.error || 'メール生成に失敗しました');
      }
    } catch (error) {
      console.error('初回コンタクト生成エラー:', error);
      alert('初回コンタクトの生成に失敗しました');
      setAgent(prev => ({ ...prev, status: 'ready', lastAction: 'エラーが発生しました' }));
    } finally {
      setIsLoading(false);
    }
  };

  const sendEmailViaGmail = async (to: string, subject: string, body: string, threadId?: string) => {
    if (!session?.accessToken) return;

    try {
      const response = await fetch('/api/gmail/send', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          to,
          subject,
          message: body,
          threadId
        })
      });

      if (!response.ok) {
        throw new Error('メール送信に失敗しました');
      }
    } catch (error) {
      console.error('Gmail送信エラー:', error);
      throw error;
    }
  };

  const handleNegotiationContinue = async (sessionId: string, newMessage: string) => {
    const session = sessions.find(s => s.id === sessionId);
    if (!session) return;

    try {
      setIsLoading(true);
      setAgent(prev => ({ ...prev, status: 'processing', lastAction: '返信生成中...' }));

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/negotiation/continue`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          conversation_history: [], // 実際の会話履歴を渡す
          new_message: newMessage,
          context: {
            session_id: sessionId,
            influencer_email: session.influencerEmail
          }
        })
      });

      const result = await response.json();
      
      if (result.success) {
        // Gmail経由で返信送信
        await sendEmailViaGmail(
          session.influencerEmail,
          `Re: ${session.campaignName}について`,
          result.content
        );

        // セッション更新
        setSessions(prev => prev.map(s => 
          s.id === sessionId 
            ? { ...s, lastUpdate: new Date().toISOString(), stage: result.metadata?.relationship_stage || s.stage }
            : s
        ));

        setAgent(prev => ({ ...prev, status: 'ready', lastAction: '返信送信完了' }));
      }
    } catch (error) {
      console.error('交渉継続エラー:', error);
      setAgent(prev => ({ ...prev, status: 'ready', lastAction: 'エラーが発生しました' }));
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'paused': return 'bg-yellow-100 text-yellow-800';
      case 'completed': return 'bg-blue-100 text-blue-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStageLabel = (stage: string) => {
    switch (stage) {
      case 'initial_contact': return '初回コンタクト';
      case 'warming_up': return '関係構築';
      case 'price_negotiation': return '価格交渉';
      case 'finalizing': return '最終調整';
      default: return stage;
    }
  };

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          AI交渉エージェント
        </h1>
        <p className="text-gray-600">
          AIが人間らしい自然な交渉を代行し、インフルエンサーとの関係構築をサポートします
        </p>
      </div>

      {/* エージェント状態表示 */}
      <Card className="mb-6">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="flex items-center justify-center w-12 h-12 bg-blue-100 rounded-full">
                <Bot className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <CardTitle className="text-lg">{agent.personality.name}</CardTitle>
                <CardDescription>{agent.personality.role} at {agent.personality.company}</CardDescription>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <Badge 
                variant={agent.status === 'ready' ? 'default' : agent.status === 'processing' ? 'secondary' : 'outline'}
                className="capitalize"
              >
                {agent.status === 'ready' && <CheckCircle className="w-3 h-3 mr-1" />}
                {agent.status === 'processing' && <Loader2 className="w-3 h-3 mr-1 animate-spin" />}
                {agent.status === 'waiting' && <AlertCircle className="w-3 h-3 mr-1" />}
                {agent.status === 'ready' ? '待機中' : agent.status === 'processing' ? '処理中' : '応答待ち'}
              </Badge>
              {gmailConnected && (
                <Badge variant="outline" className="text-green-600">
                  <Mail className="w-3 h-3 mr-1" />
                  Gmail連携済み
                </Badge>
              )}
            </div>
          </div>
          {agent.lastAction && (
            <p className="text-sm text-gray-500 mt-2">{agent.lastAction}</p>
          )}
        </CardHeader>
      </Card>

      <Tabs defaultValue="new-contact" className="space-y-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="new-contact">新規コンタクト</TabsTrigger>
          <TabsTrigger value="sessions">進行中の交渉</TabsTrigger>
          <TabsTrigger value="emails">メール履歴</TabsTrigger>
        </TabsList>

        {/* 新規コンタクト */}
        <TabsContent value="new-contact">
          <Card>
            <CardHeader>
              <CardTitle>初回コンタクト生成</CardTitle>
              <CardDescription>
                AIが自然で人間らしい初回コンタクトメールを生成します
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="influencer-name">インフルエンサー名</Label>
                  <Input
                    id="influencer-name"
                    value={newContactForm.influencerName}
                    onChange={(e) => setNewContactForm(prev => ({ ...prev, influencerName: e.target.value }))}
                    placeholder="チャンネル名や本名"
                  />
                </div>
                <div>
                  <Label htmlFor="influencer-email">メールアドレス</Label>
                  <Input
                    id="influencer-email"
                    type="email"
                    value={newContactForm.influencerEmail}
                    onChange={(e) => setNewContactForm(prev => ({ ...prev, influencerEmail: e.target.value }))}
                    placeholder="contact@example.com"
                  />
                </div>
              </div>

              <div>
                <Label htmlFor="campaign-name">キャンペーン名</Label>
                <Input
                  id="campaign-name"
                  value={newContactForm.campaignName}
                  onChange={(e) => setNewContactForm(prev => ({ ...prev, campaignName: e.target.value }))}
                  placeholder="春の新商品PRキャンペーン"
                />
              </div>

              <div>
                <Label htmlFor="product-name">商品・サービス名</Label>
                <Input
                  id="product-name"
                  value={newContactForm.productName}
                  onChange={(e) => setNewContactForm(prev => ({ ...prev, productName: e.target.value }))}
                  placeholder="新しい調味料"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="budget-min">最小予算（円）</Label>
                  <Input
                    id="budget-min"
                    type="number"
                    value={newContactForm.budgetMin}
                    onChange={(e) => setNewContactForm(prev => ({ ...prev, budgetMin: e.target.value }))}
                    placeholder="30000"
                  />
                </div>
                <div>
                  <Label htmlFor="budget-max">最大予算（円）</Label>
                  <Input
                    id="budget-max"
                    type="number"
                    value={newContactForm.budgetMax}
                    onChange={(e) => setNewContactForm(prev => ({ ...prev, budgetMax: e.target.value }))}
                    placeholder="50000"
                  />
                </div>
              </div>

              <Button 
                onClick={generateInitialContact} 
                disabled={isLoading || !gmailConnected}
                className="w-full"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    生成中...
                  </>
                ) : (
                  <>
                    <Send className="w-4 h-4 mr-2" />
                    初回コンタクト生成＆送信
                  </>
                )}
              </Button>

              {!gmailConnected && (
                <Alert>
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    メール送信にはGmailアカウントでのログインが必要です
                  </AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* 進行中の交渉 */}
        <TabsContent value="sessions">
          <div className="space-y-4">
            {sessions.length === 0 ? (
              <Card>
                <CardContent className="text-center py-8">
                  <MessageSquare className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-500">進行中の交渉セッションはありません</p>
                </CardContent>
              </Card>
            ) : (
              sessions.map((session) => (
                <Card key={session.id}>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div>
                        <CardTitle className="text-lg">{session.influencerName}</CardTitle>
                        <CardDescription>{session.campaignName}</CardDescription>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Badge className={getStatusColor(session.status)}>
                          {session.status}
                        </Badge>
                        <Badge variant="outline">
                          {getStageLabel(session.stage)}
                        </Badge>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center justify-between text-sm text-gray-500">
                      <span>最終更新: {new Date(session.lastUpdate).toLocaleString('ja-JP')}</span>
                      <div className="flex items-center space-x-4">
                        {session.proposedPrice && (
                          <span className="flex items-center">
                            <DollarSign className="w-3 h-3 mr-1" />
                            提案価格: ¥{session.proposedPrice.toLocaleString()}
                          </span>
                        )}
                        <Button 
                          size="sm" 
                          variant="outline"
                          onClick={() => setSelectedSession(session.id)}
                        >
                          詳細を見る
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        </TabsContent>

        {/* メール履歴 */}
        <TabsContent value="emails">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Gmail連携メール履歴</CardTitle>
                  <CardDescription>
                    インフルエンサーとのメールのやり取りを表示します
                  </CardDescription>
                </div>
                <Button onClick={loadEmailThreads} disabled={isLoading || !gmailConnected}>
                  {isLoading ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <Mail className="w-4 h-4 mr-2" />
                  )}
                  更新
                </Button>
              </div>
              {lastEmailCheck && (
                <p className="text-xs text-gray-400">
                  最終チェック: {lastEmailCheck.toLocaleString('ja-JP')}
                </p>
              )}
            </CardHeader>
            <CardContent>
              {!gmailConnected ? (
                <div className="text-center py-8">
                  <Mail className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-500">Gmailアカウントでログインしてください</p>
                </div>
              ) : emailThreads.length === 0 ? (
                <div className="text-center py-8">
                  <MessageSquare className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-500">メールスレッドがありません</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {emailThreads.map((thread) => (
                    <div key={thread.id} className="border rounded-lg p-3">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-medium truncate">{thread.snippet}</h4>
                        <Badge variant="outline">
                          {thread.messages.length}件
                        </Badge>
                      </div>
                      <p className="text-sm text-gray-600 truncate">{thread.snippet}</p>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}