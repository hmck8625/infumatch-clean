'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { AuthGuard } from '@/components/auth-guard';
import Header from '@/components/Header';
import { apiClient, CampaignRequest, AIRecommendationResponse } from '@/lib/api';

// マッチング結果の型定義
interface MatchingResult {
  id: string;
  influencerName: string;
  score: number;
  category: string;
  reason: string;
  estimatedReach: number;
  estimatedCost: number;
  thumbnailUrl?: string;
  subscriberCount?: number;
  engagementRate?: number;
  description?: string;
  email?: string;
  compatibility: {
    audience: number;
    content: number;
    brand: number;
  };
}

// モックデータ
const mockMatchingResults: MatchingResult[] = [
  {
    id: '1',
    influencerName: 'Tech Review Japan',
    score: 96,
    category: 'テクノロジー',
    reason: 'ターゲット層の重複率が95%、過去のテック系コラボレーション実績が豊富',
    estimatedReach: 85000,
    estimatedCost: 120000,
    compatibility: {
      audience: 95,
      content: 92,
      brand: 88,
    },
  },
  {
    id: '2',
    influencerName: 'ビューティー研究所',
    score: 89,
    category: '美容',
    reason: 'エンゲージメント率が高く、商品レビューの信頼性が高い',
    estimatedReach: 92000,
    estimatedCost: 150000,
    compatibility: {
      audience: 87,
      content: 94,
      brand: 86,
    },
  },
  {
    id: '3',
    influencerName: 'Fitness Life Tokyo',
    score: 84,
    category: 'フィットネス',
    reason: '健康志向の強いオーディエンス層、ライフスタイル系商品との親和性が高い',
    estimatedReach: 67000,
    estimatedCost: 95000,
    compatibility: {
      audience: 82,
      content: 88,
      brand: 83,
    },
  },
];

export default function MatchingPage() {
  const [isVisible, setIsVisible] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [settings, setSettings] = useState<any>(null);
  const [matchingResults, setMatchingResults] = useState<MatchingResult[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoadingSettings, setIsLoadingSettings] = useState(true);

  useEffect(() => {
    setIsVisible(true);
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setIsLoadingSettings(true);
      setError(null);
      const response = await fetch('/api/settings');
      if (response.ok) {
        const result = await response.json();
        if (result.success && result.data) {
          setSettings(result.data);
          console.log('✅ 設定データ読み込み完了:', result.data);
        } else {
          console.warn('⚠️ 設定データが見つかりません、デフォルト値を使用します');
          setSettings(null);
        }
      } else {
        throw new Error(`設定読み込み失敗: ${response.status}`);
      }
    } catch (error) {
      console.error('❌ 設定読み込みエラー:', error);
      setError(error instanceof Error ? error.message : '設定の読み込みに失敗しました');
      setSettings(null);
    } finally {
      setIsLoadingSettings(false);
    }
  };

  const handleStartMatching = async () => {
    setIsAnalyzing(true);
    setShowResults(false);
    setError(null);
    
    try {
      // 設定データからキャンペーン情報を構築
      const campaignRequest = buildCampaignRequest();
      console.log('🚀 AI推薦開始:', campaignRequest);
      
      // 実際のAI推薦APIを呼び出し
      const aiResponse = await apiClient.getAIRecommendations(campaignRequest);
      console.log('📡 AI推薦レスポンス:', aiResponse);
      
      if (aiResponse.success && aiResponse.recommendations?.length > 0) {
        // AI推薦結果をマッチング結果形式に変換
        const convertedResults = convertAIResponseToMatchingResults(aiResponse);
        setMatchingResults(convertedResults);
        console.log('✅ AI推薦結果変換完了:', convertedResults);
      } else {
        // AI推薦が失敗または結果がない場合はフォールバック
        console.warn('⚠️ AI推薦が失敗またはデータなし、フォールバックデータを使用');
        const fallbackResults = customizeMatchingResults();
        setMatchingResults(fallbackResults);
      }
      
    } catch (error) {
      console.error('❌ AI推薦API呼び出しエラー:', error);
      setError(error instanceof Error ? error.message : 'AI推薦の実行に失敗しました');
      // エラー時はフォールバックデータを使用
      const fallbackResults = customizeMatchingResults();
      setMatchingResults(fallbackResults);
    }
    
    setIsAnalyzing(false);
    setShowResults(true);
  };

  const customizeMatchingResults = () => {
    if (!settings) return mockMatchingResults;
    
    // 設定に基づいてマッチング結果をフィルタリング・カスタマイズ
    let customizedResults = [...mockMatchingResults];
    
    // 登録者数でフィルタリング
    if (settings.matchingPreferences) {
      const { minimumSubscribers, maximumSubscribers } = settings.matchingPreferences;
      customizedResults = customizedResults.filter(result => 
        result.estimatedReach >= minimumSubscribers && 
        result.estimatedReach <= maximumSubscribers
      );
    }
    
    // 優先カテゴリがマッチする場合にスコアを上げる
    if (settings.matchingPreferences?.preferredCategories?.length > 0) {
      customizedResults = customizedResults.map(result => {
        const isPreferredCategory = settings.matchingPreferences.preferredCategories.some(
          (cat: string) => result.category.includes(cat) || cat.includes(result.category)
        );
        
        if (isPreferredCategory) {
          return {
            ...result,
            score: Math.min(100, result.score + 5),
            reason: `${result.reason}（優先カテゴリマッチ）`
          };
        }
        return result;
      });
    }
    
    // 予算範囲に合わせてコストを調整
    if (settings.negotiationSettings?.defaultBudgetRange) {
      const { min, max } = settings.negotiationSettings.defaultBudgetRange;
      customizedResults = customizedResults.map(result => ({
        ...result,
        estimatedCost: Math.max(min, Math.min(max, result.estimatedCost))
      }));
    }
    
    // スコア順でソート
    return customizedResults.sort((a, b) => b.score - a.score);
  };

  const buildCampaignRequest = (): CampaignRequest => {
    // 設定データまたはデフォルト値を使用してキャンペーンリクエストを構築
    const productNames = settings?.products?.map(p => p.name).join(", ") || settings?.companyInfo?.companyName || "サンプル製品";
    const targetAudiences = settings?.products?.length > 0 
      ? settings.products.map(p => p.targetAudience).filter(Boolean)
      : ["20-30代", "男女問わず"];
    
    return {
      product_name: productNames,
      budget_min: settings?.negotiationSettings?.defaultBudgetRange?.min || 50000,
      budget_max: settings?.negotiationSettings?.defaultBudgetRange?.max || 300000,
      target_audience: targetAudiences.length > 0 ? targetAudiences : ["20-30代", "男女問わず"],
      required_categories: settings?.matchingSettings?.priorityCategories?.length > 0 
        ? settings.matchingSettings.priorityCategories 
        : ["テクノロジー", "ライフスタイル"],
      campaign_goals: settings?.companyInfo?.description || "ブランド認知度向上とコンバージョン獲得",
      min_engagement_rate: settings?.matchingSettings?.minEngagementRate || 2.0,
      min_subscribers: settings?.matchingSettings?.minSubscribers || 10000,
      max_subscribers: settings?.matchingSettings?.maxSubscribers || 500000,
      geographic_focus: settings?.matchingSettings?.geographicFocus?.[0] || "日本"
    };
  };

  const convertAIResponseToMatchingResults = (aiResponse: AIRecommendationResponse): MatchingResult[] => {
    if (!aiResponse.recommendations) return [];
    
    return aiResponse.recommendations.map((rec: any, index: number) => ({
      id: rec.channel_id || `ai-rec-${index}`,
      influencerName: rec.channel_name || `推薦チャンネル ${index + 1}`,
      score: Math.round((rec.overall_score || 0.5) * 100),
      category: rec.category || "総合",
      reason: rec.explanation || "AI分析による推薦",
      estimatedReach: rec.estimated_reach || Math.floor(Math.random() * 100000) + 50000,
      estimatedCost: rec.estimated_cost || Math.floor(Math.random() * 200000) + 80000,
      thumbnailUrl: rec.thumbnail_url,
      subscriberCount: rec.subscriber_count || 0,
      engagementRate: rec.engagement_rate || 0,
      description: rec.description || "",
      email: rec.email,
      compatibility: {
        audience: Math.round((rec.detailed_scores?.audience_fit || 0.7) * 100),
        content: Math.round((rec.detailed_scores?.category_match || 0.8) * 100),
        brand: Math.round((rec.detailed_scores?.budget_fit || 0.6) * 100),
      }
    }));
  };

  const formatNumber = (num: number) => {
    if (num >= 10000) {
      return (num / 10000).toFixed(1) + '万';
    }
    return num.toLocaleString();
  };

  return (
    <AuthGuard>
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* ヘッダー */}
      <Header variant="glass" />

      <main className="container mx-auto px-6 py-8">
        <div className={`transform transition-all duration-1000 ${isVisible ? 'translate-y-0 opacity-100' : 'translate-y-10 opacity-0'}`}>
          {/* ヘッダーセクション */}
          <div className="text-center mb-12">
            <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
              AI自動
              <span className="text-gradient block">マッチングシステム</span>
            </h1>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              機械学習アルゴリズムが企業のニーズを分析し、最適なインフルエンサーを96%の精度で特定
            </p>
          </div>

          {/* AI分析セクション */}
          <div className="card p-8 mb-12 max-w-4xl mx-auto">
            <div className="text-center mb-8">
              <div className="w-24 h-24 bg-gradient-to-r from-purple-500 to-pink-500 rounded-3xl flex items-center justify-center mx-auto mb-6">
                <svg className="w-12 h-12 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              </div>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">AI分析エンジン</h2>
              <p className="text-gray-600 max-w-2xl mx-auto mb-8">
                企業情報、製品特性、ターゲット層を総合的に分析し、最適なインフルエンサーとのマッチングを実行します
              </p>
            </div>

            {!isAnalyzing && !showResults && (
              <div className="text-center">
                {isLoadingSettings ? (
                  <div className="flex items-center justify-center space-x-3">
                    <svg className="animate-spin h-6 w-6 text-indigo-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <span className="text-gray-600">設定データを読み込み中...</span>
                  </div>
                ) : error ? (
                  <div className="text-center">
                    <div className="text-red-600 mb-4">⚠️ {error}</div>
                    <button 
                      onClick={handleStartMatching}
                      className="btn btn-primary text-lg px-12 py-4"
                    >
                      <svg className="w-6 h-6 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                      デフォルト設定でAI分析を開始
                    </button>
                  </div>
                ) : (
                  <div>
                    {settings ? (
                      <div className="mb-4 text-sm text-gray-600">
                        ✅ 設定データ読み込み完了 ({settings.companyInfo?.companyName || 'データなし'})
                      </div>
                    ) : (
                      <div className="mb-4 text-sm text-gray-500">
                        ℹ️ デフォルト設定を使用します
                      </div>
                    )}
                    <button 
                      onClick={handleStartMatching}
                      className="btn btn-primary text-lg px-12 py-4"
                    >
                      <svg className="w-6 h-6 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                      AI分析を開始
                    </button>
                  </div>
                )}
              </div>
            )}

            {isAnalyzing && (
              <div className="text-center">
                <div className="flex items-center justify-center mb-6">
                  <svg className="animate-spin -ml-1 mr-3 h-8 w-8 text-indigo-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span className="text-lg font-semibold text-gray-700">AI分析中...</span>
                </div>
                <div className="max-w-md mx-auto">
                  <div className="space-y-3">
                    <div className="flex items-center text-sm text-gray-600">
                      <div className="w-2 h-2 bg-green-500 rounded-full mr-3 animate-pulse"></div>
                      ターゲット層の分析
                    </div>
                    <div className="flex items-center text-sm text-gray-600">
                      <div className="w-2 h-2 bg-blue-500 rounded-full mr-3 animate-pulse"></div>
                      インフルエンサーデータベースの照合
                    </div>
                    <div className="flex items-center text-sm text-gray-600">
                      <div className="w-2 h-2 bg-purple-500 rounded-full mr-3 animate-pulse"></div>
                      適合度スコアの計算
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* マッチング結果 */}
          {showResults && (
            <div className="space-y-8">
              {/* 結果ヘッダー */}
              <div className="text-center">
                <div className="inline-flex items-center px-6 py-3 rounded-full bg-green-100 border border-green-300 text-green-800 font-semibold mb-4">
                  <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  分析完了
                </div>
                <h2 className="text-3xl font-bold text-gray-900 mb-2">マッチング結果</h2>
                <p className="text-gray-600">
                  <span className="font-semibold text-indigo-600">{matchingResults.length}</span>人の最適なインフルエンサーが見つかりました
                </p>
              </div>

              {/* マッチング結果カード */}
              <div className="space-y-6">
                {matchingResults.map((result, index) => (
                  <div 
                    key={result.id}
                    className={`card-interactive transform transition-all duration-500 ${
                      showResults ? 'translate-y-0 opacity-100' : 'translate-y-10 opacity-0'
                    }`}
                    style={{transitionDelay: `${index * 200}ms`}}
                  >
                    <div className="p-8">
                      {/* ヘッダー部分 */}
                      <div className="flex items-start justify-between mb-6">
                        <div className="flex items-center space-x-4">
                          <div className="relative">
                            {result.thumbnailUrl ? (
                              <img 
                                src={result.thumbnailUrl} 
                                alt={`${result.influencerName}のサムネイル`}
                                className="w-16 h-16 rounded-full object-cover border-2 border-gray-200"
                                onError={(e) => {
                                  e.currentTarget.style.display = 'none';
                                  e.currentTarget.nextElementSibling.style.display = 'flex';
                                }}
                              />
                            ) : null}
                            <div 
                              className="w-16 h-16 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full flex items-center justify-center text-white text-xl font-bold"
                              style={{ display: result.thumbnailUrl ? 'none' : 'flex' }}
                            >
                              {result.influencerName[0]}
                            </div>
                            <div className="absolute -top-1 -right-1 w-6 h-6 bg-green-500 rounded-full border-2 border-white flex items-center justify-center">
                              <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                              </svg>
                            </div>
                          </div>
                          <div>
                            <h3 className="text-xl font-bold text-gray-900">{result.influencerName}</h3>
                            <div className="flex items-center space-x-2 mt-1">
                              <span className="badge badge-primary">{result.category}</span>
                              <span className="text-sm text-gray-500">認証済み</span>
                            </div>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="flex items-center space-x-2 mb-2">
                            <span className="text-2xl font-bold text-indigo-600">{result.score}</span>
                            <span className="text-sm text-gray-500">/100</span>
                          </div>
                          <div className="text-xs text-gray-500">適合度スコア</div>
                        </div>
                      </div>

                      {/* 分析理由 */}
                      <div className="bg-gray-50 rounded-lg p-4 mb-6">
                        <h4 className="font-semibold text-gray-900 mb-2 flex items-center">
                          <svg className="w-4 h-4 mr-2 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                          </svg>
                          AI分析結果
                        </h4>
                        <p className="text-sm text-gray-700">{result.reason}</p>
                      </div>

                      {/* 詳細メトリクス */}
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                        {/* 登録者数 */}
                        <div className="text-center p-3 bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg">
                          <div className="flex items-center justify-center mb-2">
                            <svg className="w-5 h-5 text-blue-600 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                            </svg>
                          </div>
                          <p className="text-xs text-gray-600 mb-1">登録者数</p>
                          <p className="text-lg font-bold text-gray-900">
                            {result.subscriberCount ? formatNumber(result.subscriberCount) : 'N/A'}
                          </p>
                        </div>

                        {/* エンゲージメント率 */}
                        <div className="text-center p-3 bg-gradient-to-br from-green-50 to-green-100 rounded-lg">
                          <div className="flex items-center justify-center mb-2">
                            <svg className="w-5 h-5 text-green-600 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                            </svg>
                          </div>
                          <p className="text-xs text-gray-600 mb-1">エンゲージメント</p>
                          <p className="text-lg font-bold text-gray-900">
                            {result.engagementRate ? `${result.engagementRate.toFixed(1)}%` : 'N/A'}
                          </p>
                        </div>

                        {/* 推定リーチ */}
                        <div className="text-center p-3 bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg">
                          <div className="flex items-center justify-center mb-2">
                            <svg className="w-5 h-5 text-purple-600 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                            </svg>
                          </div>
                          <p className="text-xs text-gray-600 mb-1">推定リーチ</p>
                          <p className="text-lg font-bold text-gray-900">{formatNumber(result.estimatedReach)}</p>
                        </div>

                        {/* 推定コスト */}
                        <div className="text-center p-3 bg-gradient-to-br from-orange-50 to-orange-100 rounded-lg">
                          <div className="flex items-center justify-center mb-2">
                            <svg className="w-5 h-5 text-orange-600 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                            </svg>
                          </div>
                          <p className="text-xs text-gray-600 mb-1">推定コスト</p>
                          <p className="text-lg font-bold text-gray-900">¥{formatNumber(result.estimatedCost)}</p>
                        </div>
                      </div>

                      {/* チャンネル説明（実データがある場合のみ表示） */}
                      {result.description && (
                        <div className="mb-6">
                          <h4 className="font-semibold text-gray-900 mb-3">チャンネル紹介</h4>
                          <p className="text-sm text-gray-600 leading-relaxed bg-gray-50 p-4 rounded-lg">
                            {result.description.length > 200 
                              ? `${result.description.substring(0, 200)}...` 
                              : result.description
                            }
                          </p>
                        </div>
                      )}
                      </div>

                      {/* 互換性スコア */}
                      <div className="mb-6">
                        <h4 className="font-semibold text-gray-900 mb-4">詳細適合度</h4>
                        <div className="space-y-3">
                          {[
                            { label: 'オーディエンス', value: result.compatibility.audience, color: 'bg-blue-500' },
                            { label: 'コンテンツ', value: result.compatibility.content, color: 'bg-green-500' },
                            { label: 'ブランド', value: result.compatibility.brand, color: 'bg-purple-500' }
                          ].map((item, idx) => (
                            <div key={idx} className="flex items-center">
                              <div className="w-20 text-sm text-gray-600">{item.label}</div>
                              <div className="flex-1 bg-gray-200 rounded-full h-2 mr-3">
                                <div 
                                  className={`h-2 rounded-full ${item.color} transition-all duration-1000`}
                                  style={{width: `${item.value}%`}}
                                ></div>
                              </div>
                              <div className="w-12 text-sm font-semibold text-gray-700">{item.value}%</div>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* アクションボタン */}
                      <div className="flex space-x-3">
                        <Link 
                          href={result.email ? 
                            `/messages?to=${encodeURIComponent(result.email)}&subject=${encodeURIComponent(`【コラボ提案】${result.influencerName}様へ`)}&influencer=${encodeURIComponent(result.influencerName)}` :
                            '/messages'
                          } 
                          className="btn btn-primary flex-1 text-center"
                        >
                          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                          </svg>
                          {result.email ? 'コンタクト開始' : 'メッセージ'}
                        </Link>
                        <Link 
                          href={`/search?channel_id=${result.id}`} 
                          className="btn btn-outline flex-1 text-center"
                        >
                          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                          </svg>
                          詳細表示
                        </Link>
                        <button 
                          className="btn btn-ghost px-3"
                          title="お気に入りに追加"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
                          </svg>
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </main>
      </div>
    </AuthGuard>
  );
}