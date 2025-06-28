'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { 
  Bot, 
  User, 
  AlertCircle,
  Settings,
  Play,
  Pause,
  CheckCircle,
  XCircle
} from 'lucide-react';

type AutomationMode = 'manual' | 'semi_auto';

interface ThreadAutomationProps {
  threadId: string;
  threadSubject?: string;
  onModeChange?: (mode: AutomationMode, enabled: boolean) => void;
}

interface AutomationStatus {
  mode: AutomationMode;
  isActive: boolean;
  roundNumber: number;
  lastAction?: string;
  escalationReason?: string;
}

export default function ThreadAutomationControl({ 
  threadId, 
  threadSubject,
  onModeChange 
}: ThreadAutomationProps) {
  const [mode, setMode] = useState<AutomationMode>('manual');
  const [isActive, setIsActive] = useState(false);
  const [status, setStatus] = useState<AutomationStatus | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [settings, setSettings] = useState<any>(null);

  useEffect(() => {
    // 自動交渉設定を読み込み
    const savedSettings = localStorage.getItem('autoNegotiationSettings');
    if (savedSettings) {
      setSettings(JSON.parse(savedSettings));
    }

    // スレッドの現在の状態を取得
    fetchThreadStatus();
  }, [threadId]);

  const fetchThreadStatus = async () => {
    // TODO: APIから実際のステータスを取得
    setStatus({
      mode: 'manual',
      isActive: false,
      roundNumber: 0
    });
  };

  const toggleAutomation = async () => {
    setIsLoading(true);
    
    try {
      const newIsActive = !isActive;
      
      if (mode === 'semi_auto' && newIsActive) {
        // 半自動モードを開始
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const response = await fetch(`${apiUrl}/api/v1/negotiation/thread/${threadId}/automation`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            mode: 'semi_auto',
            enabled: true,
            settings: settings
          })
        });

        if (response.ok) {
          setIsActive(true);
          onModeChange?.(mode, true);
        }
      } else {
        // 自動化を停止
        setIsActive(false);
        onModeChange?.(mode, false);
      }
    } catch (error) {
      console.error('自動化トグルエラー:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleModeChange = (newMode: AutomationMode) => {
    if (isActive) {
      alert('自動化を停止してからモードを変更してください。');
      return;
    }
    setMode(newMode);
  };

  return (
    <Card className="w-full">
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-lg flex items-center gap-2">
              <Bot className="h-5 w-5" />
              スレッド自動化設定
            </CardTitle>
            {threadSubject && (
              <CardDescription className="mt-1">
                {threadSubject}
              </CardDescription>
            )}
          </div>
          
          {isActive && (
            <Badge variant="default" className="animate-pulse">
              {mode === 'semi_auto' ? '半自動実行中' : '手動モード'}
            </Badge>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* モード選択 */}
        <div className="space-y-3">
          <Label>交渉モード</Label>
          <div className="grid grid-cols-2 gap-3">
            <button
              onClick={() => handleModeChange('manual')}
              className={`p-3 rounded-lg border-2 transition-all ${
                mode === 'manual' 
                  ? 'border-blue-500 bg-blue-50' 
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <User className="h-5 w-5 mx-auto mb-1 text-blue-600" />
              <div className="text-sm font-medium">手動モード</div>
              <div className="text-xs text-gray-600">すべて手動で対応</div>
            </button>

            <button
              onClick={() => handleModeChange('semi_auto')}
              className={`p-3 rounded-lg border-2 transition-all ${
                mode === 'semi_auto' 
                  ? 'border-purple-500 bg-purple-50' 
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <Bot className="h-5 w-5 mx-auto mb-1 text-purple-600" />
              <div className="text-sm font-medium">半自動モード</div>
              <div className="text-xs text-gray-600">異常時は人間判断</div>
            </button>
          </div>
        </div>

        {/* 半自動モードの説明 */}
        {mode === 'semi_auto' && (
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              <strong>半自動モードの動作:</strong>
              <ul className="mt-2 space-y-1 text-sm">
                <li>• 設定に従って自動返信を生成・送信</li>
                <li>• 予算超過時は自動停止して承認待ち</li>
                <li>• ネガティブ感情検出時は人間に引き継ぎ</li>
                <li>• 緊急停止キーワード検出で即座に停止</li>
              </ul>
            </AlertDescription>
          </Alert>
        )}

        {/* 現在の設定サマリー */}
        {mode === 'semi_auto' && (
          <div className="p-3 bg-gray-50 rounded-lg space-y-2">
            <div className="text-sm font-medium flex items-center gap-2">
              <Settings className="h-4 w-4" />
              半自動モード設定
            </div>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div>
                <span className="text-gray-600">最大ラウンド:</span>
                <span className="ml-2 font-medium">{settings?.maxRounds || 3}回</span>
              </div>
              <div>
                <span className="text-gray-600">自動承認閾値:</span>
                <span className="ml-2 font-medium">{settings?.autoApprovalThreshold || 75}%</span>
              </div>
              <div>
                <span className="text-gray-600">予算柔軟性:</span>
                <span className="ml-2 font-medium">±{settings?.budgetFlexibilityLimit || 15}%</span>
              </div>
              <div>
                <span className="text-gray-600">稼働時間:</span>
                <span className="ml-2 font-medium">
                  {settings?.workingHours?.start || 9}:00-{settings?.workingHours?.end || 18}:00
                </span>
              </div>
            </div>
          </div>
        )}

        {/* ステータス表示 */}
        {status && isActive && (
          <div className="p-3 bg-blue-50 rounded-lg">
            <div className="text-sm space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-gray-600">現在のラウンド:</span>
                <span className="font-medium">{status.roundNumber}</span>
              </div>
              {status.lastAction && (
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">最終アクション:</span>
                  <span className="font-medium">{status.lastAction}</span>
                </div>
              )}
              {status.escalationReason && (
                <div className="mt-2 p-2 bg-yellow-100 rounded">
                  <div className="flex items-center gap-2 text-yellow-800">
                    <AlertCircle className="h-4 w-4" />
                    <span className="text-sm">エスカレーション: {status.escalationReason}</span>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* 開始/停止ボタン */}
        <Button
          onClick={toggleAutomation}
          disabled={isLoading || mode === 'manual'}
          className={`w-full ${
            isActive 
              ? 'bg-red-600 hover:bg-red-700' 
              : 'bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700'
          }`}
        >
          {isLoading ? (
            <>処理中...</>
          ) : isActive ? (
            <>
              <Pause className="h-4 w-4 mr-2" />
              自動化を停止
            </>
          ) : (
            <>
              <Play className="h-4 w-4 mr-2" />
              {mode === 'semi_auto' ? '半自動を開始' : '手動モード'}
            </>
          )}
        </Button>

        {/* 設定ページへのリンク */}
        <div className="text-center">
          <a 
            href="/settings/auto-negotiation" 
            className="text-sm text-blue-600 hover:text-blue-800"
          >
            詳細設定を変更 →
          </a>
        </div>
      </CardContent>
    </Card>
  );
}