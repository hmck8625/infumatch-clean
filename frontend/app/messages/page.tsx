'use client';

import { useState, useEffect, Suspense } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { signOut } from 'next-auth/react';
import Header from '@/components/Header';
// import { EmailThread, GmailMessage } from '@/lib/gmail'; // Server-side only
// Temporary interfaces for client-side
interface EmailThread { id: string; snippet: string; historyId: string; messages?: GmailMessage[]; }
interface GmailMessage { 
  id: string; 
  threadId: string; 
  snippet: string; 
  internalDate: string;
  payload: {
    headers: { name: string; value: string; }[];
    body?: { data?: string; };
    parts?: { mimeType: string; body?: { data?: string; }; }[];
  };
  attachments?: any[];
}
import { ErrorBoundary, useErrorHandler } from '@/components/error-boundary';
import { AuthGuard, UserInfo } from '@/components/auth-guard';
import { useAuthError } from '@/hooks/use-auth-error';
import { AttachmentDisplay } from '@/components/attachment-display';
import { AttachmentUpload } from '@/components/attachment-upload';
import { EmailSearch } from '@/components/email-search';
import { NotificationManager } from '@/components/notification-manager';
import ThreadAutomationControl from '@/components/ThreadAutomationControl';
import AutomationOrchestrator from '@/components/AutomationOrchestrator';
// import { useRealtimeGmail } from '@/hooks/use-realtime-gmail'; // Temporarily disabled
// import { SearchFilters } from '@/lib/gmail'; // Server-side only
interface SearchFilters { query?: string; labelIds?: string[]; maxResults?: number; }

function MessagesPageContent() {
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
  const [detailedTrace, setDetailedTrace] = useState<any>(null);
  const [showDetailedTrace, setShowDetailedTrace] = useState(false);
  const [aiBasicReply, setAiBasicReply] = useState<string>('');
  const [aiReplyReasoning, setAiReplyReasoning] = useState<string>('');
  const [showReasoning, setShowReasoning] = useState<boolean>(false);
  
  // スレッドごとの自動化状態を管理
  const [threadAutomationStates, setThreadAutomationStates] = useState<{[threadId: string]: {mode: string, isActive: boolean}}>({});

  // 自動化状態をlocalStorageに永続化
  useEffect(() => {
    const savedAutomationStates = localStorage.getItem('threadAutomationStates');
    if (savedAutomationStates) {
      try {
        const parsed = JSON.parse(savedAutomationStates);
        setThreadAutomationStates(parsed);
        console.log('🔄 保存された自動化状態を復元:', {
          自動化中スレッド数: Object.keys(parsed).filter(id => parsed[id]?.isActive).length,
          自動化スレッドID: Object.keys(parsed).filter(id => parsed[id]?.isActive)
        });
      } catch (error) {
        console.error('❌ 自動化状態の復元に失敗:', error);
      }
    }
  }, []);

  // 自動化状態が変更されたときにlocalStorageに保存
  useEffect(() => {
    if (Object.keys(threadAutomationStates).length > 0) {
      localStorage.setItem('threadAutomationStates', JSON.stringify(threadAutomationStates));
      console.log('💾 自動化状態を保存:', {
        自動化中スレッド数: Object.keys(threadAutomationStates).filter(id => threadAutomationStates[id]?.isActive).length,
        自動化スレッドID: Object.keys(threadAutomationStates).filter(id => threadAutomationStates[id]?.isActive)
      });
    }
  }, [threadAutomationStates]);
  
  // Gmail監視状態
  const [gmailMonitoringActive, setGmailMonitoringActive] = useState(false);
  const [lastThreadCheck, setLastThreadCheck] = useState<string | null>(null);
  const [trackedThreads, setTrackedThreads] = useState<{[threadId: string]: {lastMessageTime: string, isAutomated: boolean}}>({});

  // 追跡状態をlocalStorageに永続化
  useEffect(() => {
    const savedTrackedThreads = localStorage.getItem('trackedThreads');
    if (savedTrackedThreads) {
      try {
        const parsed = JSON.parse(savedTrackedThreads);
        setTrackedThreads(parsed);
        console.log('🔄 保存された追跡状態を復元:', {
          追跡中スレッド数: Object.keys(parsed).length,
          スレッドID: Object.keys(parsed)
        });
      } catch (error) {
        console.error('❌ 追跡状態の復元に失敗:', error);
      }
    }
  }, []);

  // 追跡状態が変更されたときにlocalStorageに保存
  useEffect(() => {
    if (Object.keys(trackedThreads).length > 0) {
      localStorage.setItem('trackedThreads', JSON.stringify(trackedThreads));
      console.log('💾 追跡状態を保存:', {
        追跡中スレッド数: Object.keys(trackedThreads).length,
        スレッドID: Object.keys(trackedThreads)
      });
    }
  }, [trackedThreads]);
  
  // Gmail監視状態変更のラッパー関数（ログ付き）
  const handleMonitoringChange = (isActive: boolean) => {
    console.log('📋 Gmail監視状態変更要求:', {
      現在の状態: gmailMonitoringActive,
      新しい状態: isActive,
      時刻: new Date().toLocaleTimeString()
    });
    setGmailMonitoringActive(isActive);
    console.log('✅ Gmail監視状態更新完了:', isActive);
  };
  
  // Gmail新着監視機能
  const checkForNewEmails = async () => {
    if (!gmailMonitoringActive) {
      console.log('⏸️ Gmail監視は無効です。スキップします。');
      return;
    }
    
    try {
      console.log('📧 Gmail新着チェック開始', {
        時刻: new Date().toLocaleTimeString(),
        監視状態: gmailMonitoringActive,
        前回チェックしたスレッドID: lastThreadCheck,
        追跡中スレッド数: Object.keys(trackedThreads).length
      });
      
      // Gmail APIで最新のスレッドを取得
      console.log('🌐 Gmail API呼び出し: /api/gmail/threads?maxResults=20');
      const response = await fetch('/api/gmail/threads?maxResults=20');
      
      console.log('📡 Gmail APIレスポンス:', {
        status: response.status,
        ok: response.ok,
        statusText: response.statusText
      });
      
      if (!response.ok) {
        console.error('❌ Gmail API呼び出し失敗:', {
          status: response.status,
          statusText: response.statusText
        });
        return;
      }
      
      const data = await response.json();
      const newThreads = data.threads || [];
      
      console.log('📬 取得したスレッド情報:', {
        総スレッド数: newThreads.length,
        最新スレッドID: newThreads.length > 0 ? newThreads[0].id : 'なし',
        全スレッドID: newThreads.map(t => t.id).slice(0, 3) // 最初の3つのIDのみ表示
      });
      
      if (newThreads.length > 0) {
        const latestThreadId = newThreads[0].id;
        const latestThreadSnippet = newThreads[0].snippet || '';
        
        console.log('🔍 最新スレッド詳細:', {
          ID: latestThreadId,
          snippet: latestThreadSnippet.substring(0, 100) + '...',
          前回のチェック: lastThreadCheck
        });
        
        // 新着スレッドが検出された場合
        if (lastThreadCheck && latestThreadId !== lastThreadCheck) {
          console.log('🆕🚨 新着スレッド検出！', {
            新着スレッドID: latestThreadId,
            前回スレッドID: lastThreadCheck,
            スニペット: latestThreadSnippet.substring(0, 150)
          });
          
          // スレッドリストを即座に更新
          console.log('🔄 スレッドリストを更新中...');
          await loadThreads();
          console.log('✅ スレッドリスト更新完了');
          
          // 新着スレッドに対して自動交渉を実行
          await processNewThread(latestThreadId);
        } else if (!lastThreadCheck) {
          console.log('🔄 初回チェック - 基準スレッドIDを設定');
        } else {
          console.log('📭 新しいスレッドなし - 既存スレッドの更新をチェック');
        }
        
        // 既存スレッドの更新検出（新機能）
        await checkExistingThreadsForUpdates(newThreads);
        
        setLastThreadCheck(latestThreadId);
      } else {
        console.log('📪 スレッドが見つかりませんでした');
      }
      
      console.log('✅ Gmail新着チェック完了', new Date().toLocaleTimeString());
      
    } catch (error) {
      console.error('❌ Gmail監視エラー:', {
        error: error,
        message: error.message,
        stack: error.stack
      });
    }
  };

  // 既存スレッドの更新をチェックする新機能
  const checkExistingThreadsForUpdates = async (currentThreads: any[]) => {
    const automatedThreadIds = Object.keys(threadAutomationStates).filter(
      threadId => threadAutomationStates[threadId]?.isActive && threadAutomationStates[threadId]?.mode === 'semi_auto'
    );
    
    if (automatedThreadIds.length === 0) {
      console.log('🤖 半自動実行中のスレッドなし');
      return;
    }
    
    console.log('🤖 半自動実行中スレッドをチェック:', {
      対象スレッド数: automatedThreadIds.length,
      スレッドID: automatedThreadIds
    });
    
    for (const threadId of automatedThreadIds) {
      try {
        // スレッド詳細を取得して最新メッセージをチェック
        console.log(`🔍 スレッド ${threadId} の詳細を取得中...`);
        const threadResponse = await fetch(`/api/gmail/threads/${threadId}`);
        
        if (!threadResponse.ok) {
          console.warn(`⚠️ スレッド ${threadId} の取得に失敗:`, threadResponse.status);
          continue;
        }
        
        const threadData = await threadResponse.json();
        // APIレスポンス構造をチェック
        console.log(`📊 スレッド ${threadId} のAPIレスポンス構造:`, {
          hasThread: !!threadData.thread,
          hasMessages: !!threadData.messages,
          threadKeysCount: threadData.thread ? Object.keys(threadData.thread).length : 0,
          directKeysCount: Object.keys(threadData).length,
          sampleKeys: Object.keys(threadData).slice(0, 5)
        });
        
        // レスポンス構造に応じてメッセージを取得
        const actualThreadData = threadData.thread || threadData;
        const messages = actualThreadData.messages || [];
        
        if (messages.length === 0) {
          console.warn(`⚠️ スレッド ${threadId} にメッセージなし`);
          continue;
        }
        
        // 最新メッセージの時刻を取得
        const latestMessage = messages[messages.length - 1];
        const latestMessageTime = latestMessage.internalDate;
        
        console.log(`📅 スレッド ${threadId} の最新メッセージ時刻:`, {
          現在の時刻: latestMessageTime,
          前回の時刻: trackedThreads[threadId]?.lastMessageTime,
          メッセージ数: messages.length
        });
        
        // 前回チェック時より新しいメッセージがあるかチェック
        const previousMessageTime = trackedThreads[threadId]?.lastMessageTime;
        
        if (previousMessageTime && latestMessageTime !== previousMessageTime) {
          console.log('🚨💬 既存スレッドに新着メッセージ検出!', {
            スレッドID: threadId,
            前回メッセージ時刻: previousMessageTime,
            新着メッセージ時刻: latestMessageTime,
            メッセージ内容: latestMessage.snippet?.substring(0, 100) + '...'
          });
          
          // スレッドリストを更新
          console.log('🔄 スレッドリスト更新中...');
          await loadThreads();
          console.log('✅ スレッドリスト更新完了');
          
          // 既存スレッドの返信に対して自動交渉を実行
          await processExistingThreadReply(threadId);
        } else if (!previousMessageTime) {
          console.log(`🔄 スレッド ${threadId} の初回追跡開始`);
        } else {
          console.log(`📭 スレッド ${threadId} に新着メッセージなし`);
        }
        
        // 追跡情報を更新
        setTrackedThreads(prev => ({
          ...prev,
          [threadId]: {
            lastMessageTime: latestMessageTime,
            isAutomated: true
          }
        }));
        
      } catch (error) {
        console.error(`❌ スレッド ${threadId} のチェック中にエラー:`, error);
      }
    }
  };
  
  // 新着スレッドを処理
  const processNewThread = async (threadId: string) => {
    try {
      console.log('🤖 新着スレッドの自動交渉開始:', {
        スレッドID: threadId,
        開始時刻: new Date().toLocaleTimeString()
      });
      
      // スレッドの詳細を取得
      console.log('📨 スレッド詳細取得中:', threadId);
      const threadResponse = await fetch(`/api/gmail/threads/${threadId}`);
      
      console.log('📡 スレッド詳細API応答:', {
        status: threadResponse.status,
        ok: threadResponse.ok,
        statusText: threadResponse.statusText
      });
      
      if (!threadResponse.ok) {
        console.error('❌ スレッド詳細取得失敗:', threadResponse.status);
        return;
      }
      
      const threadData = await threadResponse.json();
      const messages = threadData.messages || [];
      
      console.log('📧 取得したメッセージ情報:', {
        メッセージ数: messages.length,
        スレッドID: threadId
      });
      
      if (messages.length === 0) {
        console.warn('⚠️ メッセージが見つかりません');
        return;
      }
      
      // 最新メッセージを取得
      const latestMessage = messages[messages.length - 1];
      const messageContent = extractMessageContent(latestMessage);
      const fromHeader = latestMessage.payload?.headers?.find(h => h.name === 'From')?.value || '';
      const subjectHeader = latestMessage.payload?.headers?.find(h => h.name === 'Subject')?.value || '';
      
      // Reply-ToヘッダーとToヘッダーもチェック
      const replyToHeader = latestMessage.payload?.headers?.find(h => h.name === 'Reply-To')?.value || '';
      const toHeader = latestMessage.payload?.headers?.find(h => h.name === 'To')?.value || '';
      
      // 自分宛メールかどうかをチェックして無限ループを防ぐ
      const isFromSelf = fromHeader.includes('@gmail.com') && (
        fromHeader.includes('infumatch') || 
        fromHeader.includes('自分のメールドメイン') // 実際のドメインに置き換え
      );
      
      // 自動送信メールの可能性をチェック
      const isAutoGenerated = fromHeader.includes('noreply') || 
                              fromHeader.includes('no-reply') ||
                              fromHeader.includes('mailer-daemon') ||
                              subjectHeader.includes('Delivery Status Notification') ||
                              subjectHeader.includes('Undelivered Mail');
      
      if (isFromSelf) {
        console.log('⚠️ 自分からのメールのため自動返信をスキップ:', fromHeader);
        return;
      }
      
      if (isAutoGenerated) {
        console.log('⚠️ 自動送信メールのため自動返信をスキップ:', fromHeader);
        return;
      }
      
      // 返信先を決定（Reply-To優先、なければFrom）
      const replyToAddress = replyToHeader || fromHeader;
      
      console.log('📧 返信先決定:', {
        From: fromHeader,
        ReplyTo: replyToHeader,
        To: toHeader,
        決定された返信先: replyToAddress
      });
      
      console.log('📬 最新メッセージ詳細:', {
        送信者: fromHeader,
        件名: subjectHeader,
        内容プレビュー: messageContent.substring(0, 100) + '...',
        メッセージID: latestMessage.id
      });
      
      // 自動交渉APIを呼び出し
      console.log('🚀 自動交渉API呼び出し開始');
      const negotiationPayload = {
        conversation_history: messages,
        new_message: messageContent,
        context: {
          auto_reply: true,
          thread_id: threadId,
          sender: fromHeader,
          subject: subjectHeader
        }
      };
      
      console.log('📤 自動交渉APIペイロード:', {
        会話履歴数: messages.length,
        新着メッセージ文字数: messageContent.length,
        コンテキスト: negotiationPayload.context
      });
      
      const negotiationResponse = await fetch('/api/v1/negotiation/continue', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(negotiationPayload)
      });
      
      console.log('📡 自動交渉API応答:', {
        status: negotiationResponse.status,
        ok: negotiationResponse.ok,
        statusText: negotiationResponse.statusText
      });
      
      if (negotiationResponse.ok) {
        const result = await negotiationResponse.json();
        console.log('✅ 自動交渉完了:', {
          成功: result.success,
          生成された返信: result.content ? result.content.substring(0, 100) + '...' : 'なし',
          処理時間: new Date().toLocaleTimeString()
        });
        
        // 返信が必要で、かつ生成されたコンテンツがある場合のみ自動送信
        if (result.success && result.content && !result.metadata?.reply_not_needed && !result.metadata?.caution_required) {
          console.log('📤 自動返信送信開始:', {
            スレッドID: threadId,
            返信内容文字数: result.content.length,
            送信対象: replyToAddress
          });
          
          try {
            // 1. 返信ヘッダーを取得
            console.log('📋 返信ヘッダー取得中...');
            const replyHeadersResponse = await fetch(`/api/gmail/threads/${threadId}/reply-headers?messageId=${latestMessage.id}`);
            
            let replyHeaders = null;
            if (replyHeadersResponse.ok) {
              const headerData = await replyHeadersResponse.json();
              replyHeaders = headerData.replyHeaders;
              console.log('✅ 返信ヘッダー取得成功:', replyHeaders);
            } else {
              console.warn('⚠️ 返信ヘッダー取得失敗、基本情報で送信します');
            }
            
            // 2. 返信メールを送信
            console.log('📨 Gmail送信API呼び出し中...');
            const sendPayload = {
              to: replyToAddress,
              subject: subjectHeader.startsWith('Re: ') ? subjectHeader : `Re: ${subjectHeader}`,
              body: result.content,
              threadId: threadId,
              replyToMessageId: latestMessage.id,
              replyHeaders: replyHeaders
            };
            
            console.log('📤 送信ペイロード:', {
              宛先: sendPayload.to,
              件名: sendPayload.subject,
              本文文字数: sendPayload.body.length,
              スレッドID: sendPayload.threadId,
              返信先メッセージID: sendPayload.replyToMessageId,
              ヘッダー有無: !!sendPayload.replyHeaders
            });
            
            const sendResponse = await fetch('/api/gmail/send', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(sendPayload)
            });
            
            if (sendResponse.ok) {
              const sendResult = await sendResponse.json();
              console.log('✅ 自動返信送信成功!', {
                メッセージID: sendResult.messageId,
                送信完了時刻: new Date().toLocaleTimeString(),
                宛先: sendPayload.to,
                件名: sendPayload.subject
              });
            } else {
              const sendError = await sendResponse.text();
              console.error('❌ 自動返信送信失敗:', {
                status: sendResponse.status,
                error: sendError,
                payload: sendPayload
              });
            }
            
          } catch (sendError) {
            console.error('❌ 自動返信送信中のエラー:', {
              error: sendError,
              message: sendError instanceof Error ? sendError.message : 'Unknown error',
              スレッドID: threadId
            });
          }
        } else {
          console.log('ℹ️ 自動返信スキップ:', {
            success: result.success,
            hasContent: !!result.content,
            replyNotNeeded: result.metadata?.reply_not_needed,
            cautionRequired: result.metadata?.caution_required,
            理由: result.metadata?.reply_not_needed ? '返信不要メール' : 
                  result.metadata?.caution_required ? '注意が必要なメール' : 
                  !result.content ? 'コンテンツ生成失敗' : 'その他'
          });
        }
        
        // スレッドリストを更新
        console.log('🔄 自動交渉後のスレッドリスト更新中...');
        await loadThreads();
        console.log('✅ 自動交渉後のスレッドリスト更新完了');
      } else {
        const errorText = await negotiationResponse.text();
        console.error('❌ 自動交渉API失敗:', {
          status: negotiationResponse.status,
          error: errorText
        });
      }
      
    } catch (error) {
      console.error('❌ 新着スレッド処理エラー:', {
        error: error,
        message: error.message,
        stack: error.stack,
        スレッドID: threadId
      });
    }
  };

  // 既存スレッドの返信を処理
  const processExistingThreadReply = async (threadId: string) => {
    try {
      console.log('🔄 既存スレッドの返信自動交渉開始:', {
        スレッドID: threadId,
        開始時刻: new Date().toLocaleTimeString()
      });
      
      // スレッドの詳細を取得
      console.log('📨 スレッド詳細取得中:', threadId);
      const threadResponse = await fetch(`/api/gmail/threads/${threadId}`);
      
      console.log('📡 スレッド詳細API応答:', {
        status: threadResponse.status,
        ok: threadResponse.ok,
        statusText: threadResponse.statusText
      });
      
      if (!threadResponse.ok) {
        console.error('❌ スレッド詳細取得失敗:', threadResponse.status);
        return;
      }
      
      const threadData = await threadResponse.json();
      
      // APIレスポンス構造の完全な詳細調査
      console.log(`📊 既存スレッド ${threadId} のAPIレスポンス完全構造:`, {
        hasThread: !!threadData.thread,
        hasMessages: !!threadData.messages,
        threadKeysCount: threadData.thread ? Object.keys(threadData.thread).length : 0,
        directKeysCount: Object.keys(threadData).length,
        allKeys: Object.keys(threadData),
        threadObject: threadData.thread ? {
          threadKeys: Object.keys(threadData.thread),
          id: threadData.thread.id,
          hasMessages: !!threadData.thread.messages,
          messagesLength: threadData.thread.messages ? threadData.thread.messages.length : 0,
          historyId: threadData.thread.historyId,
          snippet: threadData.thread.snippet
        } : null,
        fullStructureSample: JSON.stringify(threadData, null, 2).substring(0, 1000) + '...'
      });
      
      // レスポンス構造に応じてメッセージを取得
      const actualThreadData = threadData.thread || threadData;
      const messages = actualThreadData.messages || [];
      
      console.log('📧 取得したメッセージ情報:', {
        メッセージ数: messages.length,
        スレッドID: threadId,
        使用したデータソース: threadData.thread ? 'threadData.thread' : 'threadData直接'
      });
      
      // メッセージが空の場合の詳細分析
      if (messages.length === 0) {
        console.error(`🔍 メッセージ取得失敗の詳細分析 - スレッド ${threadId}:`, {
          threadDataExists: !!threadData.thread,
          threadDataKeys: threadData.thread ? Object.keys(threadData.thread) : [],
          messagesProperty: actualThreadData.messages,
          messagesType: typeof actualThreadData.messages,
          actualThreadDataKeys: Object.keys(actualThreadData),
          fullThreadData: threadData.thread || threadData
        });
        console.warn('⚠️ メッセージが見つかりません - 処理を中止');
        return;
      }
      
      // 最新メッセージを取得
      const latestMessage = messages[messages.length - 1];
      const messageContent = extractMessageContent(latestMessage);
      const fromHeader = latestMessage.payload?.headers?.find(h => h.name === 'From')?.value || '';
      const subjectHeader = latestMessage.payload?.headers?.find(h => h.name === 'Subject')?.value || '';
      
      // Reply-ToヘッダーとToヘッダーもチェック
      const replyToHeader = latestMessage.payload?.headers?.find(h => h.name === 'Reply-To')?.value || '';
      const toHeader = latestMessage.payload?.headers?.find(h => h.name === 'To')?.value || '';
      
      // 自分宛メールかどうかをチェックして無限ループを防ぐ
      const isFromSelf = fromHeader.includes('@gmail.com') && (
        fromHeader.includes('infumatch') || 
        fromHeader.includes('自分のメールドメイン') // 実際のドメインに置き換え
      );
      
      // 自動送信メールの可能性をチェック
      const isAutoGenerated = fromHeader.includes('noreply') || 
                              fromHeader.includes('no-reply') ||
                              fromHeader.includes('mailer-daemon') ||
                              subjectHeader.includes('Delivery Status Notification') ||
                              subjectHeader.includes('Undelivered Mail');
      
      if (isFromSelf) {
        console.log('⚠️ 自分からのメールのため自動返信をスキップ:', fromHeader);
        return;
      }
      
      if (isAutoGenerated) {
        console.log('⚠️ 自動送信メールのため自動返信をスキップ:', fromHeader);
        return;
      }
      
      // 返信先を決定（Reply-To優先、なければFrom）
      const replyToAddress = replyToHeader || fromHeader;
      
      console.log('📧 返信先決定:', {
        From: fromHeader,
        ReplyTo: replyToHeader,
        To: toHeader,
        決定された返信先: replyToAddress
      });
      
      console.log('📬 最新メッセージ詳細:', {
        送信者: fromHeader,
        件名: subjectHeader,
        内容プレビュー: messageContent.substring(0, 100) + '...',
        メッセージID: latestMessage.id
      });
      
      // 自動交渉APIを呼び出し
      console.log('🚀 自動交渉API呼び出し開始（既存スレッド返信）');
      const negotiationPayload = {
        conversation_history: messages,
        new_message: messageContent,
        context: {
          auto_reply: true,
          thread_id: threadId,
          sender: fromHeader,
          subject: subjectHeader,
          is_existing_thread_reply: true  // 既存スレッドの返信であることを示すフラグ
        }
      };
      
      console.log('📤 自動交渉APIペイロード:', {
        会話履歴数: messages.length,
        新着メッセージ文字数: messageContent.length,
        コンテキスト: negotiationPayload.context
      });
      
      const negotiationResponse = await fetch('/api/v1/negotiation/continue', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(negotiationPayload)
      });
      
      console.log('📡 自動交渉API応答:', {
        status: negotiationResponse.status,
        ok: negotiationResponse.ok,
        statusText: negotiationResponse.statusText
      });
      
      if (negotiationResponse.ok) {
        const result = await negotiationResponse.json();
        console.log('✅ 自動交渉完了（既存スレッド）:', {
          成功: result.success,
          生成された返信: result.content ? result.content.substring(0, 100) + '...' : 'なし',
          処理時間: new Date().toLocaleTimeString()
        });
        
        // 返信が必要で、かつ生成されたコンテンツがある場合のみ自動送信
        if (result.success && result.content && !result.metadata?.reply_not_needed && !result.metadata?.caution_required) {
          console.log('📤 既存スレッド自動返信送信開始:', {
            スレッドID: threadId,
            返信内容文字数: result.content.length,
            送信対象: fromHeader
          });
          
          try {
            // 1. 返信ヘッダーを取得
            console.log('📋 返信ヘッダー取得中...');
            const replyHeadersResponse = await fetch(`/api/gmail/threads/${threadId}/reply-headers?messageId=${latestMessage.id}`);
            
            let replyHeaders = null;
            if (replyHeadersResponse.ok) {
              const headerData = await replyHeadersResponse.json();
              replyHeaders = headerData.replyHeaders;
              console.log('✅ 返信ヘッダー取得成功:', replyHeaders);
            } else {
              console.warn('⚠️ 返信ヘッダー取得失敗、基本情報で送信します');
            }
            
            // 2. 返信メールを送信
            console.log('📨 Gmail送信API呼び出し中...');
            const sendPayload = {
              to: replyToAddress,
              subject: subjectHeader.startsWith('Re: ') ? subjectHeader : `Re: ${subjectHeader}`,
              body: result.content,
              threadId: threadId,
              replyToMessageId: latestMessage.id,
              replyHeaders: replyHeaders
            };
            
            console.log('📤 送信ペイロード:', {
              宛先: sendPayload.to,
              件名: sendPayload.subject,
              本文文字数: sendPayload.body.length,
              スレッドID: sendPayload.threadId,
              返信先メッセージID: sendPayload.replyToMessageId,
              ヘッダー有無: !!sendPayload.replyHeaders
            });
            
            const sendResponse = await fetch('/api/gmail/send', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(sendPayload)
            });
            
            if (sendResponse.ok) {
              const sendResult = await sendResponse.json();
              console.log('✅ 既存スレッド自動返信送信成功!', {
                メッセージID: sendResult.messageId,
                送信完了時刻: new Date().toLocaleTimeString(),
                宛先: sendPayload.to,
                件名: sendPayload.subject
              });
            } else {
              const sendError = await sendResponse.text();
              console.error('❌ 既存スレッド自動返信送信失敗:', {
                status: sendResponse.status,
                error: sendError,
                payload: sendPayload
              });
            }
            
          } catch (sendError) {
            console.error('❌ 既存スレッド自動返信送信中のエラー:', {
              error: sendError,
              message: sendError instanceof Error ? sendError.message : 'Unknown error',
              スレッドID: threadId
            });
          }
        } else {
          console.log('ℹ️ 既存スレッド自動返信スキップ:', {
            success: result.success,
            hasContent: !!result.content,
            replyNotNeeded: result.metadata?.reply_not_needed,
            cautionRequired: result.metadata?.caution_required,
            理由: result.metadata?.reply_not_needed ? '返信不要メール' : 
                  result.metadata?.caution_required ? '注意が必要なメール' : 
                  !result.content ? 'コンテンツ生成失敗' : 'その他'
          });
        }
        
        // スレッドリストを更新
        console.log('🔄 既存スレッド自動交渉後のスレッドリスト更新中...');
        await loadThreads();
        console.log('✅ 既存スレッド自動交渉後のスレッドリスト更新完了');
      } else {
        const errorText = await negotiationResponse.text();
        console.error('❌ 既存スレッド自動交渉API失敗:', {
          status: negotiationResponse.status,
          error: errorText
        });
      }
      
    } catch (error) {
      console.error('❌ 既存スレッド返信処理エラー:', {
        error: error,
        message: error instanceof Error ? error.message : 'Unknown error',
        stack: error instanceof Error ? error.stack : 'No stack',
        スレッドID: threadId
      });
    }
  };
  
  // メッセージ内容を抽出するヘルパー関数
  const extractMessageContent = (message: any) => {
    // Gmail APIのメッセージ構造から本文を抽出
    const payload = message.payload || {};
    
    const decodeBase64Utf8 = (data: string) => {
      try {
        // Gmail APIのbase64url形式を標準のbase64に変換
        const base64 = data.replace(/-/g, '+').replace(/_/g, '/');
        // UTF-8として正しくデコード
        const decoded = atob(base64);
        return decodeURIComponent(escape(decoded));
      } catch (error) {
        console.warn('Base64デコードエラー:', error);
        // フォールバックとして通常のatobを使用
        return atob(data.replace(/-/g, '+').replace(/_/g, '/'));
      }
    };
    
    if (payload.body?.data) {
      return decodeBase64Utf8(payload.body.data);
    }
    if (payload.parts) {
      for (const part of payload.parts) {
        if (part.mimeType === 'text/plain' && part.body?.data) {
          return decodeBase64Utf8(part.body.data);
        }
      }
    }
    return message.snippet || '';
  };
  
  // エージェント状況とカスタムプロンプト
  interface ProcessingStep {
    time: string;
    status: string;
    detail: string;
    reasoning?: string; // AIの思考過程
    stepNumber: number; // 1-4の段階番号
    progressPercent: number; // 進捗率 (0-100)
    agentType?: string; // 処理中のエージェントタイプ
    duration?: number; // 処理時間（ミリ秒）
    confidence?: number; // 信頼度 (0-1)
    isCompleted: boolean; // 完了フラグ
  }

  // 5段階のシンプルステップ定義
  const PROCESSING_STAGES = [
    { 
      number: 1, 
      name: '📊 スレッド分析', 
      description: 'メッセージ履歴を分析し、現在の交渉状況を把握しています',
      progressTarget: 20
    },
    { 
      number: 2, 
      name: '🧠 戦略立案', 
      description: 'カスタム指示と企業設定を考慮して返信戦略を立案しています',
      progressTarget: 40
    },
    { 
      number: 3, 
      name: '🔍 内容評価', 
      description: '戦略内容の適切性を評価し、リスク要因をチェックしています',
      progressTarget: 60
    },
    { 
      number: 4, 
      name: '🎨 パターン生成', 
      description: '3つの異なるアプローチで返信パターンを生成しています',
      progressTarget: 80
    },
    { 
      number: 5, 
      name: '💌 基本返信＆理由生成', 
      description: 'AI基本返信と選択理由をGeminiで生成しています',
      progressTarget: 100
    }
  ];
  
  const [agentStatus, setAgentStatus] = useState<string>('待機中');
  const [processingSteps, setProcessingSteps] = useState<ProcessingStep[]>([]);
  const [customPrompt, setCustomPrompt] = useState<string>('');
  const [showCustomPrompt, setShowCustomPrompt] = useState(false);
  
  // 新規メール作成用の状態
  const [isComposingNew, setIsComposingNew] = useState(false);
  const [newEmailTo, setNewEmailTo] = useState('');
  const [newEmailSubject, setNewEmailSubject] = useState('');
  const [newEmailBody, setNewEmailBody] = useState('');
  const [isSendingNewEmail, setIsSendingNewEmail] = useState(false);
  
  // リアルタイムGmail機能 (temporarily disabled)
  // const {
  //   threads: realtimeThreads,
  //   isLoading: isRealtimeLoading,
  //   lastUpdated,
  //   newThreadsCount,
  //   refresh: refreshRealtime,
  //   resetNewCount,
  //   isPolling,
  //   startPolling,
  //   stopPolling,
  // } = useRealtimeGmail(threads, {
  //   pollInterval: 30000, // 30秒間隔
  //   enableNotifications: true,
  //   autoRefresh: true,
  // });

  // Mock values for disabled functionality
  const realtimeThreads = threads;
  const isRealtimeLoading = false;
  const lastUpdated = new Date();
  const newThreadsCount = 0;
  const refreshRealtime = () => {};
  const resetNewCount = () => {};
  const isPolling = false;
  const startPolling = () => {};
  const stopPolling = () => {};

  // Gmail監視の定期実行
  useEffect(() => {
    let intervalId: NodeJS.Timeout;
    
    console.log('📋 Gmail監視useEffect実行:', {
      監視状態: gmailMonitoringActive,
      前回チェックスレッド: lastThreadCheck,
      現在時刻: new Date().toLocaleTimeString()
    });
    
    if (gmailMonitoringActive) {
      console.log('🔄 Gmail監視を開始します', {
        間隔: '60秒',
        現在時刻: new Date().toLocaleTimeString(),
        初回実行: 'あり'
      });
      
      // 定期実行を設定
      intervalId = setInterval(() => {
        console.log('⏰ Gmail監視タイマー発火 - checkForNewEmails()を実行');
        checkForNewEmails();
      }, 60000); // 60秒間隔
      
      // 初回実行
      console.log('🚀 Gmail監視初回チェック実行');
      checkForNewEmails();
    } else {
      console.log('⏸️ Gmail監視は無効 - 定期チェックはスキップされます');
    }
    
    return () => {
      if (intervalId) {
        clearInterval(intervalId);
        console.log('⏹️ Gmail監視定期チェックを停止しました', {
          停止時刻: new Date().toLocaleTimeString()
        });
      }
    };
  }, [gmailMonitoringActive, lastThreadCheck]);

  useEffect(() => {
    setIsVisible(true);
    checkAuth();
    
    // 初期状態をログ出力
    console.log('📋 メッセージページ初期化:', {
      Gmail監視状態: gmailMonitoringActive,
      認証状態: isAuthenticated,
      時刻: new Date().toLocaleTimeString()
    });

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

  // 自動生成は削除 - 手動でのみAI返信候補を生成するように変更
  // useEffect(() => {
  //   if (currentThread && currentThread.messages && currentThread.messages.length > 0) {
  //     generateReplyPatterns();
  //   }
  // }, [currentThread]);

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
        console.log('Number of threads:', data.threads?.length || 0);
        
        const newThreads = data.threads || [];
        console.log('Setting threads state to:', newThreads);
        setThreads(newThreads);
        
        console.log('✅ Threads state updated successfully');
      } else {
        const errorText = await response.text();
        console.warn('Failed to load threads:', response.status, response.statusText, errorText);
      }
    } catch (error) {
      handleError(error);
      console.error('スレッド読み込みエラー:', error);
    } finally {
      console.log('📧 loadThreads completed, setting loading to false');
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

  // 処理開始時刻を記録
  const [processingStartTime, setProcessingStartTime] = useState<number>(0);
  const [currentStageIndex, setCurrentStageIndex] = useState<number>(0);

  const updateAgentStatus = (
    status: string, 
    detail?: string, 
    reasoning?: string, 
    stepNumber?: number,
    agentType?: string,
    confidence?: number
  ) => {
    setAgentStatus(status);
    
    if (detail) {
      const now = Date.now();
      const duration = processingStartTime > 0 ? now - processingStartTime : 0;
      
      // ステップ番号が指定されていない場合は自動判定
      const actualStepNumber = stepNumber || (currentStageIndex + 1);
      const stage = PROCESSING_STAGES.find(s => s.number === actualStepNumber);
      const progressPercent = stage?.progressTarget || Math.min((actualStepNumber / 4) * 100, 100);
      
      setProcessingSteps(prev => [...prev, {
        time: new Date().toLocaleTimeString(),
        status: status,
        detail: detail,
        reasoning: reasoning,
        stepNumber: actualStepNumber,
        progressPercent: progressPercent,
        agentType: agentType,
        duration: duration,
        confidence: confidence,
        isCompleted: actualStepNumber === 4
      }]);
      
      // 現在の段階インデックスを更新
      if (stepNumber && stepNumber > currentStageIndex) {
        setCurrentStageIndex(stepNumber);
      }
    }
  };

  const startProcessing = () => {
    setProcessingStartTime(Date.now());
    setCurrentStageIndex(0);
    setProcessingSteps([]);
  };

  const completeProcessing = () => {
    updateAgentStatus(
      '✅ 処理完了', 
      '3つの返信パターンを生成しました', 
      'シンプル4エージェント協調による効率的な応答生成が完了しました',
      4,
      'SimpleNegotiationManager',
      0.95
    );
  };

  const generateReplyPatterns = async () => {
    if (!currentThread || !currentThread.messages || currentThread.messages.length === 0) return;
    
    setIsGeneratingPatterns(true);
    setReplyPatterns([]);
    setThreadAnalysis(null);
    startProcessing(); // 処理開始時刻を記録
    
    try {
      // 段階1: スレッド分析
      updateAgentStatus(
        '📊 スレッド分析', 
        'メッセージ履歴を分析し、現在の交渉状況を把握しています...', 
        'スレッド分析エージェントがメッセージ履歴を読み込み、交渉段階・相手の感情・懸念事項を分析します',
        1,
        'ThreadAnalysisAgent',
        0.85
      );
      console.log('🤖 AIエージェントが返信パターンを生成中...');
      
      // バックエンドの交渉エージェントAPIを呼び出し
      // 最新の改善版バックエンドを常に使用（メール種別判定・会話履歴参照機能付き）
      const apiUrl = 'https://infumatch-backend-269567634217.asia-northeast1.run.app';
      console.log('🔄 最新改善版バックエンドを使用（メール種別判定・会話履歴参照機能搭載）');
      
      console.log('🔗 使用するAPI URL:', apiUrl);
      console.log('🔧 環境変数 NEXT_PUBLIC_API_URL:', process.env.NEXT_PUBLIC_API_URL);
      
      // スレッドメッセージを整形
      const threadMessages = currentThread.messages.map(message => ({
        id: message.id,
        sender: getMessageSender(message),
        content: getMessagePlainText(message),
        date: new Date(parseInt(message.internalDate)).toISOString(),
        subject: getMessageSubject(message)
      }));
      
      // リクエストデータを準備（orchestrated negotiation API用）
      const requestData = {
        conversation_history: threadMessages.map(msg => ({
          role: msg.sender === 'InfuMatch' ? 'assistant' : 'user',
          content: msg.content
        })),
        new_message: threadMessages.length > 0 ? threadMessages[threadMessages.length - 1].content : '',
        context: {
          company_settings: {
            companyInfo: {
              companyName: "InfuMatch",
              contactPerson: "田中美咲",
              email: "tanaka@infumatch.com"
            },
            products: [
              { name: "健康食品A" },
              { name: "美容クリーム" }
            ]
          },
          custom_instructions: ""  // 後で更新
        }
      };
      
      console.log('📤 API送信データ:', JSON.stringify(requestData, null, 2));
      console.log('📝 カスタムプロンプトの状態:', customPrompt ? `「${customPrompt}」が設定されています` : '未設定');
      
      // 企業設定を取得 - 段階2の準備
      updateAgentStatus(
        '🧠 戦略立案', 
        '企業情報・商材情報・カスタム指示を考慮して戦略を立案しています...', 
        '戦略立案エージェントが企業設定とカスタム指示を統合し、最適な返信戦略を考案します',
        2,
        'ReplyStrategyAgent',
        0.90
      );
      let companySettings = {};
      try {
        const settingsResponse = await fetch('/api/settings');
        if (settingsResponse.ok) {
          const settingsData = await settingsResponse.json();
          companySettings = settingsData.data || {};
          console.log('🏢 企業設定を取得:', companySettings);
          console.log('🔍 設定API応答全体:', settingsData);
          
          // 設定の詳細をログ出力
          const companyInfo = companySettings.companyInfo || {};
          const products = companySettings.products || [];
          const negotiationSettings = companySettings.negotiationSettings || {};
          
          console.log('📋 企業設定詳細:');
          console.log('  - 会社名:', companyInfo.companyName);
          console.log('  - 業界:', companyInfo.industry);
          console.log('  - 商品数:', products.length);
          console.log('  - 交渉トーン:', negotiationSettings.preferredTone);
          console.log('  - 重要事項:', negotiationSettings.keyPriorities);
          console.log('  - 避ける話題:', negotiationSettings.avoidTopics);
          
          // 段階3: 内容評価 (設定読み込み完了後)
          updateAgentStatus(
            '🔍 内容評価', 
            `企業: ${companyInfo.companyName || '未設定'}, 商材: ${products.length}件を基に戦略内容を評価中`,
            `${companyInfo.companyName || '企業'}の設定を把握し、立案された戦略の適切性とリスク要因を評価します`,
            3,
            'ContentEvaluationAgent',
            0.85
          );
        } else {
          updateAgentStatus('⚠️ 設定取得失敗', '企業設定の読み込みに失敗しました', 'デフォルト設定で続行します');
        }
      } catch (e: any) {
        console.warn('⚠️ 企業設定の取得に失敗:', e);
        updateAgentStatus('⚠️ 設定エラー', `企業設定エラー: ${e.message || e}`, 'エラーが発生しましたが、処理を続行します');
      }
      
      // 企業設定を統合
      if (companySettings.companyInfo) {
        const companyInfo = companySettings.companyInfo;
        requestData.context.company_settings.companyInfo = {
          companyName: companyInfo.companyName || "InfuMatch",
          contactPerson: companyInfo.contactPerson || "田中美咲",
          industry: companyInfo.industry || "",
          employeeCount: companyInfo.employeeCount || "",
          website: companyInfo.website || "",
          description: companyInfo.description || "",
          contactEmail: companyInfo.contactEmail || ""
        };
      }
      
      // 商品情報を追加
      if (companySettings.products && companySettings.products.length > 0) {
        requestData.context.company_settings.products = companySettings.products;
      }
      
      // 交渉設定を追加
      if (companySettings.negotiationSettings) {
        const negSettings = companySettings.negotiationSettings;
        requestData.context.company_settings.negotiationSettings = {
          preferredTone: negSettings.preferredTone || "professional",
          responseTimeExpectation: negSettings.responseTimeExpectation || "normal",
          budgetFlexibility: negSettings.budgetFlexibility || "moderate",
          decisionMakers: negSettings.decisionMakers || [],
          communicationPreferences: negSettings.communicationPreferences || [],
          specialInstructions: negSettings.specialInstructions || "",
          keyPriorities: negSettings.keyPriorities || [],
          avoidTopics: negSettings.avoidTopics || []
        };
      }
      
      // マッチング設定を追加
      if (companySettings.matchingSettings) {
        const matchSettings = companySettings.matchingSettings;
        requestData.context.company_settings.matchingSettings = {
          priorityCategories: matchSettings.priorityCategories || [],
          minSubscribers: matchSettings.minSubscribers || 0,
          maxSubscribers: matchSettings.maxSubscribers || 1000000,
          minEngagementRate: matchSettings.minEngagementRate || 0,
          excludeCategories: matchSettings.excludeCategories || [],
          geographicFocus: matchSettings.geographicFocus || [],
          priorityKeywords: matchSettings.priorityKeywords || [],
          excludeKeywords: matchSettings.excludeKeywords || []
        };
      }
      
      // カスタムプロンプトを追加
      if (customPrompt.trim()) {
        updateAgentStatus(
          '📝 カスタム指示適用', 
          `ユーザー指示: "${customPrompt}"`, 
          `カスタム指示「${customPrompt}」を交渉戦略に組み込みます。この指示を優先的に考慮して返信を調整します`,
          2,
          'CustomizationAgent',
          0.90
        );
        requestData.context.custom_instructions = customPrompt.trim();
        console.log('📝 カスタムプロンプトを適用:', customPrompt);
      }
      
      // 段階4: パターン生成
      const threadSubject = currentThread.messages[0] ? getMessageSubject(currentThread.messages[0]) : 'No Subject';
      const messageCount = currentThread.messages.length;
      const lastSender = threadMessages[threadMessages.length - 1]?.sender || '不明';
      
      updateAgentStatus(
        '🎨 パターン生成', 
        `${messageCount}件のメッセージを基に3つの返信パターンを生成中...`, 
        `${lastSender}からのメッセージに対し、協調的・中立・主張的の3つのアプローチで返信パターンを生成します`,
        4,
        'PatternGenerationAgent',
        0.80
      );
      
      // 新しい4エージェント統合システムAPIを使用
      const fullUrl = `${apiUrl}/api/v1/negotiation/continue`;
      console.log('🌐 リクエスト先URL:', fullUrl);
      console.log('🎯 企業設定を活用した返信生成を開始します');
      console.log('📝 最終的なコンテキスト:', {
        has_company_settings: Object.keys(requestData.context.company_settings).length > 0,
        has_custom_instructions: !!requestData.context.custom_instructions,
        custom_instructions: requestData.context.custom_instructions || '設定なし'
      });
      
      const response = await fetch(fullUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData)
      });
      
      console.log('📊 レスポンス詳細:');
      console.log('  - ステータス:', response.status);
      console.log('  - ステータステキスト:', response.statusText);
      console.log('  - OK:', response.ok);
      console.log('  - URL:', response.url);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('❌ APIエラー詳細:', errorText);
        updateAgentStatus('❌ APIエラー', `${response.status}: ${errorText}`, 'APIエラーが発生しました。フォールバックモードに切り替えます');
        throw new Error(`API Error: ${response.status} ${response.statusText} - ${errorText}`);
      }
      
      const result = await response.json();
      console.log('📥 API応答:', result);
      
      // 返信不要・注意フラグのチェック
      if (result.reply_not_needed) {
        updateAgentStatus(
          '⚠️ 返信不要', 
          `${result.email_type}として判定されました`, 
          `理由: ${result.reason}`
        );
        setReplyPatterns([{
          approach: 'system_message',
          content: result.message,
          tone: 'informational',
          isSystemMessage: true
        }]);
        setAiBasicReply(result.message);
        setAiReplyReasoning(result.reason);
        return;
      }
      
      if (result.caution_required) {
        updateAgentStatus(
          '⚠️ 返信注意', 
          `${result.email_type}として判定されました`, 
          `理由: ${result.reason}`
        );
        setReplyPatterns([{
          approach: 'caution_message',
          content: result.message,
          tone: 'warning',
          isSystemMessage: true
        }]);
        setAiBasicReply(result.message);
        setAiReplyReasoning(result.reason);
        return;
      }
      
      // 詳細トレース情報を表示（新機能）
      if (result.detailed_trace) {
        console.log('🔍 === 4エージェント詳細トレース ===');
        const trace = result.detailed_trace;
        
        // 各ステージの詳細
        trace.processing_stages?.forEach((stage: any, index: number) => {
          console.log(`🎭 Stage ${stage.stage}: ${stage.name}`);
          console.log(`   ⏱️ 処理時間: ${stage.duration.toFixed(2)}秒`);
          console.log(`   ✅ ステータス: ${stage.status}`);
        });
        
        // 中間生成物の詳細
        console.log('📊 === 中間生成物 ===');
        if (trace.intermediate_outputs?.thread_analysis) {
          console.log('📋 スレッド分析結果:', trace.intermediate_outputs.thread_analysis);
        }
        if (trace.intermediate_outputs?.strategy_plan) {
          console.log('🧠 戦略立案結果:', trace.intermediate_outputs.strategy_plan);
        }
        if (trace.intermediate_outputs?.evaluation_result) {
          console.log('🔍 内容評価結果:', trace.intermediate_outputs.evaluation_result);
        }
        if (trace.intermediate_outputs?.patterns_result) {
          console.log('🎨 パターン生成結果:', Object.keys(trace.intermediate_outputs.patterns_result));
        }
        
        // パフォーマンス統計
        if (trace.performance_metrics) {
          console.log('⚡ === パフォーマンス統計 ===');
          console.log(`   🏃 総処理時間: ${trace.performance_metrics.total_duration.toFixed(2)}秒`);
          console.log(`   📈 処理効率: ${trace.performance_metrics.throughput}`);
          console.log('   📊 ステージ別処理時間:');
          Object.entries(trace.performance_metrics.stage_durations).forEach(([stage, duration]: [string, any]) => {
            console.log(`      ${stage}: ${duration.toFixed(2)}秒`);
          });
        }
        
        // 詳細トレース情報をstateに保存
        setDetailedTrace(trace);
      }
      
      // API応答を受信
      updateAgentStatus(
        '📥 応答受信', 
        'AI応答を受信し、パターン結果を処理中...', 
        'シンプル4エージェントシステムからの応答を解析し、生成された3つのパターンを処理しています',
        4,
        'SimpleNegotiationManager',
        0.85
      );

      // AI思考過程の詳細表示 (オーケストレーション対応)
      const aiThinking = result.ai_thinking || {};
      const orchestrationDetails = result.orchestration_details || {};
      const metadata = result.metadata || {};
      
      // 4段階システムでの最終処理
      if (metadata.processing_type === 'simple_4_agent') {
        updateAgentStatus(
          '✅ 処理完了', 
          `4つのシンプルエージェントによる効率的な応答生成完了`, 
          aiThinking.orchestration_summary || 'シンプル4エージェント協調による効率的な応答を生成しました',
          4,
          'SimpleNegotiationManager',
          0.95
        );
      } else {
        // フォールバック時の表示
        updateAgentStatus(
          '✅ 処理完了', 
          'フォールバックシステムによる応答生成完了', 
          `${aiThinking.processing_note || 'AI処理完了'} → ${aiThinking.reason || '標準応答生成'}`,
          4,
          'FallbackAgent',
          0.80
        );
      }
      
      // AI分析の詳細をログ出力
      console.log('🧠 AI詳細分析結果:', aiThinking);
      console.log('🎭 オーケストレーション詳細:', orchestrationDetails);
      console.log('📄 AI生成基本返信:', result.content);
      
      // 従来のAI思考過程も表示（互換性のため）
      if (aiThinking.message_analysis) {
        updateAgentStatus('🔍 メッセージ理解', aiThinking.message_analysis, 
          aiThinking.detected_intent || 'メッセージの意図を分析しました');
      }
      
      if (aiThinking.sentiment_analysis) {
        updateAgentStatus('💭 感情・トーン分析', aiThinking.sentiment_analysis, 
          aiThinking.negotiation_stage || '交渉段階を判定しました');
      }
      
      if (aiThinking.custom_instructions_impact) {
        updateAgentStatus('⚙️ カスタム指示適用', aiThinking.custom_instructions_impact, 
          'ユーザーの指示に基づいて応答をカスタマイズしました');
      }
      
      if (result.success) {
        // AIから返された基本返信を基に、3つの異なる特徴を持つパターンを生成
        const baseReply = result.content || 'AI応答が生成されませんでした';
        const contact = getThreadPrimaryContact(currentThread);
        
        // 基本的な分析結果を取得
        const basicMetadata = result.metadata || {};
        console.log('🔍 交渉エージェント分析結果:', basicMetadata);
        console.log(`🤖 AI基本返信: "${baseReply.substring(0, 50)}..."`);
        
        // 4エージェントシステムによる3パターン構築
        updateAgentStatus(
          '🎨 Gemini 3パターン生成完了', 
          'Geminiが3つの異なるトーンで返信を直接生成しました', 
          '協調的・プロフェッショナル・フォーマルの3パターンをGeminiが生成',
          4,
          'GeminiDirectGeneration',
          0.95
        );
        
        let patterns = [];
        
        // 4エージェントシステムの結果から3パターンを構築
        if (result.patterns) {
          const patternsFromAPI = result.patterns;
          patterns = [
            // 協調的パターン
            {
              pattern_type: patternsFromAPI.pattern_collaborative?.approach || 'collaborative',
              pattern_name: '協調的・親しみやすい',
              tone: patternsFromAPI.pattern_collaborative?.tone || 'friendly_accommodating',
              content: patternsFromAPI.pattern_collaborative?.content || 'パターン生成に失敗しました',
              reasoning: 'AIが分析結果に基づいて協調的で親しみやすいトーンで生成',
              recommendation_score: 0.90
            },
            // バランス型パターン  
            {
              pattern_type: patternsFromAPI.pattern_balanced?.approach || 'balanced',
              pattern_name: 'プロフェッショナル・バランス型',
              tone: patternsFromAPI.pattern_balanced?.tone || 'professional_polite',
              content: patternsFromAPI.pattern_balanced?.content || 'パターン生成に失敗しました',
              reasoning: 'AIが分析結果に基づいてプロフェッショナルで中立的なトーンで生成',
              recommendation_score: 0.95
            },
            // フォーマルパターン
            {
              pattern_type: patternsFromAPI.pattern_formal?.approach || 'formal',
              pattern_name: '格式高い・正式',
              tone: patternsFromAPI.pattern_formal?.tone || 'highly_formal',
              content: patternsFromAPI.pattern_formal?.content || 'パターン生成に失敗しました',
              reasoning: 'AIが分析結果に基づいて格式高く正式なトーンで生成',
              recommendation_score: 0.85
            }
          ];
        } else {
          // APIからパターンが取得できない場合のフォールバック
          // baseReplyには既に署名が含まれているため、追加の署名は不要
          patterns = [
            {
              pattern_type: 'collaborative',
              pattern_name: '協調的・親しみやすい',
              tone: 'friendly_accommodating',
              content: `${contact}様\n\nいつもお世話になっております。\n\n${baseReply}`,
              reasoning: 'フォールバック: 協調的なアプローチ',
              recommendation_score: 0.70
            },
            {
              pattern_type: 'balanced',
              pattern_name: 'プロフェッショナル・バランス型',
              tone: 'professional_polite',
              content: `${contact}様\n\nお忙しい中ご連絡いただき、ありがとうございます。\n\n${baseReply}`,
              reasoning: 'フォールバック: プロフェッショナルなアプローチ',
              recommendation_score: 0.75
            },
            {
              pattern_type: 'formal',
              pattern_name: '格式高い・正式',
              tone: 'highly_formal',
              content: `${contact}様\n\n平素よりお世話になっております。\n\n${baseReply}`,
              reasoning: 'フォールバック: 格式高いアプローチ',
              recommendation_score: 0.65
            }
          ];
        }
        
        const analysis = {
          thread_summary: `AIが会話履歴を分析: "${baseReply.substring(0, 50)}..."`,
          conversation_stage: basicMetadata.relationship_stage || '交渉エージェントによる分析完了',
          recommended_approach: 'AIが推奨する3つの異なるアプローチパターン',
          sentiment: 'neutral',
          // 将来の高度な分析機能のプレースホルダー
          success_probability: 0.75, // デモ用の値
          key_concerns: ['企業設定の活用', '効果的なコミュニケーション'],
          opportunities: ['AI交渉エージェントの活用', '戦略的アプローチ'],
          risks: [],
          next_steps: ['返信パターンの選択', '個別カスタマイズ']
        };
        
        // 段階7: 完了・結果出力
        updateAgentStatus(
          '✅ 完了・結果出力', 
          `3つの返信パターンが生成されました`, 
          `友好的・積極的、慎重・プロフェッショナル、ビジネス重視の3パターンを用意しました。${customPrompt ? 'カスタム指示も反映済みです。' : ''}状況に応じて最適なものを選択してください`,
          7,
          'NegotiationManager',
          0.95
        );
        console.log(`✅ AI返信を基に3つのパターンを生成しました: "${baseReply.substring(0, 50)}..."`);
        
        setReplyPatterns(patterns);
        setThreadAnalysis(analysis);
        
        // 新機能：AI生成基本返信と理由を設定
        if (result.basic_reply) {
          console.log('💌 AI基本返信を受信:', result.basic_reply.substring(0, 50) + '...');
          setAiBasicReply(result.basic_reply);
        }
        
        if (result.reply_reasoning) {
          console.log('🧠 返信理由を受信:', result.reply_reasoning.substring(0, 50) + '...');
          setAiReplyReasoning(result.reply_reasoning);
        }
      } else {
        updateAgentStatus('❌ 生成失敗', result.error || 'API返信が不正な形式です');
        throw new Error(result.error || 'API返信が不正な形式です');
      }
      
    } catch (error: any) {
      console.error('❌ 返信パターン生成エラー:', error);
      updateAgentStatus(
        '❌ エラー発生', 
        error.message || error.toString(), 
        'エラーが発生したため、フォールバックパターンを使用します',
        7,
        'ErrorHandler',
        0.30
      );
      
      // フォールバック: エラー時はモックデータを使用
      console.log('🔄 フォールバック: モックデータを使用します');
      
      const fallbackPatterns = [
        {
          pattern_type: 'friendly_enthusiastic',
          pattern_name: '友好的・積極的',
          tone: '親しみやすく、前向きで協力的なトーン',
          content: `${getThreadPrimaryContact(currentThread)}様

いつもお世話になっております。InfuMatchの田中です。

ご連絡いただき、ありがとうございます！
ぜひ詳細についてお話しさせていただければと思います。

お時間のある際に、お電話やビデオ通話でお話しできればと思いますが、いかがでしょうか？

お返事お待ちしております。

よろしくお願いいたします。
田中`,
          reasoning: 'コラボレーションに積極的で、関係構築を重視するアプローチ',
          recommendation_score: 0.85
        },
        {
          pattern_type: 'cautious_professional',
          pattern_name: '慎重・プロフェッショナル',
          tone: '丁寧で専門的、詳細を重視するトーン',
          content: `${getThreadPrimaryContact(currentThread)}様

お忙しい中、ご連絡いただきありがとうございます。
InfuMatchの田中と申します。

ご提案いただいた件について、詳細を確認させていただきたく思います。

・プロジェクトの具体的な内容
・ご希望のスケジュール
・ご予算の範囲

などについて、お聞かせいただけますでしょうか。

ご検討のほど、よろしくお願いいたします。

田中`,
          reasoning: 'リスクを最小限に抑え、詳細を確認してから進めたい場合',
          recommendation_score: 0.75
        },
        {
          pattern_type: 'business_focused',
          pattern_name: 'ビジネス重視',
          tone: '効率的で結果重視、具体的な提案を含むトーン',
          content: `${getThreadPrimaryContact(currentThread)}様

InfuMatchの田中です。

ご連絡いただいた件について、以下のような形でお手伝いできると考えております：

1. 商品紹介動画の制作サポート
2. エンゲージメント分析レポートの提供
3. フォロワー向けプロモーション企画

ご予算に応じて最適なプランをご提案いたします。
来週、30分程度のお時間をいただけますでしょうか？

お返事をお待ちしております。

田中`,
          reasoning: '具体的な価値提案を示し、次のステップを明確にしたい場合',
          recommendation_score: 0.90
        }
      ];
      
      // フォールバック完了
      updateAgentStatus(
        '✅ フォールバック完了', 
        'フォールバックパターンを生成しました', 
        'エラーが発生しましたが、標準的な返信パターンを用意しました。手動で調整してご利用ください',
        7,
        'FallbackSystem',
        0.60
      );

      setReplyPatterns(fallbackPatterns);
      setThreadAnalysis({
        relationship_stage: 'initial_contact',
        emotional_tone: 'positive',
        urgency_level: 'normal',
        main_topics: ['コラボレーション', '商品紹介', 'プロモーション'],
        note: 'フォールバックモードで生成（AI分析は利用できませんでした）'
      });
      
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
      // 🔍 DEBUG: 新規メール送信データの詳細をログ出力
      const newEmailData = {
        to: newEmailTo,
        subject: newEmailSubject,
        message: newEmailBody,
      };
      
      console.log('=== FRONTEND NEW EMAIL SEND DEBUG START ===');
      console.log('📧 New email data:', JSON.stringify(newEmailData, null, 2));
      console.log('📧 To:', newEmailTo);
      console.log('📧 Subject:', newEmailSubject);
      console.log('📧 Body:', newEmailBody);
      
      const response = await fetch('/api/gmail/send', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newEmailData),
      });

      // 認証エラーをチェック
      const authErrorHandled = await handleApiResponse(response);
      if (authErrorHandled) {
        setIsSendingNewEmail(false);
        return;
      }

      if (response.ok) {
        const responseData = await response.json();
        console.log('✅ New email send response:', responseData);
        console.log('=== FRONTEND NEW EMAIL SEND DEBUG END (SUCCESS) ===');
        
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
        console.error('❌ New email send failed:', response.status, response.statusText);
        console.error('❌ Error response:', errorData);
        console.log('=== FRONTEND NEW EMAIL SEND DEBUG END (ERROR) ===');
        
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
      const lastMessage = currentThread.messages && currentThread.messages.length > 0 
        ? currentThread.messages[currentThread.messages.length - 1] 
        : null;
      
      if (!lastMessage) {
        alert('メッセージが見つかりません');
        return;
      }
      const fromHeader = getHeader(lastMessage, 'from');
      const subjectHeader = getHeader(lastMessage, 'subject');
      
      // 添付ファイルがある場合はFormDataを使用
      if (attachmentFiles.length > 0) {
        const lastMessageId = lastMessage.id;
        
        // 正しい返信ヘッダーを取得
        let replyHeaders = null;
        try {
          const response = await fetch(`/api/gmail/threads/${currentThread.id}/reply-headers?messageId=${lastMessageId}`);
          if (response.ok) {
            const headerData = await response.json();
            replyHeaders = headerData.replyHeaders;
            console.log('📧 Retrieved reply headers for attachment email:', replyHeaders);
          }
        } catch (error) {
          console.error('❌ Error getting reply headers for attachment email:', error);
        }
        
        const formData = new FormData();
        formData.append('to', fromHeader);
        
        // 正しい件名を使用
        const replySubject = replyHeaders?.subject || 
          (subjectHeader.startsWith('Re:') ? subjectHeader : `Re: ${subjectHeader}`);
        formData.append('subject', replySubject);
        formData.append('message', replyText);
        formData.append('threadId', currentThread.id);
        formData.append('replyToMessageId', lastMessageId);
        
        // 返信ヘッダー情報を追加
        if (replyHeaders) {
          formData.append('replyHeaders', JSON.stringify(replyHeaders));
        }
        
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
        // 添付ファイルなしの場合は正しい返信ヘッダーを取得してAPIを使用
        const lastMessageId = lastMessage.id;
        
        console.log('📧 Getting reply headers for message:', lastMessageId);
        
        // 正しい返信ヘッダーを取得
        let replyHeaders = null;
        try {
          // GmailServiceを使って正しいヘッダー情報を取得
          const response = await fetch(`/api/gmail/threads/${currentThread.id}/reply-headers?messageId=${lastMessageId}`);
          if (response.ok) {
            replyHeaders = await response.json();
            console.log('📧 Retrieved reply headers:', replyHeaders);
          } else {
            console.warn('⚠️ Failed to get reply headers, using fallback');
          }
        } catch (error) {
          console.error('❌ Error getting reply headers:', error);
        }
        
        // 件名を設定（ヘッダーから取得した件名を優先）
        const replySubject = replyHeaders?.subject || 
          (subjectHeader.startsWith('Re:') ? subjectHeader : `Re: ${subjectHeader}`);
        
        // 🔍 DEBUG: 送信するデータの詳細をログ出力
        const sendData = {
          to: fromHeader,
          subject: replySubject,
          message: replyText,
          threadId: currentThread.id,
          replyToMessageId: lastMessageId,
          replyHeaders: replyHeaders // 新しく追加
        };
        
        console.log('=== FRONTEND EMAIL SEND DEBUG START ===');
        console.log('📧 Frontend send data:', JSON.stringify(sendData, null, 2));
        console.log('📧 Original subject header:', subjectHeader);
        console.log('📧 Reply subject:', replySubject);
        console.log('📧 From header:', fromHeader);
        console.log('📧 Reply text:', replyText);
        console.log('📧 Thread ID:', currentThread.id);
        console.log('📧 Reply to message ID:', lastMessageId);
        console.log('📧 Reply headers:', replyHeaders);
        console.log('📧 Last message details:', lastMessage);
        
        const response = await fetch('/api/gmail/send', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(sendData),
        });

        // 認証エラーをチェック
        const authErrorHandled = await handleApiResponse(response);
        if (authErrorHandled) {
          return;
        }

        if (response.ok) {
          const responseData = await response.json();
          console.log('✅ Email send response:', responseData);
          console.log('=== FRONTEND EMAIL SEND DEBUG END (SUCCESS) ===');
          
          setReplyText('');
          alert('メールを送信しました');
          await loadThreadDetails(currentThread.id);
        } else {
          const errorData = await response.text();
          console.error('❌ Email send failed:', response.status, response.statusText);
          console.error('❌ Error response:', errorData);
          console.log('=== FRONTEND EMAIL SEND DEBUG END (ERROR) ===');
          
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

  // AI返信パターン生成用のヘルパー関数
  const getMessageSender = (message: GmailMessage): string => {
    const fromHeader = getHeader(message, 'from');
    const emailMatch = fromHeader.match(/^(.+?)\s*<(.+)>$/);
    return emailMatch ? emailMatch[1].trim().replace(/['"]/g, '') : fromHeader;
  };

  const getMessagePlainText = (message: GmailMessage): string => {
    const emailBody = getEmailBody(message);
    // HTMLタグを除去してプレーンテキストにする
    return emailBody.replace(/<[^>]*>/g, '').replace(/&[^;]+;/g, ' ').trim();
  };

  const getMessageSubject = (message: GmailMessage): string => {
    return getHeader(message, 'subject');
  };

  const isFromUser = (message: GmailMessage) => {
    const fromHeader = getHeader(message, 'from');
    // 簡単なチェック - 実際のユーザーメールアドレスと比較する必要がある
    return fromHeader.includes('@company.com'); // 仮の判定
  };

  // スレッドから件名を取得
  const getThreadSubject = (thread: EmailThread): string => {
    if (!thread.messages || thread.messages.length === 0) {
      // snippetから件名を推測
      const snippetText = thread.snippet || '';
      if (snippetText.length > 0) {
        // 最初の50文字程度を件名として使用
        return snippetText.substring(0, 50) + (snippetText.length > 50 ? '...' : '');
      }
      return 'タイトルなし';
    }
    const firstMessage = thread.messages[0];
    const subject = getHeader(firstMessage, 'subject');
    if (subject && subject.trim()) {
      return subject;
    }
    // subjectが空の場合もsnippetを使用
    const snippetText = thread.snippet || '';
    if (snippetText.length > 0) {
      return snippetText.substring(0, 50) + (snippetText.length > 50 ? '...' : '');
    }
    return 'タイトルなし';
  };

  // スレッドから主要な相手を取得
  const getThreadPrimaryContact = (thread: EmailThread): string => {
    // まずsnippetから送信者情報を推測
    const snippet = thread.snippet || '';
    
    // snippetに含まれる一般的なパターンを解析
    if (snippet.includes('グロービス')) return 'グロービス経営大学院';
    if (snippet.includes('GitHub')) return 'GitHub';
    if (snippet.includes('Amazon')) return 'Amazon';
    if (snippet.includes('Google')) return 'Google';
    
    // メッセージが利用可能な場合は詳細を取得
    if (thread.messages && thread.messages.length > 0) {
      const latestMessage = thread.messages[thread.messages.length - 1];
      const fromHeader = getHeader(latestMessage, 'from');
      
      if (fromHeader) {
        // メールアドレスから名前を抽出（"名前 <email@example.com>" 形式）
        const emailMatch = fromHeader.match(/^(.+?)\s*<(.+)>$/);
        if (emailMatch) {
          let name = emailMatch[1].trim().replace(/['"]/g, '');
          
          // MIME エンコードされた名前をデコード
          if (name.includes('=?UTF-8?B?')) {
            try {
              const base64Match = name.match(/=\?UTF-8\?B\?(.+?)\?=/);
              if (base64Match) {
                name = Buffer.from(base64Match[1], 'base64').toString('utf8');
              }
            } catch (e) {
              console.warn('Failed to decode MIME header:', e);
            }
          }
          
          return name || emailMatch[2].split('@')[0];
        }
        
        if (fromHeader.includes('@')) {
          return fromHeader.split('@')[0];
        }
        
        return fromHeader;
      }
    }
    
    // 最後の手段：snippetの最初の部分から推測
    if (snippet.length > 0) {
      const firstLine = snippet.split('\n')[0];
      if (firstLine.length > 0 && firstLine.length < 30) {
        return firstLine;
      }
      return snippet.substring(0, 20) + '...';
    }
    
    return '不明な送信者';
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
          <Header variant="glass" />

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
                  
                  <div className="flex items-center gap-2 mb-4">
                    <button
                      onClick={() => setShowSearch(!showSearch)}
                      className={`px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 flex items-center gap-2 ${
                        showSearch 
                          ? 'bg-indigo-100 text-indigo-700 border border-indigo-300' 
                          : 'bg-gray-50 text-gray-600 hover:bg-gray-100 border border-gray-200'
                      }`}
                    >
                      🔍 検索
                    </button>
                    <button
                      onClick={() => setShowNotifications(!showNotifications)}
                      className={`px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 flex items-center gap-2 ${
                        showNotifications 
                          ? 'bg-orange-100 text-orange-700 border border-orange-300' 
                          : 'bg-gray-50 text-gray-600 hover:bg-gray-100 border border-gray-200'
                      }`}
                    >
                      🔔 通知
                    </button>
                    <button
                      onClick={async () => {
                        console.log('🔄 手動更新ボタンクリック');
                        await loadThreads();
                        console.log('✅ スレッド更新完了');
                      }}
                      disabled={isLoadingThreads}
                      className="px-3 py-2 rounded-lg text-sm font-medium bg-green-50 text-green-700 hover:bg-green-100 border border-green-200 transition-all duration-200 flex items-center gap-2 disabled:opacity-50"
                    >
                      {isLoadingThreads || isRealtimeLoading ? (
                        <svg className="animate-spin h-3 w-3" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                      ) : (
                        '🔄'
                      )}
                      更新
                    </button>
                    <div className="flex items-center gap-4 text-xs ml-auto">
                      <div className="flex items-center text-green-600">
                        <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                        Gmail接続済み
                      </div>
                      <div className={`flex items-center ${gmailMonitoringActive ? 'text-purple-600' : 'text-gray-400'}`}>
                        <svg className={`w-3 h-3 mr-1 ${gmailMonitoringActive ? 'animate-pulse' : ''}`} fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                        {gmailMonitoringActive ? '自動監視中' : '監視停止中'}
                      </div>
                    </div>
                  </div>
                </div>
                <div className="divide-y divide-gray-100 max-h-96 overflow-y-auto">
                  {(() => {
                    console.log('🔍 Rendering threads, count:', threads.length);
                    console.log('🔍 Threads data:', threads);
                    return threads.length === 0 ? (
                      <div className="p-6 text-center text-gray-500">
                        <p>メールスレッドが見つかりません</p>
                        <p className="text-xs mt-2">現在のスレッド数: {threads.length}</p>
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
                                {thread.messages?.length || 0}
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
                                  {thread.messages && thread.messages.length > 0 && formatDate(thread.messages[thread.messages.length - 1].internalDate)}
                                </p>
                              </div>
                              <div className="flex items-center space-x-2">
                                {/* 自動化状態インジケーター */}
                                {threadAutomationStates[thread.id]?.isActive && (
                                  <div className={`flex items-center space-x-1 px-2 py-0.5 rounded-full text-xs ${
                                    threadAutomationStates[thread.id].mode === 'semi_auto' 
                                      ? 'bg-purple-100 text-purple-700' 
                                      : 'bg-gray-100 text-gray-600'
                                  }`}>
                                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                                    </svg>
                                    <span>{threadAutomationStates[thread.id].mode === 'semi_auto' ? '半自動' : '手動'}</span>
                                  </div>
                                )}
                                {thread.messages && thread.messages.length > 1 && (
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
                  );
                  })()}
                </div>
              </div>
            </div>

            {/* メール詳細 */}
            <div className="lg:col-span-2">
              {currentThread ? (
                <div className="space-y-4">
                  {/* スレッド自動化コントロール */}
                  <ThreadAutomationControl 
                    threadId={currentThread.id}
                    threadSubject={currentThread.messages && currentThread.messages.length > 0 ? 
                      getHeader(currentThread.messages[0], 'subject') : 'メールスレッド'}
                    onModeChange={(mode, enabled) => {
                      console.log(`🤖 スレッド自動化状態変更: ${currentThread.id}`, {
                        モード: mode,
                        有効: enabled,
                        時刻: new Date().toLocaleTimeString()
                      });
                      
                      // スレッドの自動化状態を更新
                      setThreadAutomationStates(prev => ({
                        ...prev,
                        [currentThread.id]: { mode, isActive: enabled }
                      }));
                      
                      // 半自動モードが有効になった場合、スレッドの追跡を開始
                      if (mode === 'semi_auto' && enabled) {
                        console.log(`🎯 スレッド ${currentThread.id} の半自動監視を開始`);
                        
                        // 現在のスレッドの最新メッセージ時刻を取得して追跡開始
                        const initializeThreadTracking = async () => {
                          try {
                            const messages = currentThread.messages || [];
                            if (messages.length > 0) {
                              const latestMessage = messages[messages.length - 1];
                              const latestMessageTime = latestMessage.internalDate;
                              
                              setTrackedThreads(prev => ({
                                ...prev,
                                [currentThread.id]: {
                                  lastMessageTime: latestMessageTime,
                                  isAutomated: true
                                }
                              }));
                              
                              console.log(`✅ スレッド ${currentThread.id} の追跡開始完了`, {
                                最新メッセージ時刻: latestMessageTime,
                                メッセージ数: messages.length
                              });
                            }
                          } catch (error) {
                            console.error(`❌ スレッド ${currentThread.id} の追跡開始エラー:`, error);
                          }
                        };
                        
                        initializeThreadTracking();
                      } else if (!enabled) {
                        // 自動化が無効になった場合、追跡を停止
                        console.log(`⏹️ スレッド ${currentThread.id} の自動化追跡を停止`);
                        setTrackedThreads(prev => {
                          const updated = { ...prev };
                          delete updated[currentThread.id];
                          // localStorageも更新
                          if (Object.keys(updated).length === 0) {
                            localStorage.removeItem('trackedThreads');
                          } else {
                            localStorage.setItem('trackedThreads', JSON.stringify(updated));
                          }
                          return updated;
                        });
                      }
                    }}
                  />
                  
                  <div className="card">
                  {/* ヘッダー */}
                  <div className="p-6 border-b border-gray-100">
                    <div className="flex items-center justify-between">
                      <div>
                        <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                          Gmail スレッド詳細
                          {threadAutomationStates[currentThread.id]?.isActive && (
                            <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                              threadAutomationStates[currentThread.id].mode === 'semi_auto' 
                                ? 'bg-purple-100 text-purple-800' 
                                : 'bg-gray-100 text-gray-800'
                            }`}>
                              <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                              </svg>
                              {threadAutomationStates[currentThread.id].mode === 'semi_auto' ? '半自動' : '手動'}モード
                            </span>
                          )}
                        </h2>
                        <p className="text-sm text-gray-500 mt-1">
                          {currentThread.messages?.length || 0}件のメッセージ
                        </p>
                        {/* 相手のメールアドレス表示 */}
                        {currentThread.messages && currentThread.messages.length > 0 && (() => {
                          const lastMessage = currentThread.messages[currentThread.messages.length - 1];
                          const fromHeader = getHeader(lastMessage, 'from');
                          const emailMatch = fromHeader.match(/^(.+?)\s*<(.+)>$/);
                          const recipientEmail = emailMatch ? emailMatch[2] : fromHeader;
                          const recipientName = emailMatch ? emailMatch[1].trim().replace(/['"]/g, '') : '';
                          
                          return (
                            <div className="mt-2 flex items-center space-x-2">
                              <span className="text-xs text-gray-400">送信先:</span>
                              <span className="text-sm font-medium text-indigo-600">
                                {recipientName && recipientName !== recipientEmail ? 
                                  `${recipientName} <${recipientEmail}>` : 
                                  recipientEmail
                                }
                              </span>
                            </div>
                          );
                        })()}
                      </div>
                    </div>
                  </div>

                  {/* メール一覧 */}
                  <div className="max-h-96 overflow-y-auto scrollbar-hide">
                    {(currentThread.messages || []).map((message, index) => (
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
                          <div className="text-gray-700 leading-relaxed whitespace-pre-wrap break-words">
                            {getEmailBody(message)}
                          </div>
                          
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
                  <h4 className="font-semibold text-gray-800 mb-3">📊 高度な交渉分析結果</h4>
                  
                  {/* 基本分析 */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm mb-4">
                    <div className="text-center">
                      <div className="text-gray-500">交渉段階</div>
                      <div className="font-medium text-blue-600">
                        {threadAnalysis.conversation_stage || '分析中'}
                      </div>
                    </div>
                    <div className="text-center">
                      <div className="text-gray-500">成功確率</div>
                      <div className={`font-medium ${
                        (threadAnalysis.success_probability || 0) > 0.7 ? 'text-green-600' :
                        (threadAnalysis.success_probability || 0) > 0.4 ? 'text-yellow-600' : 'text-red-600'
                      }`}>
                        {threadAnalysis.success_probability ? 
                          `${(threadAnalysis.success_probability * 100).toFixed(1)}%` : 'N/A'}
                      </div>
                    </div>
                    <div className="text-center">
                      <div className="text-gray-500">感情スコア</div>
                      <div className={`font-medium ${
                        (threadAnalysis.sentiment || 0) > 0.3 ? 'text-green-600' :
                        (threadAnalysis.sentiment || 0) < -0.3 ? 'text-red-600' : 'text-gray-600'
                      }`}>
                        {typeof threadAnalysis.sentiment === 'number' ? 
                          threadAnalysis.sentiment.toFixed(2) : '中立'}
                      </div>
                    </div>
                    <div className="text-center">
                      <div className="text-gray-500">推奨戦略</div>
                      <div className="font-medium text-purple-600">
                        {threadAnalysis.recommended_approach || '戦略分析中'}
                      </div>
                    </div>
                  </div>
                  
                  {/* 詳細分析 */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                    {/* 懸念事項 */}
                    {threadAnalysis.key_concerns && threadAnalysis.key_concerns.length > 0 && (
                      <div className="bg-red-50 rounded p-3">
                        <div className="font-medium text-red-800 mb-1">⚠️ 懸念事項</div>
                        <ul className="text-red-700 text-xs space-y-1">
                          {threadAnalysis.key_concerns.map((concern, idx) => (
                            <li key={idx}>• {concern}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    
                    {/* 機会 */}
                    {threadAnalysis.opportunities && threadAnalysis.opportunities.length > 0 && (
                      <div className="bg-green-50 rounded p-3">
                        <div className="font-medium text-green-800 mb-1">💡 機会</div>
                        <ul className="text-green-700 text-xs space-y-1">
                          {threadAnalysis.opportunities.map((opportunity, idx) => (
                            <li key={idx}>• {opportunity}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    
                    {/* 次のステップ */}
                    {threadAnalysis.next_steps && threadAnalysis.next_steps.length > 0 && (
                      <div className="bg-blue-50 rounded p-3">
                        <div className="font-medium text-blue-800 mb-1">🎯 次のステップ</div>
                        <ul className="text-blue-700 text-xs space-y-1">
                          {threadAnalysis.next_steps.map((step, idx) => (
                            <li key={idx}>• {step}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* エージェント動作状況表示 */}
              <div className="mb-6">
                <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-4 border border-blue-200">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="flex-shrink-0">
                        <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                          <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.847a4.5 4.5 0 003.09 3.09L15.75 12l-2.847.813a4.5 4.5 0 00-3.09 3.09z" />
                          </svg>
                        </div>
                      </div>
                      <div>
                        <div className="text-sm font-medium text-blue-900">
                          🤖 AIエージェント: {agentStatus}
                        </div>
                        {processingSteps.length > 0 && (
                          <div className="text-xs text-blue-700 mt-1">
                            {processingSteps[processingSteps.length - 1].detail}
                          </div>
                        )}
                      </div>
                    </div>
                    
                    {/* 処理ステップ履歴 */}
                    {processingSteps.length > 1 && (
                      <button
                        onClick={() => setShowCustomPrompt(!showCustomPrompt)}
                        className="text-xs text-blue-600 hover:text-blue-800 underline flex items-center space-x-1"
                      >
                        <span>🔍 5段階詳細表示</span>
                        <span className="bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded text-xs">
                          {processingSteps.length}/5完了
                        </span>
                        <span className="text-xs">
                          {showCustomPrompt ? '▲' : '▼'}
                        </span>
                      </button>
                    )}
                  </div>
                  
                  {/* 7段階詳細ステップ表示 */}
                  {showCustomPrompt && processingSteps.length > 1 && (
                    <div className="mt-3 border-t border-blue-200 pt-3">
                      {/* 進捗バー */}
                      <div className="mb-4">
                        <div className="flex justify-between text-xs text-blue-600 mb-1">
                          <span>処理進捗</span>
                          <span>{Math.max(...processingSteps.map(s => s.progressPercent || 0))}%</span>
                        </div>
                        <div className="w-full bg-blue-100 rounded-full h-2">
                          <div 
                            className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full transition-all duration-500"
                            style={{ width: `${Math.max(...processingSteps.map(s => s.progressPercent || 0))}%` }}
                          ></div>
                        </div>
                        <div className="flex justify-between text-xs text-blue-500 mt-1">
                          {PROCESSING_STAGES.map((stage, idx) => (
                            <div 
                              key={stage.number}
                              className={`text-center ${
                                processingSteps.some(s => s.stepNumber >= stage.number) 
                                  ? 'text-blue-700 font-medium' 
                                  : 'text-blue-400'
                              }`}
                            >
                              {idx === 0 || idx === 3 || idx === 6 ? stage.number : '·'}
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* ステップ詳細 */}
                      <div className="space-y-3 max-h-60 overflow-y-auto">
                        {processingSteps.map((step, index) => {
                          const isLatest = index === processingSteps.length - 1;
                          const stage = PROCESSING_STAGES.find(s => s.number === step.stepNumber);
                          
                          return (
                            <div 
                              key={index} 
                              className={`space-y-2 p-3 rounded-lg border-l-4 ${
                                isLatest 
                                  ? 'border-l-blue-500 bg-blue-50' 
                                  : step.isCompleted 
                                    ? 'border-l-green-400 bg-green-50' 
                                    : 'border-l-gray-300 bg-gray-50'
                              }`}
                            >
                              <div className="flex items-start justify-between">
                                <div className="flex-grow">
                                  <div className="flex items-center space-x-2">
                                    <span className="text-xs font-bold text-blue-700">
                                      段階{step.stepNumber}/5
                                    </span>
                                    {step.agentType && (
                                      <span className="text-xs text-purple-600 bg-purple-100 px-2 py-0.5 rounded">
                                        {step.agentType}
                                      </span>
                                    )}
                                    {step.confidence && (
                                      <span className="text-xs text-green-600">
                                        信頼度: {(step.confidence * 100).toFixed(0)}%
                                      </span>
                                    )}
                                  </div>
                                  <div className="text-xs font-medium text-blue-800 mt-1">
                                    <span className="text-gray-500">{step.time}</span> - {step.status}
                                  </div>
                                  <div className="text-xs text-blue-700 mt-1">
                                    {step.detail}
                                  </div>
                                  {step.reasoning && (
                                    <details className="mt-2">
                                      <summary className="text-xs text-blue-600 cursor-pointer hover:text-blue-800">
                                        💭 AI思考過程を表示
                                      </summary>
                                      <div className="text-xs text-blue-600 mt-1 pl-3 border-l-2 border-blue-200 italic">
                                        {step.reasoning}
                                      </div>
                                    </details>
                                  )}
                                </div>
                                <div className="ml-2 flex flex-col items-end">
                                  {step.duration && step.duration > 0 && (
                                    <span className="text-xs text-gray-500">
                                      {(step.duration / 1000).toFixed(1)}s
                                    </span>
                                  )}
                                  {step.isCompleted && (
                                    <span className="text-green-500 text-xs">✓</span>
                                  )}
                                </div>
                              </div>
                              
                              {/* ステージ説明 */}
                              {stage && isLatest && (
                                <div className="text-xs text-blue-600 bg-blue-100 p-2 rounded">
                                  {stage.description}
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* カスタムプロンプト入力エリア */}
              <div className="mb-6">
                <div className="bg-yellow-50 rounded-xl p-4 border border-yellow-200">
                  <div className="flex items-center justify-between mb-3">
                    <label className="text-sm font-medium text-yellow-800 flex items-center">
                      <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                      📝 カスタム指示（任意）
                    </label>
                    <button
                      onClick={() => setCustomPrompt('')}
                      className="text-xs text-yellow-600 hover:text-yellow-800 underline"
                    >
                      クリア
                    </button>
                  </div>
                  
                  <textarea
                    value={customPrompt}
                    onChange={(e) => setCustomPrompt(e.target.value)}
                    placeholder="例: 値引きしたい、もっと積極的に、丁寧な言葉遣いで、急ぎで返信が欲しい、など"
                    className="w-full px-3 py-2 text-sm border border-yellow-300 rounded-lg focus:ring-2 focus:ring-yellow-500 focus:border-transparent resize-none"
                    rows={2}
                  />
                  
                  <div className="mt-2 text-xs text-yellow-700">
                    💡 AIは企業設定・商材情報・交渉ポイントと併せて、ここで指定した内容も考慮して返信を生成します
                  </div>
                </div>
              </div>

              {/* 生成ボタン */}
              <div className="flex justify-center gap-4 mb-6">
                {/* 通常版ボタン */}
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
                      🤖 AI返信候補を生成
                    </>
                  )}
                </button>

              </div>

            </div>
            
            {/* AI生成基本返信表示エリア */}
            {aiBasicReply && (
              <div className="mb-8 bg-gradient-to-r from-green-50 to-blue-50 rounded-xl p-6 border border-green-200">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-800 flex items-center">
                    <svg className="w-5 h-5 mr-2 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.847a4.5 4.5 0 003.09 3.09L15.75 12l-2.847.813a4.5 4.5 0 00-3.09 3.09z" />
                    </svg>
                    🤖 AI生成基本返信
                  </h3>
                  <button
                    onClick={() => setReplyText(aiBasicReply)}
                    className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm"
                  >
                    返信欄に適用
                  </button>
                </div>
                
                <div className="bg-white rounded-lg p-4 border border-green-100 mb-4">
                  <div className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
                    {aiBasicReply}
                  </div>
                </div>
                
                {/* 返信理由表示 */}
                {aiReplyReasoning && (
                  <div className="mt-4">
                    <button
                      onClick={() => setShowReasoning(!showReasoning)}
                      className="flex items-center text-sm text-blue-600 hover:text-blue-800 mb-2"
                    >
                      <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                      </svg>
                      💭 なぜこの返信にしたのか - AI判断理由
                      <span className="ml-2 text-xs">
                        {showReasoning ? '▲' : '▼'}
                      </span>
                    </button>
                    
                    {showReasoning && (
                      <div className="bg-blue-50 rounded-lg p-4 border border-blue-100">
                        <div className="text-sm text-blue-800 leading-relaxed whitespace-pre-wrap">
                          {aiReplyReasoning}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
            
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

        {/* 詳細トレース表示パネル */}
        {detailedTrace && (
          <div className="mt-6 bg-gray-50 rounded-lg p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-800">
                🔍 5段階エージェント詳細トレース
              </h3>
              <button
                onClick={() => setShowDetailedTrace(!showDetailedTrace)}
                className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
              >
                {showDetailedTrace ? '非表示' : '詳細表示'}
              </button>
            </div>
            
            {showDetailedTrace && (
              <div className="space-y-4">
                {/* パフォーマンス統計 */}
                {detailedTrace.performance_metrics && (
                  <div className="bg-white rounded p-3 border">
                    <h4 className="font-medium text-gray-700 mb-2">⚡ パフォーマンス統計</h4>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-gray-600">総処理時間:</span>
                        <span className="ml-2 font-mono">{detailedTrace.performance_metrics.total_duration?.toFixed(2)}秒</span>
                      </div>
                      <div>
                        <span className="text-gray-600">処理効率:</span>
                        <span className="ml-2 font-mono">{detailedTrace.performance_metrics.throughput}</span>
                      </div>
                    </div>
                  </div>
                )}

                {/* 処理ステージ詳細 */}
                {detailedTrace.processing_stages && (
                  <div className="bg-white rounded p-3 border">
                    <h4 className="font-medium text-gray-700 mb-3">🎭 処理ステージ詳細</h4>
                    <div className="space-y-2">
                      {detailedTrace.processing_stages.map((stage: any, index: number) => (
                        <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                          <div className="flex items-center space-x-3">
                            <span className="w-6 h-6 bg-blue-100 text-blue-700 rounded-full flex items-center justify-center text-sm font-medium">
                              {stage.stage}
                            </span>
                            <span className="font-medium">{stage.name}</span>
                          </div>
                          <div className="flex items-center space-x-4 text-sm text-gray-600">
                            <span>⏱️ {stage.duration?.toFixed(2)}秒</span>
                            <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs">
                              {stage.status}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* 中間生成物 */}
                {detailedTrace.intermediate_outputs && (
                  <div className="bg-white rounded p-3 border">
                    <h4 className="font-medium text-gray-700 mb-3">📊 中間生成物</h4>
                    <div className="space-y-3">
                      {detailedTrace.intermediate_outputs.thread_analysis && (
                        <div className="border-l-4 border-blue-400 pl-3">
                          <h5 className="font-medium text-sm text-blue-700">📋 スレッド分析結果</h5>
                          <div className="text-sm text-gray-600 mt-1">
                            <div>交渉段階: <span className="font-mono">{detailedTrace.intermediate_outputs.thread_analysis.negotiation_stage}</span></div>
                            <div>感情分析: <span className="font-mono">{detailedTrace.intermediate_outputs.thread_analysis.sentiment}</span></div>
                            <div>緊急度: <span className="font-mono">{detailedTrace.intermediate_outputs.thread_analysis.urgency_level}</span></div>
                          </div>
                        </div>
                      )}

                      {detailedTrace.intermediate_outputs.strategy_plan && (
                        <div className="border-l-4 border-green-400 pl-3">
                          <h5 className="font-medium text-sm text-green-700">🧠 戦略立案結果</h5>
                          <div className="text-sm text-gray-600 mt-1">
                            <div>アプローチ: <span className="font-mono">{detailedTrace.intermediate_outputs.strategy_plan.primary_approach}</span></div>
                            <div>トーン: <span className="font-mono">{detailedTrace.intermediate_outputs.strategy_plan.tone_setting}</span></div>
                            <div>信頼度: <span className="font-mono">{detailedTrace.intermediate_outputs.strategy_plan.strategy_confidence}</span></div>
                          </div>
                        </div>
                      )}

                      {detailedTrace.intermediate_outputs.evaluation_result && (
                        <div className="border-l-4 border-yellow-400 pl-3">
                          <h5 className="font-medium text-sm text-yellow-700">🔍 内容評価結果</h5>
                          <div className="text-sm text-gray-600 mt-1">
                            <div>評価スコア: <span className="font-mono">{detailedTrace.intermediate_outputs.evaluation_result.quick_score}</span></div>
                            <div>承認推奨: <span className="font-mono">{detailedTrace.intermediate_outputs.evaluation_result.approval_recommendation}</span></div>
                          </div>
                        </div>
                      )}

                      {detailedTrace.intermediate_outputs.patterns_result && (
                        <div className="border-l-4 border-purple-400 pl-3">
                          <h5 className="font-medium text-sm text-purple-700">🎨 パターン生成結果</h5>
                          <div className="text-sm text-gray-600 mt-1">
                            <div>生成パターン数: <span className="font-mono">{Object.keys(detailedTrace.intermediate_outputs.patterns_result).filter(k => k.startsWith('pattern_')).length}個</span></div>
                            <div>パターン種類: 
                              {Object.keys(detailedTrace.intermediate_outputs.patterns_result)
                                .filter(k => k.startsWith('pattern_'))
                                .map(k => detailedTrace.intermediate_outputs.patterns_result[k]?.approach)
                                .join(', ')}
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* 自動交渉システム設定 */}
        <div className="mt-8">
          <AutomationOrchestrator 
            onMonitoringChange={handleMonitoringChange}
          />
        </div>
            </div>
          </main>
        </div>
      </ErrorBoundary>
    </AuthGuard>
  );
}

export default function MessagesPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center">読み込み中...</div>}>
      <MessagesPageContent />
    </Suspense>
  );
}