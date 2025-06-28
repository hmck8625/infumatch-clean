'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { 
  Play, 
  Pause, 
  Bot, 
  Brain,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  Activity,
  Zap,
  Shield,
  BarChart3,
  ChevronDown,
  ChevronUp
} from 'lucide-react';

type AutomationMode = 'manual' | 'semi_auto';

interface AutomationStatus {
  is_running: boolean;
  mode: AutomationMode;
  active_negotiations: number;
  performance_metrics: {
    total_negotiations: number;
    successful_closures: number;
    failed_negotiations: number;
    average_time_to_close: number;
    total_deal_value: number;
    automation_interventions: number;
  };
}

interface AutomationOrchestratorProps {
  onMonitoringChange?: (isActive: boolean) => void;
}

export default function AutomationOrchestrator({ onMonitoringChange }: AutomationOrchestratorProps = {}) {
  const [status, setStatus] = useState<AutomationStatus | null>(null);
  const [mode, setMode] = useState<AutomationMode>('semi_auto');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchStatus = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/v1/automation/status`);
      
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setStatus(data);
        }
      }
    } catch (err) {
      console.error('ステータス取得エラー:', err);
    }
  };

  const toggleAutomation = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const endpoint = status?.is_running 
        ? `${apiUrl}/api/v1/automation/stop`
        : `${apiUrl}/api/v1/automation/start`;

      const body = status?.is_running 
        ? {}
        : {
            user_id: 'current_user',
            mode: mode,
            company_settings: {} // 実際の設定を取得
          };

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          await fetchStatus();
          
          // フロントエンドでの監視状態を更新
          const shouldMonitor = data.is_running && data.mode === 'semi_auto';
          console.log('🔄 AutomationOrchestrator: 監視状態を更新', {
            is_running: data.is_running,
            mode: data.mode,
            shouldMonitor: shouldMonitor,
            onMonitoringChangeExists: !!onMonitoringChange
          });
          
          if (onMonitoringChange) {
            onMonitoringChange(shouldMonitor);
            console.log('✅ onMonitoringChange呼び出し完了:', shouldMonitor);
          } else {
            console.warn('⚠️ onMonitoringChangeコールバックが設定されていません');
          }
        } else {
          setError(data.message || '操作に失敗しました');
        }
      }
    } catch (err) {
      setError('自動化システムの操作に失敗しました');
    } finally {
      setIsLoading(false);
    }
  };

  const getModeLabel = (mode: AutomationMode) => {
    const labels = {
      manual: '手動モード',
      semi_auto: '半自動モード'
    };
    return labels[mode];
  };

  const getModeDescription = (mode: AutomationMode) => {
    const descriptions = {
      manual: '全ての操作を手動で行います',
      semi_auto: '異常時のみ人間が判断します'
    };
    return descriptions[mode];
  };

  const calculateSuccessRate = () => {
    if (!status?.performance_metrics.total_negotiations) return 0;
    return (status.performance_metrics.successful_closures / status.performance_metrics.total_negotiations) * 100;
  };

  return (
    <Card className="w-full">
      <CardHeader 
        className="cursor-pointer hover:bg-gray-50 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Brain className="h-5 w-5" />
              自動交渉システム設定
              {isExpanded ? (
                <ChevronUp className="h-4 w-4 ml-2" />
              ) : (
                <ChevronDown className="h-4 w-4 ml-2" />
              )}
            </CardTitle>
            <CardDescription>
              全体の自動化設定とパフォーマンス状況
            </CardDescription>
          </div>
          
          {status?.is_running && (
            <Badge variant="default" className="animate-pulse">
              <Activity className="h-3 w-3 mr-1" />
              稼働中
            </Badge>
          )}
        </div>
      </CardHeader>

      {isExpanded && (
        <CardContent className="space-y-6">
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

        {/* モード選択 */}
        <div className="space-y-3">
          <label className="text-sm font-medium">自動化モード</label>
          <Select 
            value={mode} 
            onValueChange={(value) => setMode(value as AutomationMode)}
            disabled={status?.is_running}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="manual">
                <div className="flex items-center gap-2">
                  <Shield className="h-4 w-4" />
                  手動モード
                </div>
              </SelectItem>
              <SelectItem value="semi_auto">
                <div className="flex items-center gap-2">
                  <Bot className="h-4 w-4" />
                  半自動モード
                </div>
              </SelectItem>
            </SelectContent>
          </Select>
          <p className="text-sm text-gray-600">
            {getModeDescription(mode)}
          </p>
        </div>

        {/* パフォーマンスメトリクス */}
        {status && (
          <div className="space-y-4">
            <h4 className="text-sm font-medium flex items-center gap-2">
              <BarChart3 className="h-4 w-4" />
              パフォーマンス指標
            </h4>

            {/* 成功率 */}
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>成功率</span>
                <span className="font-medium">{calculateSuccessRate().toFixed(1)}%</span>
              </div>
              <Progress value={calculateSuccessRate()} className="h-2" />
            </div>

            {/* 統計グリッド */}
            <div className="grid grid-cols-2 gap-3">
              <div className="p-3 bg-blue-50 rounded-lg">
                <p className="text-sm text-blue-600">総交渉数</p>
                <p className="text-2xl font-bold text-blue-900">
                  {status.performance_metrics.total_negotiations}
                </p>
              </div>
              
              <div className="p-3 bg-green-50 rounded-lg">
                <p className="text-sm text-green-600">成約数</p>
                <p className="text-2xl font-bold text-green-900">
                  {status.performance_metrics.successful_closures}
                </p>
              </div>
              
              <div className="p-3 bg-purple-50 rounded-lg">
                <p className="text-sm text-purple-600">AI介入数</p>
                <p className="text-2xl font-bold text-purple-900">
                  {status.performance_metrics.automation_interventions}
                </p>
              </div>
              
              <div className="p-3 bg-orange-50 rounded-lg">
                <p className="text-sm text-orange-600">アクティブ</p>
                <p className="text-2xl font-bold text-orange-900">
                  {status.active_negotiations}
                </p>
              </div>
            </div>

            {/* 平均成約時間 */}
            <div className="p-3 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-600">平均成約時間</p>
              <p className="text-lg font-semibold">
                {(status.performance_metrics.average_time_to_close / 24).toFixed(1)} 日
              </p>
            </div>
          </div>
        )}

        {/* 起動/停止ボタン */}
        <Button
          className={`w-full ${
            status?.is_running 
              ? 'bg-red-600 hover:bg-red-700' 
              : 'bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700'
          }`}
          onClick={toggleAutomation}
          disabled={isLoading}
        >
          {isLoading ? (
            <>処理中...</>
          ) : status?.is_running ? (
            <>
              <Pause className="h-4 w-4 mr-2" />
              自動化を停止
            </>
          ) : (
            <>
              <Play className="h-4 w-4 mr-2" />
              自動化を開始
            </>
          )}
        </Button>

        {/* 半自動モードの説明 */}
        {status?.mode === 'semi_auto' && status?.is_running && (
          <Alert>
            <Bot className="h-4 w-4" />
            <AlertDescription>
              半自動モードで動作中。異常検出時は自動的に停止し、人間の判断を仰ぎます。
            </AlertDescription>
          </Alert>
        )}
        </CardContent>
      )}
    </Card>
  );
}