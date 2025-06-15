'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { signOut } from 'next-auth/react';
import { EmailThread, GmailMessage } from '@/lib/gmail';
import { ErrorBoundary, useErrorHandler } from '@/components/error-boundary';
import { AuthGuard, UserInfo } from '@/components/auth-guard';
import { useAuthError } from '@/hooks/use-auth-error';
import { AttachmentDisplay } from '@/components/attachment-display';
import { AttachmentUpload } from '@/components/attachment-upload';
import { EmailSearch } from '@/components/email-search';
import { NotificationManager } from '@/components/notification-manager';
import { useRealtimeGmail } from '@/hooks/use-realtime-gmail';
import { SearchFilters } from '@/lib/gmail';

export default function MessagesPage() {
  const searchParams = useSearchParams();
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const handleError = useErrorHandler();
  const { handleApiResponse, isAuthenticated: authStatus } = useAuthError();
  const [selectedThread, setSelectedThread] = useState<string | null>(null);
  const [threads, setThreads] = useState<EmailThread[]>([]);
  const [currentThread, setCurrentThread] = useState<EmailThread | null>(null);
  const [replyText, setReplyText] = useState('');
  const [isVisible, setIsVisible] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [isLoadingThreads, setIsLoadingThreads] = useState(false);
  const [replyPatterns, setReplyPatterns] = useState<any[]>([]);
  const [isGeneratingPatterns, setIsGeneratingPatterns] = useState(false);
  const [threadAnalysis, setThreadAnalysis] = useState<any>(null);
  const [attachmentFiles, setAttachmentFiles] = useState<File[]>([]);
  const [showSearch, setShowSearch] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const [searchFilters, setSearchFilters] = useState<SearchFilters>({});
  
  // 新規メール作成用の状態
  const [isComposingNew, setIsComposingNew] = useState(false);
  const [newEmailTo, setNewEmailTo] = useState('');
  const [newEmailSubject, setNewEmailSubject] = useState('');
  const [newEmailBody, setNewEmailBody] = useState('');
  const [isSendingNewEmail, setIsSendingNewEmail] = useState(false);
  
  // リアルタイムGmail機能
  const {
    threads: realtimeThreads,
    isLoading: isRealtimeLoading,
    lastUpdated,
    newThreadsCount,
    refresh: refreshRealtime,
    resetNewCount,
    isPolling,
    startPolling,
    stopPolling,
  } = useRealtimeGmail(threads, {
    pollInterval: 30000, // 30秒間隔
    enableNotifications: true,
    autoRefresh: true,
  });

  useEffect(() => {
    setIsVisible(true);
    checkAuth();

    // URLパラメータからコラボ提案情報を取得
    const to = searchParams.get('to');
    const subject = searchParams.get('subject');
    const body = searchParams.get('body');
    const influencer = searchParams.get('influencer');
    
    if (to || subject || body) {
      setIsComposingNew(true);
      setNewEmailTo(to || '');
      setNewEmailSubject(subject || '');
      setNewEmailBody(body || '');
    }

    // Chrome拡張機能のエラーをキャッチ
    const handleGlobalError = (event: ErrorEvent) => {
      // Chrome拡張機能のエラーをサイレントに処理
      if (event.filename?.includes('chrome-extension://')) {
        event.preventDefault();
        console.warn('Chrome extension error caught and ignored:', event.error);
        return true;
      }
    };

    const handleUnhandledRejection = (event: PromiseRejectionEvent) => {
      // Promise rejection のエラーもキャッチ
      if (event.reason?.stack?.includes('chrome-extension://')) {
        event.preventDefault();
        console.warn('Chrome extension promise rejection caught and ignored:', event.reason);
      }
    };

    window.addEventListener('error', handleGlobalError);
    window.addEventListener('unhandledrejection', handleUnhandledRejection);

    return () => {
      window.removeEventListener('error', handleGlobalError);
      window.removeEventListener('unhandledrejection', handleUnhandledRejection);
    };
  }, [searchParams]);

  useEffect(() => {
    if (isAuthenticated) {
      loadThreads();
    }
  }, [isAuthenticated]);
  
  // リアルタイムスレッドが更新されたらローカル状態も更新
  useEffect(() => {
    if (realtimeThreads.length > 0) {
      setThreads(realtimeThreads);
    }
  }, [realtimeThreads]);

  useEffect(() => {
    if (selectedThread) {
      loadThreadDetails(selectedThread);
    }
  }, [selectedThread]);

  useEffect(() => {
    if (currentThread && currentThread.messages.length > 0) {
      generateReplyPatterns();
    }
  }, [currentThread]);

  const checkAuth = async () => {
    try {
      console.log('🔐 Checking authentication...');
      const response = await fetch('/api/auth/session');
      const session = await response.json();
      
      console.log('Session response:', {
        hasUser: !!session?.user,
        userEmail: session?.user?.email,
        hasAccessToken: !!session?.accessToken,
        expires: session?.expires
      });
      
      const authenticated = !!(session?.user && session?.accessToken);
      setIsAuthenticated(authenticated);
      
      console.log('Authentication status:', authenticated);
      
      if (authenticated) {
        console.log('✅ User is authenticated, will load threads');
      } else {
        console.log('❌ User is not authenticated');
      }
    } catch (error) {
      console.error('認証確認エラー:', error);
      setIsAuthenticated(false);
    } finally {
      setIsLoading(false);
    }
  };

  const loadThreads = async () => {
    console.log('📧 loadThreads called');
    console.log('isAuthenticated:', isAuthenticated);
    
    if (!isAuthenticated) {
      console.log('⚠️ Not authenticated, skipping thread loading');
      return;
    }
    
    setIsLoadingThreads(true);
    try {
      let url = '/api/gmail/threads';
      
      // 検索フィルタがある場合は検索APIを使用
      if (Object.keys(searchFilters).length > 0) {
        const params = new URLSearchParams();
        
        Object.entries(searchFilters).forEach(([key, value]) => {
          if (value !== undefined && value !== null && value !== '') {
            if (value instanceof Date) {
              params.append(key, value.toISOString().split('T')[0]);
            } else if (Array.isArray(value)) {
              params.append(key, value.join(','));
            } else {
              params.append(key, value.toString());
            }
          }
        });
        
        url = `/api/gmail/search?${params.toString()}`;
      }
      
      console.log('Making request to:', url);
      const response = await fetch(url);
      
      console.log('Response status:', response.status);
      console.log('Response ok:', response.ok);
      
      // 認証エラーをチェック
      const authErrorHandled = await handleApiResponse(response);
      if (authErrorHandled) {
        console.log('Auth error handled, stopping');
        return;
      }
      
      if (response.ok) {
        const data = await response.json();
        console.log('Threads data received:', data);
        setThreads(data.threads || []);
      } else {
        const errorText = await response.text();
        console.warn('Failed to load threads:', response.status, response.statusText, errorText);
      }
    } catch (error) {
      handleError(error);
      console.error('スレッド読み込みエラー:', error);
    } finally {
      setIsLoadingThreads(false);
    }
  };
  
  // 検索実行
  const handleSearch = (filters: SearchFilters) => {
    setSearchFilters(filters);
    setShowSearch(false);
    loadThreads();
  };
  
  // 検索クリア
  const handleClearSearch = () => {
    setSearchFilters({});
    loadThreads();
  };

  const loadThreadDetails = async (threadId: string) => {
    try {
      const response = await fetch(`/api/gmail/threads/${threadId}`);
      
      // 認証エラーをチェック
      const authErrorHandled = await handleApiResponse(response);
      if (authErrorHandled) {
        return;
      }
      
      if (response.ok) {
        const data = await response.json();
        setCurrentThread(data.thread);
      }
    } catch (error) {
      console.error('スレッド詳細読み込みエラー:', error);
    }
  };

  const generateReplyPatterns = async () => {
    if (!currentThread || currentThread.messages.length === 0) return;
    
    setIsGeneratingPatterns(true);
    setReplyPatterns([]);
    setThreadAnalysis(null);
    
    try {
      // メッセージを適切な形式に変換
      const threadMessages = currentThread.messages.map(message => ({
        sender: getInfluencerName(message),
        content: getEmailBody(message),
        date: new Date(parseInt(message.internalDate)).toISOString(),
        isFromUser: isFromUser(message)
      }));

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'}/api/v1/negotiation/reply-patterns`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email_thread: {
            id: currentThread.id,
            subject: getThreadSubject(currentThread),
            participants: [
              'InfuMatch担当者',
              getThreadPrimaryContact(currentThread)
            ]
          },
          thread_messages: threadMessages,
          context: {
            platform: 'gmail',
            thread_length: currentThread.messages.length
          }
        })
      });

      if (response.ok) {
        const result = await response.json();
        if (result.success && result.metadata) {
          setReplyPatterns(result.metadata.reply_patterns || []);
          setThreadAnalysis(result.metadata.thread_analysis || null);
        }
      } else {
        console.error('返信パターン生成エラー:', response.status, response.statusText);
      }
    } catch (error) {
      console.error('返信パターン生成エラー:', error);
    } finally {
      setIsGeneratingPatterns(false);
    }
  };

  const handleLogout = async () => {
    try {
      await signOut({ 
        callbackUrl: '/',
        redirect: true 
      });
    } catch (error) {
      console.error('ログアウトエラー:', error);
    }
  };

  const handleSendNewEmail = async () => {
    if (!newEmailTo.trim() || !newEmailSubject.trim() || !newEmailBody.trim()) {
      alert('宛先、件名、本文をすべて入力してください');
      return;
    }

    setIsSendingNewEmail(true);
    try {
      const response = await fetch('/api/gmail/send', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          to: newEmailTo,
          subject: newEmailSubject,
          message: newEmailBody,
        }),
      });

      // 認証エラーをチェック
      const authErrorHandled = await handleApiResponse(response);
      if (authErrorHandled) {
        setIsSendingNewEmail(false);
        return;
      }

      if (response.ok) {
        alert('メールが正常に送信されました！');
        
        // フォームをリセット
        setNewEmailTo('');
        setNewEmailSubject('');
        setNewEmailBody('');
        setIsComposingNew(false);
        
        // スレッド一覧を更新
        await loadThreads();
      } else {
        const errorData = await response.json();
        console.error('送信エラー:', errorData);
        alert(`メール送信に失敗しました: ${errorData.error || '不明なエラー'}`);
      }
    } catch (error) {
      console.error('メール送信エラー:', error);
      alert('メール送信中にエラーが発生しました');
    } finally {
      setIsSendingNewEmail(false);
    }
  };

  const handleSendReply = async () => {
    if (!replyText.trim() || !currentThread) return;

    setIsSending(true);
    try {
      const lastMessage = currentThread.messages[currentThread.messages.length - 1];
      const fromHeader = getHeader(lastMessage, 'from');
      const subjectHeader = getHeader(lastMessage, 'subject');
      
      // 添付ファイルがある場合はFormDataを使用
      if (attachmentFiles.length > 0) {
        const formData = new FormData();
        formData.append('to', fromHeader);
        formData.append('subject', subjectHeader.startsWith('Re:') ? subjectHeader : `Re: ${subjectHeader}`);
        formData.append('message', replyText);
        formData.append('threadId', currentThread.id);
        
        // 添付ファイルを追加
        attachmentFiles.forEach((file, index) => {
          formData.append(`attachment_${index}`, file);
        });
        
        const response = await fetch('/api/gmail/send-with-attachments', {
          method: 'POST',
          body: formData,
        });
        
        // 認証エラーをチェック
        const authErrorHandled = await handleApiResponse(response);
        if (authErrorHandled) {
          return;
        }
        
        if (response.ok) {
          setReplyText('');
          setAttachmentFiles([]);
          alert('メールを送信しました');
          await loadThreadDetails(currentThread.id);
        } else {
          alert('メール送信に失敗しました');
        }
      } else {
        // 添付ファイルなしの場合は既存のAPIを使用
        const response = await fetch('/api/gmail/send', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            to: fromHeader,
            subject: subjectHeader.startsWith('Re:') ? subjectHeader : `Re: ${subjectHeader}`,
            message: replyText,
            threadId: currentThread.id,
          }),
        });

        // 認証エラーをチェック
        const authErrorHandled = await handleApiResponse(response);
        if (authErrorHandled) {
          return;
        }

        if (response.ok) {
          setReplyText('');
          alert('メールを送信しました');
          await loadThreadDetails(currentThread.id);
        } else {
          alert('メール送信に失敗しました');
        }
      }
    } catch (error) {
      console.error('送信エラー:', error);
      alert('メール送信に失敗しました');
    } finally {
      setIsSending(false);
    }
  };

  const formatDate = (internalDate: string) => {
    const date = new Date(parseInt(internalDate));
    return date.toLocaleString('ja-JP');
  };

  const getHeader = (message: GmailMessage, headerName: string): string => {
    const header = message.payload.headers.find(
      h => h.name.toLowerCase() === headerName.toLowerCase()
    );
    return header?.value || '';
  };

  const decodeBase64 = (data: string): string => {
    try {
      return Buffer.from(data, 'base64').toString('utf-8');
    } catch (error) {
      return '';
    }
  };

  const getEmailBody = (message: GmailMessage): string => {
    const { payload } = message;
    
    // シンプルなテキスト/HTMLメッセージ
    if (payload.body?.data) {
      return decodeBase64(payload.body.data);
    }

    // マルチパートメッセージ
    if (payload.parts) {
      for (const part of payload.parts) {
        if (part.mimeType === 'text/html' || part.mimeType === 'text/plain') {
          if (part.body?.data) {
            return decodeBase64(part.body.data);
          }
        }
      }
    }

    return message.snippet;
  };

  const getInfluencerName = (message: GmailMessage) => {
    const fromHeader = getHeader(message, 'from');
    const emailMatch = fromHeader.match(/^(.+)<(.+)>$/);
    return emailMatch ? emailMatch[1].trim() : fromHeader;
  };

  const isFromUser = (message: GmailMessage) => {
    const fromHeader = getHeader(message, 'from');
    // 簡単なチェック - 実際のユーザーメールアドレスと比較する必要がある
    return fromHeader.includes('@company.com'); // 仮の判定
  };

  // スレッドから件名を取得
  const getThreadSubject = (thread: EmailThread): string => {
    if (thread.messages.length === 0) return 'タイトルなし';
    const firstMessage = thread.messages[0];
    const subject = getHeader(firstMessage, 'subject');
    return subject || 'タイトルなし';
  };

  // スレッドから主要な相手を取得（最後のメッセージの送信者）
  const getThreadPrimaryContact = (thread: EmailThread): string => {
    if (thread.messages.length === 0) return '不明';
    const latestMessage = thread.messages[thread.messages.length - 1];
    const fromHeader = getHeader(latestMessage, 'from');
    
    // メールアドレスから名前を抽出（"名前 <email@example.com>" 形式）
    const emailMatch = fromHeader.match(/^(.+?)\s*<(.+)>$/);
    if (emailMatch) {
      const name = emailMatch[1].trim().replace(/['"]/g, '');
      return name || emailMatch[2];
    }
    
    return fromHeader || '不明';
  };

  // スレッドの未読判定（簡易版）
  const isThreadUnread = (thread: EmailThread): boolean => {
    // 実装上の簡略化：すべて既読として扱う
    // 実際にはlabelIdsをチェックして 'UNREAD' があるかを確認
    return false;
  };

  // 認証が必要な場合
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin h-8 w-8 border-4 border-indigo-600 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-gray-600">読み込み中...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center">
        <div className="card p-8 text-center max-w-md mx-auto">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">ログインが必要です</h1>
          <p className="text-gray-600 mb-6">
            Gmail統合機能を使用するには、Googleアカウントでログインしてください。
          </p>
          <Link href="/auth/signin">
            <button className="btn btn-primary w-full">
              Googleでログイン
            </button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <AuthGuard>
      <ErrorBoundary>
        <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* ヘッダー */}
      <header className="bg-white/80 backdrop-blur-md shadow-sm border-b border-gray-200/50 sticky top-0 z-50">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <Link href="/" className="text-2xl font-bold text-gradient">
              InfuMatch
            </Link>
            <nav className="hidden md:flex space-x-8">
              <Link href="/search" className="text-gray-600 hover:text-indigo-600 transition-colors">
                検索
              </Link>
              <Link href="/messages" className="text-indigo-600 font-medium border-b-2 border-indigo-600 pb-1">
                メッセージ
              </Link>
              <Link href="/matching" className="text-gray-600 hover:text-indigo-600 transition-colors">
                AIマッチング
              </Link>
              <Link href="/settings" className="text-gray-600 hover:text-indigo-600 transition-colors">
                設定
              </Link>
            </nav>
            <div className="flex items-center space-x-4">
              <button 
                onClick={handleLogout}
                className="btn btn-primary"
              >
                ログアウト
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-6 py-8">
        <div className={`transform transition-all duration-1000 ${isVisible ? 'translate-y-0 opacity-100' : 'translate-y-10 opacity-0'}`}>
          {/* ヘッダーセクション */}
          <div className="text-center mb-12">
            <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
              Gmail統合
              <span className="text-gradient block">メッセージ管理</span>
            </h1>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              実際のGmailでインフルエンサーとやり取りし、AIが返信を提案します
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* 新規メール作成エリア */}
            {isComposingNew && (
              <div className="col-span-1 lg:col-span-3 mb-8">
                <div className="bg-gradient-to-r from-green-50 to-blue-50 rounded-xl p-6 border border-green-200">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-xl font-bold text-green-800 flex items-center gap-2">
                      ✉️ AI生成コラボ提案メール
                    </h3>
                    <button
                      onClick={() => {
                        setIsComposingNew(false);
                        setNewEmailTo('');
                        setNewEmailSubject('');
                        setNewEmailBody('');
                      }}
                      className="text-gray-500 hover:text-gray-700"
                    >
                      ✕
                    </button>
                  </div>
                  
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">宛先</label>
                      <input
                        type="email"
                        value={newEmailTo}
                        onChange={(e) => setNewEmailTo(e.target.value)}
                        className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-transparent"
                        placeholder="例: influencer@example.com"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">件名</label>
                      <input
                        type="text"
                        value={newEmailSubject}
                        onChange={(e) => setNewEmailSubject(e.target.value)}
                        className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-transparent"
                        placeholder="件名を入力..."
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">本文</label>
                      <textarea
                        value={newEmailBody}
                        onChange={(e) => setNewEmailBody(e.target.value)}
                        rows={12}
                        className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-transparent resize-none"
                        placeholder="メッセージを入力..."
                      />
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div className="text-sm text-green-700 bg-green-100 px-3 py-2 rounded-lg">
                        💡 このメッセージはAIがあなたの商材情報に基づいて生成しました
                      </div>
                      
                      <div className="flex items-center gap-3">
                        <button
                          onClick={() => {
                            setIsComposingNew(false);
                            setNewEmailTo('');
                            setNewEmailSubject('');
                            setNewEmailBody('');
                          }}
                          className="px-6 py-3 border border-gray-300 text-gray-700 rounded-xl font-medium hover:bg-gray-50 transition-colors"
                        >
                          キャンセル
                        </button>
                        <button
                          onClick={handleSendNewEmail}
                          disabled={!newEmailTo || !newEmailSubject || !newEmailBody || isSendingNewEmail}
                          className="bg-gradient-to-r from-green-600 to-blue-600 text-white px-6 py-3 rounded-xl font-medium hover:from-green-700 hover:to-blue-700 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                        >
                          {isSendingNewEmail ? (
                            <>
                              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                              送信中...
                            </>
                          ) : (
                            <>
                              📤 送信
                            </>
                          )}
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
            
            {/* 検索エリア */}
            {showSearch && (
              <div className="col-span-1 lg:col-span-3 mb-8">
                <EmailSearch 
                  onSearch={handleSearch}
                  onClear={handleClearSearch}
                  isLoading={isLoadingThreads}
                />
              </div>
            )}
            
            {/* 通知エリア */}
            {showNotifications && (
              <div className="col-span-1 lg:col-span-3 mb-8">
                <NotificationManager />
              </div>
            )}
            
            {/* スレッド一覧 */}
            <div className="lg:col-span-1">
              <div className="card">
                <div className="p-6 border-b border-gray-100">
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                      📧 メールスレッド
                      {newThreadsCount > 0 && (
                        <span className="bg-red-500 text-white text-xs px-2 py-1 rounded-full animate-pulse">
                          +{newThreadsCount}
                        </span>
                      )}
                    </h2>
                    <div className="flex items-center gap-2">
                      {lastUpdated && (
                        <span className="text-xs text-gray-500">
                          最終更新: {lastUpdated.toLocaleTimeString()}
                        </span>
                      )}
                      <div className={`w-2 h-2 rounded-full ${
                        isPolling ? 'bg-green-500 animate-pulse' : 'bg-gray-400'
                      }`} title={isPolling ? 'リアルタイム更新中' : '停止中'} />
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-3 mb-4">
                    <button
                      onClick={() => setShowSearch(!showSearch)}
                      className={`px-4 py-2 rounded-xl font-medium transition-all duration-200 flex items-center gap-2 ${
                        showSearch 
                          ? 'bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-lg' 
                          : 'bg-indigo-50 text-indigo-700 hover:bg-indigo-100 border border-indigo-200'
                      }`}
                    >
                      🔍 高度検索
                    </button>
                    <button
                      onClick={() => setShowNotifications(!showNotifications)}
                      className={`px-4 py-2 rounded-xl font-medium transition-all duration-200 flex items-center gap-2 ${
                        showNotifications 
                          ? 'bg-gradient-to-r from-orange-500 to-red-600 text-white shadow-lg' 
                          : 'bg-orange-50 text-orange-700 hover:bg-orange-100 border border-orange-200'
                      }`}
                    >
                      🔔 通知設定
                    </button>
                    <button
                      onClick={() => {
                        refreshRealtime();
                        resetNewCount();
                      }}
                      disabled={isRealtimeLoading}
                      className="btn btn-outline text-sm flex items-center gap-1"
                    >
                      {isRealtimeLoading ? '🔄' : '♾️'} 更新
                    </button>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <h2 className="text-lg font-bold text-gray-900">Gmail スレッド</h2>
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={loadThreads}
                        disabled={isLoading}
                        className="btn btn-ghost text-sm"
                      >
                        {isLoading ? (
                          <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                          </svg>
                        ) : (
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                          </svg>
                        )}
                        更新
                      </button>
                      <div className="flex items-center text-sm text-green-600">
                        <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                        Gmail接続済み
                      </div>
                    </div>
                  </div>
                </div>
                <div className="divide-y divide-gray-100 max-h-96 overflow-y-auto">
                  {threads.length === 0 ? (
                    <div className="p-6 text-center text-gray-500">
                      <p>メールスレッドが見つかりません</p>
                    </div>
                  ) : (
                    threads.map((thread, index) => (
                      <div
                        key={thread.id}
                        onClick={() => setSelectedThread(thread.id)}
                        className={`p-4 cursor-pointer hover:bg-gray-50 transition-all duration-200 ${
                          selectedThread === thread.id ? 'bg-indigo-50 border-r-4 border-indigo-500' : ''
                        }`}
                        style={{transitionDelay: `${index * 100}ms`}}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center space-x-2 mb-2">
                              <h3 className={`font-semibold truncate ${isThreadUnread(thread) ? 'text-gray-900' : 'text-gray-700'}`}>
                                {getThreadSubject(thread)}
                              </h3>
                              <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full">
                                {thread.messages.length}
                              </span>
                              {isThreadUnread(thread) && (
                                <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
                              )}
                            </div>
                            <div className="flex items-center space-x-2 mb-2">
                              <div className="w-6 h-6 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center text-white text-xs font-medium">
                                {getThreadPrimaryContact(thread)[0]?.toUpperCase() || '?'}
                              </div>
                              <p className="text-sm text-gray-600 font-medium truncate">
                                {getThreadPrimaryContact(thread)}
                              </p>
                            </div>
                            <p className="text-sm text-gray-500 line-clamp-2 mb-3">
                              {thread.snippet}
                            </p>
                            <div className="flex items-center justify-between">
                              <div className="flex items-center space-x-2">
                                <svg className="w-3 h-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                                <p className="text-xs text-gray-400">
                                  {thread.messages.length > 0 && formatDate(thread.messages[thread.messages.length - 1].internalDate)}
                                </p>
                              </div>
                              <div className="flex items-center space-x-1">
                                {thread.messages.length > 1 && (
                                  <svg className="w-3 h-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                                  </svg>
                                )}
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>

            {/* メール詳細 */}
            <div className="lg:col-span-2">
              {currentThread ? (
                <div className="card">
                  {/* ヘッダー */}
                  <div className="p-6 border-b border-gray-100">
                    <div className="flex items-center justify-between">
                      <div>
                        <h2 className="text-lg font-bold text-gray-900">
                          Gmail スレッド詳細
                        </h2>
                        <p className="text-sm text-gray-500 mt-1">
                          {currentThread.messages.length}件のメッセージ
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* メール一覧 */}
                  <div className="max-h-96 overflow-y-auto scrollbar-hide">
                    {currentThread.messages.map((message, index) => (
                      <div
                        key={message.id}
                        className="p-6 border-b border-gray-100 transition-all duration-300"
                        style={{transitionDelay: `${index * 150}ms`}}
                      >
                        <div className="flex items-start justify-between mb-4">
                          <div className="flex items-center space-x-3">
                            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-medium ${
                              isFromUser(message) ? 'bg-indigo-500' : 'bg-purple-500'
                            }`}>
                              {isFromUser(message) ? 'あ' : getInfluencerName(message)[0]}
                            </div>
                            <div>
                              <p className="text-sm font-semibold text-gray-900">
                                {isFromUser(message) ? 'あなた' : getInfluencerName(message)}
                              </p>
                              <p className="text-xs text-gray-500">{formatDate(message.internalDate)}</p>
                            </div>
                          </div>
                          <div className="text-xs text-gray-400">
                            {getHeader(message, 'subject')}
                          </div>
                        </div>
                        <div className="bg-gray-50 rounded-lg p-4">
                          <div 
                            className="text-gray-700 leading-relaxed"
                            dangerouslySetInnerHTML={{
                              __html: getEmailBody(message)
                            }}
                          />
                          
                          {/* 添付ファイル表示 */}
                          {message.attachments && message.attachments.length > 0 && (
                            <AttachmentDisplay 
                              attachments={message.attachments} 
                              messageId={message.id}
                            />
                          )}
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* 返信エリア */}
                  <div className="p-6 border-t border-gray-100 bg-gray-50/50">
                    <div className="mb-4">
                      <label className="block text-sm font-semibold text-gray-700 mb-3">
                        <svg className="w-4 h-4 inline mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                        </svg>
                        返信メッセージ
                      </label>
                      <textarea
                        value={replyText}
                        onChange={(e) => setReplyText(e.target.value)}
                        placeholder="返信メッセージを入力してください..."
                        className="input bg-white"
                        rows={4}
                      />
                    </div>
                    
                    {/* 添付ファイルアップロード */}
                    <div className="mb-4">
                      <AttachmentUpload 
                        onFilesChange={setAttachmentFiles}
                        maxFiles={5}
                        maxFileSize={25}
                      />
                    </div>
                    <div className="flex justify-between items-center">
                      <div className="flex items-center space-x-4">
                        <div className="flex items-center text-sm text-gray-500">
                          <svg className="w-4 h-4 mr-2 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                          </svg>
                          Gmail API接続済み
                        </div>
                      </div>
                      <div className="flex items-center space-x-3">
                        <button
                          onClick={handleSendReply}
                          disabled={isSending || !replyText.trim()}
                          className="btn btn-primary text-sm"
                        >
                          {isSending ? (
                            <>
                              <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                              </svg>
                              送信中...
                            </>
                          ) : (
                            <>
                              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                              </svg>
                              送信
                            </>
                          )}
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="card p-12 text-center">
                  <div className="max-w-md mx-auto">
                    <svg className="w-24 h-24 text-gray-300 mx-auto mb-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                    </svg>
                    <h3 className="text-xl font-semibold text-gray-900 mb-2">スレッドを選択</h3>
                    <p className="text-gray-500">
                      左側からGmailスレッドを選択してメッセージを表示してください
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* AI返信候補エリア */}
        {currentThread && (
          <div className="mt-12 card p-8">
            <div className="text-center mb-8">
              <div className="flex items-center justify-center mb-4">
                <div className="flex items-center justify-center w-12 h-12 bg-blue-100 rounded-full mr-4">
                  <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.847a4.5 4.5 0 003.09 3.09L15.75 12l-2.847.813a4.5 4.5 0 00-3.09 3.09z" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-2xl font-bold text-gray-900 mb-2">AI返信候補生成</h3>
                  <p className="text-gray-600">
                    田中美咲（交渉エージェント）がメールスレッドを分析し、最適な返信パターンを提案します
                  </p>
                </div>
              </div>
              
              {/* スレッド分析結果 */}
              {threadAnalysis && (
                <div className="bg-gray-50 rounded-lg p-4 mb-6">
                  <h4 className="font-semibold text-gray-800 mb-3">📊 スレッド分析結果</h4>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div className="text-center">
                      <div className="text-gray-500">関係性段階</div>
                      <div className="font-medium text-blue-600">
                        {threadAnalysis.relationship_stage === 'initial_contact' && '初回コンタクト'}
                        {threadAnalysis.relationship_stage === 'warming_up' && '関係構築期'}
                        {threadAnalysis.relationship_stage === 'price_negotiation' && '価格交渉期'}
                        {threadAnalysis.relationship_stage === 'relationship_building' && '関係深化期'}
                      </div>
                    </div>
                    <div className="text-center">
                      <div className="text-gray-500">感情トーン</div>
                      <div className="font-medium text-green-600">
                        {threadAnalysis.emotional_tone === 'positive' && '好意的'}
                        {threadAnalysis.emotional_tone === 'negative' && '慎重'}
                        {threadAnalysis.emotional_tone === 'neutral' && '中性的'}
                        {threadAnalysis.emotional_tone === 'urgent' && '緊急'}
                      </div>
                    </div>
                    <div className="text-center">
                      <div className="text-gray-500">緊急度</div>
                      <div className="font-medium text-orange-600">
                        {threadAnalysis.urgency_level === 'high' && '高'}
                        {threadAnalysis.urgency_level === 'medium' && '中'}
                        {threadAnalysis.urgency_level === 'normal' && '通常'}
                      </div>
                    </div>
                    <div className="text-center">
                      <div className="text-gray-500">主要トピック</div>
                      <div className="font-medium text-purple-600">
                        {threadAnalysis.main_topics?.join(', ') || 'なし'}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* 生成ボタン */}
              <div className="flex justify-center mb-6">
                <button
                  onClick={generateReplyPatterns}
                  disabled={isGeneratingPatterns}
                  className="btn btn-primary"
                >
                  {isGeneratingPatterns ? (
                    <>
                      <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      AI分析中...
                    </>
                  ) : (
                    <>
                      <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.847a4.5 4.5 0 003.09 3.09L15.75 12l-2.847.813a4.5 4.5 0 00-3.09 3.09z" />
                      </svg>
                      返信パターンを再生成
                    </>
                  )}
                </button>
              </div>
            </div>
            
            {/* AI生成返信パターン */}
            {isGeneratingPatterns ? (
              <div className="text-center py-12">
                <div className="animate-pulse">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {[1, 2, 3].map((i) => (
                      <div key={i} className="bg-gray-200 rounded-xl h-48"></div>
                    ))}
                  </div>
                </div>
                <p className="text-gray-500 mt-4">AIが返信パターンを生成しています...</p>
              </div>
            ) : replyPatterns.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {replyPatterns.map((pattern, index) => {
                  const getPatternColor = (type: string) => {
                    switch(type) {
                      case 'friendly_enthusiastic':
                        return 'border-green-200 hover:border-green-400 hover:bg-green-50';
                      case 'cautious_professional':
                        return 'border-blue-200 hover:border-blue-400 hover:bg-blue-50';
                      case 'business_focused':
                        return 'border-purple-200 hover:border-purple-400 hover:bg-purple-50';
                      default:
                        return 'border-gray-200 hover:border-gray-400 hover:bg-gray-50';
                    }
                  };

                  const getPatternIcon = (type: string) => {
                    switch(type) {
                      case 'friendly_enthusiastic':
                        return (
                          <svg className="w-6 h-6 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                        );
                      case 'cautious_professional':
                        return (
                          <svg className="w-6 h-6 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                          </svg>
                        );
                      case 'business_focused':
                        return (
                          <svg className="w-6 h-6 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                          </svg>
                        );
                      default:
                        return null;
                    }
                  };

                  return (
                    <div
                      key={index}
                      onClick={() => setReplyText(pattern.content)}
                      className={`p-6 border-2 rounded-xl cursor-pointer transition-all duration-300 group relative ${getPatternColor(pattern.pattern_type)}`}
                    >
                      {/* 推奨スコア */}
                      <div className="absolute top-3 right-3">
                        <div className="bg-white rounded-full px-2 py-1 text-xs font-medium text-gray-600 border">
                          推奨度: {Math.round((pattern.recommendation_score || 0.5) * 100)}%
                        </div>
                      </div>
                      
                      <div className="flex items-center mb-4">
                        {getPatternIcon(pattern.pattern_type)}
                        <h4 className="font-semibold text-gray-900 ml-3">{pattern.pattern_name}</h4>
                      </div>
                      
                      <div className="mb-4">
                        <span className="text-xs text-gray-500 uppercase tracking-wide">トーン</span>
                        <p className="text-sm font-medium text-gray-700">{pattern.tone}</p>
                      </div>
                      
                      <div className="bg-white rounded-lg p-3 mb-4 border">
                        <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
                          {pattern.content}
                        </p>
                      </div>
                      
                      <div className="mb-4">
                        <span className="text-xs text-gray-500 uppercase tracking-wide">使用場面</span>
                        <p className="text-xs text-gray-600 leading-relaxed">
                          {pattern.reasoning}
                        </p>
                      </div>
                      
                      <div className="flex items-center text-xs text-gray-400 group-hover:text-gray-600 transition-colors">
                        <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122" />
                        </svg>
                        クリックで返信欄に適用
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : currentThread ? (
              <div className="text-center py-12">
                <div className="max-w-md mx-auto">
                  <svg className="w-24 h-24 text-gray-300 mx-auto mb-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.847a4.5 4.5 0 003.09 3.09L15.75 12l-2.847.813a4.5 4.5 0 00-3.09 3.09z" />
                  </svg>
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">返信パターンを生成</h3>
                  <p className="text-gray-500 mb-4">
                    上のボタンをクリックしてAIに返信候補を生成させてください
                  </p>
                </div>
              </div>
            ) : null}
          </div>
        )}
      </main>
        </div>
      </ErrorBoundary>
    </AuthGuard>
  );
}