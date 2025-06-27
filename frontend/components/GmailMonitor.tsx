'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Play, 
  Pause, 
  RefreshCw, 
  Mail, 
  Clock, 
  AlertCircle,
  CheckCircle,
  Activity
} from 'lucide-react';

interface MonitorStats {
  total_checks: number;
  new_threads_found: number;
  auto_negotiations_started: number;
  errors: number;
  last_check_time: string | null;
}

interface MonitorConfig {
  check_interval_seconds: number;
  max_threads_per_check: number;
  label_filter: string;
}

export default function GmailMonitor() {
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [stats, setStats] = useState<MonitorStats>({
    total_checks: 0,
    new_threads_found: 0,
    auto_negotiations_started: 0,
    errors: 0,
    last_check_time: null
  });
  const [config, setConfig] = useState<MonitorConfig>({
    check_interval_seconds: 60,
    max_threads_per_check: 10,
    label_filter: 'INBOX'
  });
  const [lastError, setLastError] = useState<string | null>(null);

  // 状態を定期的に更新
  useEffect(() => {
    fetchMonitorStatus();
    
    const interval = setInterval(() => {
      if (isMonitoring) {
        fetchMonitorStatus();
      }
    }, 5000); // 5秒ごとに更新

    return () => clearInterval(interval);
  }, [isMonitoring]);

  const fetchMonitorStatus = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/v1/negotiation/gmail-monitor/status`);
      if (response.ok) {
        const data = await response.json();
        setIsMonitoring(data.is_monitoring);
        setStats(data.stats);
        setConfig(data.monitor_config);
      }
    } catch (error) {
      console.error('監視状態の取得に失敗:', error);
    }
  };

  const toggleMonitoring = async () => {
    setIsLoading(true);
    setLastError(null);
    
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const endpoint = isMonitoring 
        ? `${apiUrl}/api/v1/negotiation/gmail-monitor/stop`
        : `${apiUrl}/api/v1/negotiation/gmail-monitor/start`;
        
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: 'current_user', // 実際のユーザーIDを使用
          monitor_config: config
        })
      });

      if (response.ok) {
        const data = await response.json();
        setIsMonitoring(!isMonitoring);
        console.log(`Gmail監視${isMonitoring ? '停止' : '開始'}:`, data);
      } else {
        throw new Error('監視状態の変更に失敗しました');
      }
    } catch (error) {
      setLastError(error instanceof Error ? error.message : '不明なエラー');
      console.error('監視トグルエラー:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const formatLastCheckTime = (timestamp: string | null) => {
    if (!timestamp) return '未実行';
    
    const date = new Date(timestamp);
    const now = new Date();
    const diffMinutes = Math.floor((now.getTime() - date.getTime()) / 60000);
    
    if (diffMinutes < 1) return 'たった今';
    if (diffMinutes < 60) return `${diffMinutes}分前`;
    if (diffMinutes < 1440) return `${Math.floor(diffMinutes / 60)}時間前`;
    return date.toLocaleDateString('ja-JP');
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Mail className="h-5 w-5" />
              Gmail自動監視
            </CardTitle>
            <CardDescription>
              新着メールを自動的に検出して交渉を開始します
            </CardDescription>
          </div>
          
          <div className="flex items-center gap-3">
            {isMonitoring ? (
              <Badge variant="default" className="animate-pulse">
                <Activity className="h-3 w-3 mr-1" />
                監視中
              </Badge>
            ) : (
              <Badge variant="secondary">
                <Pause className="h-3 w-3 mr-1" />
                停止中
              </Badge>
            )}
            
            <Switch
              checked={isMonitoring}
              onCheckedChange={toggleMonitoring}
              disabled={isLoading}
            />
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* エラー表示 */}
        {lastError && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{lastError}</AlertDescription>
          </Alert>
        )}
        
        {/* 監視設定 */}
        <div className="grid grid-cols-3 gap-4 p-4 bg-gray-50 rounded-lg">
          <div>
            <p className="text-sm text-gray-600">チェック間隔</p>
            <p className="font-medium">{config.check_interval_seconds}秒</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">最大処理数/回</p>
            <p className="font-medium">{config.max_threads_per_check}件</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">監視ラベル</p>
            <p className="font-medium">{config.label_filter}</p>
          </div>
        </div>
        
        {/* 統計情報 */}
        <div className="space-y-3">
          <h4 className="text-sm font-medium text-gray-700">監視統計</h4>
          
          <div className="grid grid-cols-2 gap-3">
            <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
              <div>
                <p className="text-sm text-blue-600">チェック回数</p>
                <p className="text-2xl font-bold text-blue-900">{stats.total_checks}</p>
              </div>
              <RefreshCw className="h-8 w-8 text-blue-400" />
            </div>
            
            <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
              <div>
                <p className="text-sm text-green-600">新着検出</p>
                <p className="text-2xl font-bold text-green-900">{stats.new_threads_found}</p>
              </div>
              <Mail className="h-8 w-8 text-green-400" />
            </div>
            
            <div className="flex items-center justify-between p-3 bg-purple-50 rounded-lg">
              <div>
                <p className="text-sm text-purple-600">自動交渉開始</p>
                <p className="text-2xl font-bold text-purple-900">{stats.auto_negotiations_started}</p>
              </div>
              <CheckCircle className="h-8 w-8 text-purple-400" />
            </div>
            
            <div className="flex items-center justify-between p-3 bg-red-50 rounded-lg">
              <div>
                <p className="text-sm text-red-600">エラー</p>
                <p className="text-2xl font-bold text-red-900">{stats.errors}</p>
              </div>
              <AlertCircle className="h-8 w-8 text-red-400" />
            </div>
          </div>
          
          {/* 最終チェック時刻 */}
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <Clock className="h-4 w-4" />
            <span>最終チェック: {formatLastCheckTime(stats.last_check_time)}</span>
          </div>
        </div>
        
        {/* アクションボタン */}
        <div className="flex justify-end gap-2 pt-2">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchMonitorStatus}
            disabled={isLoading}
          >
            <RefreshCw className="h-4 w-4 mr-1" />
            更新
          </Button>
          
          <Button
            variant={isMonitoring ? "destructive" : "default"}
            size="sm"
            onClick={toggleMonitoring}
            disabled={isLoading}
          >
            {isLoading ? (
              <>処理中...</>
            ) : isMonitoring ? (
              <>
                <Pause className="h-4 w-4 mr-1" />
                監視停止
              </>
            ) : (
              <>
                <Play className="h-4 w-4 mr-1" />
                監視開始
              </>
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}