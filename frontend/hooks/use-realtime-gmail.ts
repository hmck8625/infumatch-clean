import { useState, useEffect, useRef, useCallback } from 'react';
import { EmailThread } from '@/lib/gmail';
import { notificationService } from '@/lib/notification-service';
import { useAuthError } from './use-auth-error';

interface RealtimeGmailOptions {
  pollInterval?: number; // ポーリング間隔（ミリ秒）
  enableNotifications?: boolean;
  autoRefresh?: boolean;
}

interface RealtimeGmailState {
  threads: EmailThread[];
  isLoading: boolean;
  lastUpdated: Date | null;
  error: string | null;
  newThreadsCount: number;
}

export function useRealtimeGmail(
  initialThreads: EmailThread[] = [],
  options: RealtimeGmailOptions = {}
) {
  const {
    pollInterval = 30000, // デフォルト30秒
    enableNotifications = false,
    autoRefresh = true,
  } = options;

  const [state, setState] = useState<RealtimeGmailState>({
    threads: initialThreads,
    isLoading: false,
    lastUpdated: null,
    error: null,
    newThreadsCount: 0,
  });

  const { handleApiResponse } = useAuthError();
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const lastCheckTimeRef = useRef<number>(Date.now());
  const isPollingRef = useRef<boolean>(false);

  // スレッドを更新
  const updateThreads = useCallback((newThreads: EmailThread[]) => {
    setState(prev => {
      // 新しいスレッドを検出
      const existingIds = new Set(prev.threads.map(t => t.id));
      const newThreadsOnly = newThreads.filter(t => !existingIds.has(t.id));
      
      // 新着通知
      if (enableNotifications && newThreadsOnly.length > 0) {
        newThreadsOnly.forEach(thread => {
          const lastMessage = thread.messages[thread.messages.length - 1];
          if (lastMessage) {
            const from = getHeaderValue(lastMessage, 'from');
            const subject = getHeaderValue(lastMessage, 'subject');
            
            notificationService.showGmailNotification({
              type: 'new_email',
              threadId: thread.id,
              messageId: lastMessage.id,
              from,
              subject,
              snippet: thread.snippet,
              timestamp: parseInt(lastMessage.internalDate),
            });
          }
        });
      }

      return {
        ...prev,
        threads: newThreads,
        lastUpdated: new Date(),
        error: null,
        newThreadsCount: prev.newThreadsCount + newThreadsOnly.length,
      };
    });
  }, [enableNotifications]);

  // エラーを設定
  const setError = useCallback((error: string) => {
    setState(prev => ({ ...prev, error, isLoading: false }));
  }, []);

  // ローディング状態を設定
  const setLoading = useCallback((isLoading: boolean) => {
    setState(prev => ({ ...prev, isLoading }));
  }, []);

  // スレッドを取得
  const fetchThreads = useCallback(async (showLoading = true) => {
    if (isPollingRef.current) return; // 重複実行を防ぐ
    
    try {
      isPollingRef.current = true;
      
      if (showLoading) {
        setLoading(true);
      }

      const response = await fetch('/api/gmail/threads?maxResults=20');
      
      const authErrorHandled = await handleApiResponse(response);
      if (authErrorHandled) {
        setError('認証エラーが発生しました');
        return;
      }

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      const threads: EmailThread[] = data.threads || [];
      
      updateThreads(threads);
      lastCheckTimeRef.current = Date.now();
      
    } catch (error: any) {
      console.error('スレッド取得エラー:', error);
      setError(error.message || 'スレッドの取得に失敗しました');
    } finally {
      isPollingRef.current = false;
      setLoading(false);
    }
  }, [handleApiResponse, setError, setLoading, updateThreads]);

  // 新着メールのみをチェック（軽量版）
  const checkForNewEmails = useCallback(async () => {
    if (isPollingRef.current) return;
    
    try {
      isPollingRef.current = true;
      
      // 最後のチェック時刻以降の新着メールのみを取得
      const lastCheckTime = new Date(lastCheckTimeRef.current);
      const dateAfter = lastCheckTime.toISOString().split('T')[0];
      
      const response = await fetch(`/api/gmail/search?isUnread=true&maxResults=5&dateAfter=${dateAfter}`);
      
      const authErrorHandled = await handleApiResponse(response);
      if (authErrorHandled) return;

      if (response.ok) {
        const data = await response.json();
        const newThreads: EmailThread[] = data.threads || [];
        
        if (newThreads.length > 0) {
          // 既存のスレッドと新しいスレッドをマージ
          setState(prev => {
            const existingIds = new Set(prev.threads.map(t => t.id));
            const uniqueNewThreads = newThreads.filter(t => !existingIds.has(t.id));
            
            if (uniqueNewThreads.length > 0) {
              // 新着通知
              if (enableNotifications) {
                uniqueNewThreads.forEach(thread => {
                  const lastMessage = thread.messages[thread.messages.length - 1];
                  if (lastMessage) {
                    const from = getHeaderValue(lastMessage, 'from');
                    const subject = getHeaderValue(lastMessage, 'subject');
                    
                    notificationService.showGmailNotification({
                      type: 'new_email',
                      threadId: thread.id,
                      messageId: lastMessage.id,
                      from,
                      subject,
                      snippet: thread.snippet,
                      timestamp: parseInt(lastMessage.internalDate),
                    });
                  }
                });
              }
              
              return {
                ...prev,
                threads: [...uniqueNewThreads, ...prev.threads],
                lastUpdated: new Date(),
                newThreadsCount: prev.newThreadsCount + uniqueNewThreads.length,
              };
            }
            
            return prev;
          });
        }
        
        lastCheckTimeRef.current = Date.now();
      }
    } catch (error: any) {
      console.error('新着メールチェックエラー:', error);
    } finally {
      isPollingRef.current = false;
    }
  }, [enableNotifications, handleApiResponse]);

  // ポーリング開始
  const startPolling = useCallback(() => {
    if (pollIntervalRef.current) return; // 既に開始済み
    
    console.log(`🔄 Gmail ポーリング開始 (${pollInterval}ms間隔)`);
    
    pollIntervalRef.current = setInterval(() => {
      if (autoRefresh) {
        checkForNewEmails();
      }
    }, pollInterval);
  }, [pollInterval, autoRefresh, checkForNewEmails]);

  // ポーリング停止
  const stopPolling = useCallback(() => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
      console.log('⏹️ Gmail ポーリング停止');
    }
  }, []);

  // 手動更新
  const refresh = useCallback(() => {
    fetchThreads(true);
  }, [fetchThreads]);

  // 新着数をリセット
  const resetNewCount = useCallback(() => {
    setState(prev => ({ ...prev, newThreadsCount: 0 }));
  }, []);

  // 特定のスレッドを更新
  const updateThread = useCallback((threadId: string, updatedThread: EmailThread) => {
    setState(prev => ({
      ...prev,
      threads: prev.threads.map(t => t.id === threadId ? updatedThread : t),
      lastUpdated: new Date(),
    }));
  }, []);

  // スレッドを削除
  const removeThread = useCallback((threadId: string) => {
    setState(prev => ({
      ...prev,
      threads: prev.threads.filter(t => t.id !== threadId),
      lastUpdated: new Date(),
    }));
  }, []);

  // 初期化時とオプション変更時
  useEffect(() => {
    if (autoRefresh) {
      startPolling();
    }
    
    return () => {
      stopPolling();
    };
  }, [autoRefresh, pollInterval, startPolling, stopPolling]);

  // ページのビジビリティ変更時
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden) {
        // ページが非表示になったらポーリング間隔を長くする
        stopPolling();
        if (autoRefresh) {
          pollIntervalRef.current = setInterval(checkForNewEmails, pollInterval * 2);
        }
      } else {
        // ページが表示されたら通常のポーリングに戻す
        stopPolling();
        if (autoRefresh) {
          startPolling();
          // すぐに最新データを取得
          setTimeout(checkForNewEmails, 1000);
        }
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [autoRefresh, pollInterval, startPolling, stopPolling, checkForNewEmails]);

  return {
    ...state,
    refresh,
    startPolling,
    stopPolling,
    resetNewCount,
    updateThread,
    removeThread,
    isPolling: !!pollIntervalRef.current,
  };
}

// ヘルパー関数
function getHeaderValue(message: any, headerName: string): string {
  const header = message.payload.headers.find(
    (h: any) => h.name.toLowerCase() === headerName.toLowerCase()
  );
  return header?.value || '';
}