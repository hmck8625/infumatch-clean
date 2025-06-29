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
  currentAutomationState?: {mode: string, isActive: boolean};
  onModeChange?: (threadId: string, mode: AutomationMode, enabled: boolean) => void;
}

interface AutomationStatus {
  mode: AutomationMode;
  isActive: boolean;
  lastAction?: string;
  escalationReason?: string;
}

export default function ThreadAutomationControl({ 
  threadId, 
  threadSubject,
  currentAutomationState,
  onModeChange 
}: ThreadAutomationProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [settings, setSettings] = useState<any>(null);
  
  // 現在の状態を props から取得
  const mode = (currentAutomationState?.mode as AutomationMode) || 'manual';
  const isActive = currentAutomationState?.isActive || false;

  useEffect(() => {
    // 自動交渉設定を読み込み
    const savedSettings = localStorage.getItem('autoNegotiationSettings');
    if (savedSettings) {
      setSettings(JSON.parse(savedSettings));
    }
    
    // ローカルストレージから自動化状態を復元
    const threadStates = JSON.parse(localStorage.getItem('threadAutomationStates') || '{}');
    const threadState = threadStates[threadId];
    
    if (threadState && threadState.enabled) {
      console.log(`🔄 スレッド ${threadId} の自動化状態復元:`, threadState);
      // 既に親コンポーネントから currentAutomationState を受け取っているので、
      // ここでは確認のみ行う
    }
  }, [threadId]);


  const startSemiAuto = async () => {
    setIsLoading(true);
    
    try {
      // 既存の automation status エンドポイントを使用
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      
      // まず現在のステータスを確認
      const statusResponse = await fetch(`${apiUrl}/api/v1/automation/status`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      });

      if (statusResponse.ok) {
        const statusData = await statusResponse.json();
        console.log('🤖 自動化ステータス確認:', statusData);
        
        // ローカルで半自動モードを開始したことを記録
        const automationState = {
          threadId,
          mode: 'semi_auto',
          enabled: true,
          settings: settings,
          startedAt: new Date().toISOString()
        };
        
        // ローカルストレージに保存
        const existingStates = JSON.parse(localStorage.getItem('threadAutomationStates') || '{}');
        existingStates[threadId] = automationState;
        localStorage.setItem('threadAutomationStates', JSON.stringify(existingStates));
        
        console.log(`🚀 スレッド ${threadId} の半自動モード開始 (ローカル管理)`);
        
        // 親コンポーネントに通知
        onModeChange?.(threadId, 'semi_auto', true);
      } else {
        throw new Error('自動化ステータスの確認に失敗しました');
      }
    } catch (error) {
      console.error('半自動開始エラー:', error);
      
      // フォールバック: エラーでもローカルで開始
      const automationState = {
        threadId,
        mode: 'semi_auto',
        enabled: true,
        settings: settings,
        startedAt: new Date().toISOString(),
        fallback: true
      };
      
      const existingStates = JSON.parse(localStorage.getItem('threadAutomationStates') || '{}');
      existingStates[threadId] = automationState;
      localStorage.setItem('threadAutomationStates', JSON.stringify(existingStates));
      
      console.log(`⚠️ フォールバック: スレッド ${threadId} の半自動モード開始 (ローカル管理のみ)`);
      onModeChange?.(threadId, 'semi_auto', true);
    } finally {
      setIsLoading(false);
    }
  };
  
  const stopAutomation = async () => {
    setIsLoading(true);
    
    try {
      // ローカルストレージから削除
      const existingStates = JSON.parse(localStorage.getItem('threadAutomationStates') || '{}');
      delete existingStates[threadId];
      localStorage.setItem('threadAutomationStates', JSON.stringify(existingStates));
      
      console.log(`⏹️ スレッド ${threadId} の自動化停止 (ローカル管理)`);
      
      // 親コンポーネントに通知
      onModeChange?.(threadId, 'manual', false);
    } catch (error) {
      console.error('自動化停止エラー:', error);
    } finally {
      setIsLoading(false);
    }
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
          
          {isActive && mode === 'semi_auto' && (
            <Badge variant="default" className="animate-pulse">
              半自動実行中
            </Badge>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* 現在の状態表示 */}
        <div className="p-3 bg-gray-50 rounded-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {mode === 'semi_auto' ? (
                <>
                  <Bot className="h-5 w-5 text-purple-600" />
                  <span className="font-medium">半自動モード</span>
                </>
              ) : (
                <>
                  <User className="h-5 w-5 text-blue-600" />
                  <span className="font-medium">手動モード</span>
                </>
              )}
            </div>
            <div className="text-sm text-gray-600">
              {isActive ? '動作中' : '停止中'}
            </div>
          </div>
        </div>


        {/* 設定情報 */}
        {mode === 'semi_auto' && settings && (
          <div className="p-3 bg-purple-50 rounded-lg space-y-2">
            <div className="text-sm font-medium flex items-center gap-2">
              <Settings className="h-4 w-4" />
              半自動モード設定
            </div>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div>
                <span className="text-gray-600">自動承認閾値:</span>
                <span className="ml-2 font-medium">{settings?.autoApprovalThreshold || 75}%</span>
              </div>
              <div>
                <span className="text-gray-600">予算柔軟性:</span>
                <span className="ml-2 font-medium">±{settings?.budgetFlexibilityLimit || 15}%</span>
              </div>
              <div className="col-span-2">
                <span className="text-gray-600">稼働時間:</span>
                <span className="ml-2 font-medium">
                  {settings?.workingHours?.start || 9}:00-{settings?.workingHours?.end || 18}:00
                </span>
              </div>
            </div>
          </div>
        )}


        {/* アクションボタン */}
        {mode === 'semi_auto' && isActive ? (
          <Button
            onClick={stopAutomation}
            disabled={isLoading}
            className="w-full bg-red-600 hover:bg-red-700"
          >
            {isLoading ? (
              <>処理中...</>
            ) : (
              <>
                <Pause className="h-4 w-4 mr-2" />
                🛑 自動化を停止
              </>
            )}
          </Button>
        ) : (
          <Button
            onClick={startSemiAuto}
            disabled={isLoading}
            className="w-full bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700"
          >
            {isLoading ? (
              <>処理中...</>
            ) : (
              <>
                <Play className="h-4 w-4 mr-2" />
                🤖 半自動を開始
              </>
            )}
          </Button>
        )}

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