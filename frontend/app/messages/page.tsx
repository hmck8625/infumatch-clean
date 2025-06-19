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

  // 4段階のシンプルステップ定義
  const PROCESSING_STAGES = [
    { 
      number: 1, 
      name: '📊 スレッド分析', 
      description: 'メッセージ履歴を分析し、現在の交渉状況を把握しています',
      progressTarget: 25
    },
    { 
      number: 2, 
      name: '🧠 戦略立案', 
      description: 'カスタム指示と企業設定を考慮して返信戦略を立案しています',
      progressTarget: 50
    },
    { 
      number: 3, 
      name: '🔍 内容評価', 
      description: '戦略内容の適切性を評価し、リスク要因をチェックしています',
      progressTarget: 75
    },
    { 
      number: 4, 
      name: '🎨 パターン生成', 
      description: '3つの異なるアプローチで返信パターンを生成しています',
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
      let apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://infumatch-backend-fuwvv3ux7q-an.a.run.app';
      
      // 最新のオーケストレーションシステムURLに更新
      if (apiUrl.includes('hackathon-backend-462905-269567634217') || 
          apiUrl.includes('infumatch-orchestration-269567634217') ||
          apiUrl.includes('infumatch-backend-fuwvv3ux7q-an.a.run.app')) {
        console.warn('⚠️ 古いAPI URLが検出されました。最新の4エージェントシステムURLに修正します。');
        apiUrl = 'https://infumatch-backend-269567634217.asia-northeast1.run.app';
      }
      
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
          companySettings = settingsData.settings || {};
          console.log('🏢 企業設定を取得:', companySettings);
          
          // 設定の詳細をログ出力
          const companyInfo = companySettings.companyInfo || {};
          const products = companySettings.products || [];
          const negotiationSettings = companySettings.negotiationSettings || {};
          
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
        requestData.context.company_settings.companyInfo.companyName = companyInfo.companyName || "InfuMatch";
        requestData.context.company_settings.companyInfo.contactPerson = companyInfo.contactPerson || "田中美咲";
        requestData.context.company_settings.companyInfo.email = companyInfo.email || "tanaka@infumatch.com";
        
        if (companySettings.products && companySettings.products.length > 0) {
          requestData.context.company_settings.products = companySettings.products;
        }
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
        
        // AIが既に完成した返信を生成しているかチェック
        const isCompleteReply = baseReply.includes('田中') || baseReply.includes('InfuMatch') || baseReply.length > 100;
        console.log(`🤖 AI返信判定: ${isCompleteReply ? '完成版' : '部分版'} (長さ: ${baseReply.length}文字)`);
        
        // 基本的な分析結果を取得
        const basicMetadata = result.metadata || {};
        console.log('🔍 交渉エージェント分析結果:', basicMetadata);
        
        // 基本的な戦略情報をUI用に整形
        if (basicMetadata.relationship_stage) {
          console.log(`📊 交渉段階: ${basicMetadata.relationship_stage}`);
          console.log(`🎯 エージェント: ${basicMetadata.agent || 'NegotiationAgent'}`);
        }
        
        // 将来の高度な分析のためのプレースホルダー
        console.log('💡 高度な分析機能は次回のバックエンドデプロイで利用可能になります');
        
        // 交渉段階を分析
        const negotiationStage = basicMetadata.relationship_stage || 'initial_contact';
        let stageReasoning = '';
        
        switch(negotiationStage) {
          case 'initial_contact':
            stageReasoning = '初回接触段階です。信頼関係構築を重視し、相手の興味を引き出す内容にします';
            break;
          case 'warming_up':
            stageReasoning = 'ウォーミングアップ段階です。具体的な提案に向けて、相手のニーズを探りながら関係を深めます';
            break;
          case 'negotiation':
            stageReasoning = '交渉段階です。価格や条件面での調整を行い、Win-Winの解決策を模索します';
            break;
          case 'closing':
            stageReasoning = 'クロージング段階です。最終確認と次のステップを明確にして、契約に向けて進めます';
            break;
          default:
            stageReasoning = '現在の交渉段階を分析し、適切なアプローチを選択します';
        }
        
        // パターン生成の最終処理
        updateAgentStatus(
          '🎨 パターン最終生成', 
          '3つの異なるコミュニケーションスタイルを作成中...', 
          `${stageReasoning} 協調的・中立・主張的の3パターンを生成しています`,
          4,
          'PatternGenerationAgent',
          0.92
        );
        
        // 多様性を向上させるためのランダム要素を追加
        const currentTime = new Date();
        const variations = {
          greetings: [
            'いつもお世話になっております。',
            'お疲れ様です。',
            'いつもありがとうございます。'
          ],
          closings: [
            'よろしくお願いいたします。',
            'ご検討のほど、よろしくお願いいたします。',
            '何かご不明な点がございましたら、お気軽にお声がけください。'
          ],
          meetings: [
            'お電話やビデオ通話でお話しできればと思います',
            'オンラインミーティングでご相談させていただければと思います',
            'お時間のあるときにお打ち合わせをお願いできればと思います'
          ]
        };
        
        const getRandomItem = (arr: string[]) => arr[Math.floor(Math.random() * arr.length)];
        
        let patterns = [];
        
        if (isCompleteReply) {
          // AIが既に完成した返信を生成している場合は、そのまま使用
          patterns = [
            {
              pattern_type: 'ai_generated_original',
              pattern_name: 'AI生成オリジナル',
              tone: 'AIが分析に基づいて最適化したトーン',
              content: baseReply,
              reasoning: 'AIが文脈とカスタム指示を理解して生成した完成版の返信',
              recommendation_score: 0.95
            },
            {
              pattern_type: 'ai_generated_formal',
              pattern_name: 'AI生成（フォーマル調整）',
              tone: 'AIベース + より丁寧なフォーマル表現',
              content: baseReply.replace(/。/g, 'です。').replace(/です。です。/g, 'です。'),
              reasoning: 'AI生成内容をベースに、より丁寧な表現に微調整',
              recommendation_score: 0.85
            },
            {
              pattern_type: 'ai_generated_concise',
              pattern_name: 'AI生成（簡潔版）',
              tone: 'AIベース + より簡潔な表現',
              content: baseReply.split('\n').filter(line => line.trim().length > 0).slice(0, -1).join('\n') + '\n\n簡潔にご連絡いたします。よろしくお願いいたします。',
              reasoning: 'AI生成内容をベースに、より簡潔で効率的な表現に調整',
              recommendation_score: 0.80
            }
          ];
        } else {
          // AIが部分的な返信を生成している場合は、従来のパターン生成
          patterns = [
            {
              pattern_type: 'friendly_enthusiastic',
              pattern_name: '友好的・積極的',
              tone: '親しみやすく、前向きで協力的なトーン',
              content: `${contact}様

${getRandomItem(variations.greetings)}InfuMatchの田中です。

${baseReply}

ぜひ詳細についてお話しさせていただければと思います！
${getRandomItem(variations.meetings)}が、いかがでしょうか？

お返事お待ちしております。

${getRandomItem(variations.closings)}
田中`,
              reasoning: 'AIが生成した基本内容に、積極的で関係構築を重視するアプローチを追加',
              recommendation_score: 0.85
            },
            {
              pattern_type: 'cautious_professional',
              pattern_name: '慎重・プロフェッショナル',
              tone: '丁寧で専門的、詳細を重視するトーン',
              content: `${contact}様

お忙しい中、ご連絡いただきありがとうございます。
InfuMatchの田中と申します。

${baseReply}

つきましては、以下の点について詳細を確認させていただけますでしょうか。

・プロジェクトの具体的な内容
・ご希望のスケジュール  
・ご予算の範囲

${getRandomItem(variations.closings)}

田中`,
              reasoning: 'AIが生成した基本内容に、リスクを最小限に抑えた慎重なアプローチを追加',
              recommendation_score: 0.75
            },
            {
              pattern_type: 'business_focused',
              pattern_name: 'ビジネス重視・効率的',
              tone: '簡潔で要点を押さえた、効率を重視するトーン',
              content: `${contact}様

${baseReply}

具体的な提案内容と次のステップについて、
近日中に${getRandomItem(variations.meetings)}。

ご都合の良い日時をお聞かせください。

田中（InfuMatch）`,
              reasoning: 'AIが生成した基本内容を簡潔にまとめ、効率的な進行を重視したアプローチ',
              recommendation_score: 0.70
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
        const replySubject = subjectHeader.startsWith('Re:') ? subjectHeader : `Re: ${subjectHeader}`;
        const lastMessageId = lastMessage.id;
        
        // 🔍 DEBUG: 送信するデータの詳細をログ出力
        const sendData = {
          to: fromHeader,
          subject: replySubject,
          message: replyText,
          threadId: currentThread.id,
          replyToMessageId: lastMessageId,
        };
        
        console.log('=== FRONTEND EMAIL SEND DEBUG START ===');
        console.log('📧 Frontend send data:', JSON.stringify(sendData, null, 2));
        console.log('📧 Original subject header:', subjectHeader);
        console.log('📧 Reply subject:', replySubject);
        console.log('📧 From header:', fromHeader);
        console.log('📧 Reply text:', replyText);
        console.log('📧 Thread ID:', currentThread.id);
        console.log('📧 Reply to message ID:', lastMessageId);
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
                      onClick={() => {
                        loadThreads();
                        refreshRealtime();
                        resetNewCount();
                      }}
                      disabled={isLoadingThreads || isRealtimeLoading}
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
                    <div className="flex items-center text-xs text-green-600 ml-auto">
                      <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                      Gmail接続済み
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
                              <div className="flex items-center space-x-1">
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
                        <span>🔍 7段階詳細表示</span>
                        <span className="bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded text-xs">
                          {processingSteps.length}/7完了
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
                                      段階{step.stepNumber}/7
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
                      🤖 AI返信候補を生成
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

export default function MessagesPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center">読み込み中...</div>}>
      <MessagesPageContent />
    </Suspense>
  );
}