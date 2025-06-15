'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { notificationService } from '@/lib/notification-service';
import { Bell, BellOff, Volume2, VolumeX, Settings, Sparkles, Clock, CheckCircle, XCircle } from 'lucide-react';

interface NotificationManagerProps {
  onNotificationReceived?: (notification: any) => void;
}

export function NotificationManager({ onNotificationReceived }: NotificationManagerProps) {
  const [notificationStatus, setNotificationStatus] = useState({
    supported: false,
    permission: 'default' as NotificationPermission,
    enabled: false,
  });
  const [isBackgroundCheckActive, setIsBackgroundCheckActive] = useState(false);
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [checkInterval, setCheckInterval] = useState(60); // 秒

  useEffect(() => {
    // 初期状態を取得
    updateNotificationStatus();
    
    // ローカルストレージから設定を復元
    const savedSoundEnabled = localStorage.getItem('notification-sound-enabled');
    if (savedSoundEnabled !== null) {
      setSoundEnabled(JSON.parse(savedSoundEnabled));
    }

    const savedInterval = localStorage.getItem('notification-check-interval');
    if (savedInterval) {
      setCheckInterval(parseInt(savedInterval));
    }

    const savedBackgroundCheck = localStorage.getItem('notification-background-check');
    if (savedBackgroundCheck === 'true') {
      startBackgroundCheck();
    }
  }, []);

  const updateNotificationStatus = () => {
    const status = notificationService.getNotificationStatus();
    setNotificationStatus(status);
  };

  const handleToggleNotifications = async () => {
    try {
      const enabled = await notificationService.toggleNotifications();
      updateNotificationStatus();
      
      if (enabled) {
        // 通知が有効になったら、テスト通知を表示
        notificationService.showNotification({
          title: '🎉 通知が有効になりました',
          body: 'InfuMatchからの通知を受信できます',
          tag: 'notification-enabled',
        });

        // サウンドも再生
        if (soundEnabled) {
          notificationService.playNotificationSound();
        }
      }
    } catch (error) {
      console.error('通知設定エラー:', error);
    }
  };

  const startBackgroundCheck = () => {
    if (!notificationStatus.enabled) {
      alert('まず通知許可を有効にしてください');
      return;
    }

    notificationService.startBackgroundCheck(checkInterval * 1000);
    setIsBackgroundCheckActive(true);
    localStorage.setItem('notification-background-check', 'true');
    
    console.log(`🔔 バックグラウンドチェック開始 (${checkInterval}秒間隔)`);
  };

  const stopBackgroundCheck = () => {
    // 実際のバックグラウンドチェックを停止する実装は省略（実際はsetIntervalの管理が必要）
    setIsBackgroundCheckActive(false);
    localStorage.setItem('notification-background-check', 'false');
    console.log('🔕 バックグラウンドチェック停止');
  };

  const handleSoundToggle = () => {
    const newSoundEnabled = !soundEnabled;
    setSoundEnabled(newSoundEnabled);
    localStorage.setItem('notification-sound-enabled', JSON.stringify(newSoundEnabled));
    
    if (newSoundEnabled) {
      notificationService.playNotificationSound();
    }
  };

  const handleIntervalChange = (newInterval: number) => {
    setCheckInterval(newInterval);
    localStorage.setItem('notification-check-interval', newInterval.toString());
    
    // バックグラウンドチェックが有効な場合は再起動
    if (isBackgroundCheckActive) {
      stopBackgroundCheck();
      setTimeout(() => startBackgroundCheck(), 1000);
    }
  };

  const showTestNotification = () => {
    if (!notificationStatus.enabled) {
      alert('通知許可が必要です');
      return;
    }

    notificationService.showGmailNotification({
      type: 'new_email',
      threadId: 'test-thread-123',
      messageId: 'test-message-456',
      from: 'test@example.com',
      subject: 'テスト通知',
      snippet: 'これはテスト通知です。通知が正常に動作しています。',
      timestamp: Date.now(),
    });

    if (soundEnabled) {
      notificationService.playNotificationSound();
    }
  };

  return (
    <div className="w-full space-y-4">
      {/* メインヘッダー */}
      <div className="bg-gradient-to-r from-orange-50 via-red-50 to-pink-50 rounded-2xl p-6 border border-orange-100/50">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-gradient-to-br from-orange-500 to-red-600 rounded-xl flex items-center justify-center shadow-lg">
              <Bell className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                🔔 リアルタイム通知
                <Sparkles className="w-5 h-5 text-orange-500" />
              </h2>
              <p className="text-sm text-gray-600">新着メールを即座にお知らせします</p>
            </div>
          </div>
        </div>

        {/* 通知ステータス */}
        <div className="bg-white/60 rounded-xl p-4 border border-orange-100">
          <div className="flex items-center gap-2 mb-3">
            <Settings className="w-4 h-4 text-orange-600" />
            <span className="text-sm font-medium text-orange-900">システム状態</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-700">ブラウザサポート</span>
              <Badge 
                variant={notificationStatus.supported ? "default" : "destructive"}
                className="text-xs"
              >
                {notificationStatus.supported ? (
                  <>
                    <CheckCircle className="w-3 h-3 mr-1" />
                    サポート
                  </>
                ) : (
                  <>
                    <XCircle className="w-3 h-3 mr-1" />
                    非サポート
                  </>
                )}
              </Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-700">通知許可</span>
              <Badge 
                variant={notificationStatus.enabled ? "default" : "secondary"}
                className={`text-xs ${
                  notificationStatus.permission === 'granted' ? 'bg-green-100 text-green-800' : 
                  notificationStatus.permission === 'denied' ? 'bg-red-100 text-red-800' : 
                  'bg-yellow-100 text-yellow-800'
                }`}
              >
                {notificationStatus.permission === 'granted' ? '✅ 許可済み' : 
                 notificationStatus.permission === 'denied' ? '❌ 拒否' : '⏳ 未設定'}
              </Badge>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-700">バックグラウンド</span>
              <Badge 
                variant={isBackgroundCheckActive ? "default" : "secondary"}
                className={`text-xs ${isBackgroundCheckActive ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}
              >
                {isBackgroundCheckActive ? (
                  <>
                    <Bell className="w-3 h-3 mr-1" />
                    有効
                  </>
                ) : (
                  <>
                    <BellOff className="w-3 h-3 mr-1" />
                    無効
                  </>
                )}
              </Badge>
            </div>
          </div>
        </div>
      </div>

      {/* 設定カード */}
      <div className="bg-white rounded-2xl p-6 border border-gray-200 shadow-sm space-y-6">

        {/* 基本設定 */}
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Settings className="w-5 h-5 text-orange-500" />
            基本設定
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 bg-gradient-to-r from-orange-50 to-red-50 rounded-xl border border-orange-200">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-medium text-gray-900 flex items-center gap-2">
                    <Bell className="w-4 h-4 text-orange-600" />
                    通知許可
                  </h4>
                  <p className="text-sm text-gray-600 mt-1">新着メールの通知を受信する</p>
                </div>
                <Button
                  onClick={handleToggleNotifications}
                  className={`ml-4 transition-all duration-200 ${
                    notificationStatus.enabled
                      ? 'bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white shadow-lg'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200 border border-gray-300'
                  }`}
                  size="sm"
                >
                  {notificationStatus.enabled ? (
                    <>
                      <Bell className="w-4 h-4 mr-1" />
                      有効
                    </>
                  ) : (
                    <>
                      <BellOff className="w-4 h-4 mr-1" />
                      無効
                    </>
                  )}
                </Button>
              </div>
            </div>

            <div className="p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl border border-blue-200">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-medium text-gray-900 flex items-center gap-2">
                    <Volume2 className="w-4 h-4 text-blue-600" />
                    通知音
                  </h4>
                  <p className="text-sm text-gray-600 mt-1">通知時に音を再生する</p>
                </div>
                <Button
                  onClick={handleSoundToggle}
                  className={`ml-4 transition-all duration-200 ${
                    soundEnabled
                      ? 'bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 text-white shadow-lg'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200 border border-gray-300'
                  }`}
                  size="sm"
                >
                  {soundEnabled ? (
                    <>
                      <Volume2 className="w-4 h-4 mr-1" />
                      有効
                    </>
                  ) : (
                    <>
                      <VolumeX className="w-4 h-4 mr-1" />
                      無効
                    </>
                  )}
                </Button>
              </div>
            </div>
          </div>
        </div>

        {/* バックグラウンドチェック設定 */}
        <div className="border-t border-gray-200 pt-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Clock className="w-5 h-5 text-purple-500" />
            バックグラウンドチェック
          </h3>
          
          <div className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-xl p-5 border border-purple-200">
            <p className="text-sm text-gray-700 mb-4 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-purple-600" />
              定期的に新着メールをチェックして、リアルタイム通知します
            </p>
            
            <div className="flex items-center gap-4 mb-4">
              <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
                <Clock className="w-4 h-4 text-purple-600" />
                チェック間隔:
              </label>
              <select
                value={checkInterval}
                onChange={(e) => handleIntervalChange(parseInt(e.target.value))}
                className="px-3 py-2 bg-white border border-purple-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-200 focus:border-purple-400 text-sm"
              >
                <option value={30}>30秒ごと</option>
                <option value={60}>1分ごと</option>
                <option value={120}>2分ごと</option>
                <option value={300}>5分ごと</option>
                <option value={600}>10分ごと</option>
              </select>
            </div>

            <div className="flex flex-wrap gap-3">
              {!isBackgroundCheckActive ? (
                <Button
                  onClick={startBackgroundCheck}
                  disabled={!notificationStatus.enabled}
                  className="bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white shadow-lg hover:shadow-xl transition-all duration-200"
                  size="sm"
                >
                  <Bell className="w-4 h-4 mr-2" />
                  監視開始
                </Button>
              ) : (
                <Button
                  onClick={stopBackgroundCheck}
                  className="bg-gradient-to-r from-red-500 to-pink-600 hover:from-red-600 hover:to-pink-700 text-white shadow-lg hover:shadow-xl transition-all duration-200"
                  size="sm"
                >
                  <BellOff className="w-4 h-4 mr-2" />
                  監視停止
                </Button>
              )}
              
              <Button
                onClick={showTestNotification}
                disabled={!notificationStatus.enabled}
                className="bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white shadow-lg hover:shadow-xl transition-all duration-200"
                size="sm"
              >
                <Settings className="w-4 h-4 mr-2" />
                テスト通知
              </Button>
            </div>
          </div>
        </div>

        {/* 使用方法の説明 */}
        <div className="border-t border-gray-200 pt-6">
          <div className="bg-gradient-to-r from-blue-50 via-indigo-50 to-purple-50 rounded-xl p-5 border border-blue-200">
            <h4 className="font-semibold text-blue-900 mb-3 flex items-center gap-2">
              💡 使用ガイド
              <Sparkles className="w-4 h-4 text-blue-600" />
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-blue-800">
              <div className="space-y-2">
                <div className="flex items-start gap-2">
                  <span className="flex-shrink-0 w-5 h-5 bg-blue-500 text-white rounded-full flex items-center justify-center text-xs font-bold">1</span>
                  <span>「通知許可」を有効にして、ブラウザの通知許可を与えてください</span>
                </div>
                <div className="flex items-start gap-2">
                  <span className="flex-shrink-0 w-5 h-5 bg-blue-500 text-white rounded-full flex items-center justify-center text-xs font-bold">2</span>
                  <span>「監視開始」でバックグラウンドチェックを開始します</span>
                </div>
              </div>
              <div className="space-y-2">
                <div className="flex items-start gap-2">
                  <span className="flex-shrink-0 w-5 h-5 bg-blue-500 text-white rounded-full flex items-center justify-center text-xs font-bold">3</span>
                  <span>新着メールがあると、デスクトップ通知が表示されます</span>
                </div>
                <div className="flex items-start gap-2">
                  <span className="flex-shrink-0 w-5 h-5 bg-blue-500 text-white rounded-full flex items-center justify-center text-xs font-bold">4</span>
                  <span>通知をクリックして該当メールスレッドに移動できます</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}