'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { searchInfluencers, getAIRecommendations, generateCollaborationProposal, Influencer, APIError, CampaignRequest, AIRecommendationResponse } from '@/lib/api';
import Header from '@/components/Header';
import { 
  Search, 
  Filter, 
  Users, 
  Eye, 
  Play, 
  TrendingUp, 
  Mail, 
  MailCheck,
  MailX,
  Info,
  X,
  ExternalLink,
  Globe,
  Calendar,
  BarChart3,
  Shield,
  Star,
  Target,
  Sparkles,
  SearchCheck,
  TrendingUp as TrendingUpIcon,
  AlertTriangle,
  MessageCircle,
  BarChart
} from 'lucide-react';

// アイコン配列を定義
const AVATAR_ICONS = [
  '👤', '🎮', '🍳', '💄', '🏃‍♂️', '📱', '🎯', '🌟', 
  '🎨', '📚', '🎵', '🎬', '⚡', '🚀', '💎', '🔥',
  '🌸', '🌺', '🌻', '🌹', '🦄', '🐱', '🐶', '🦊'
];

// カテゴリー別アイコンマッピング
const getCategoryIcon = (category: string): string => {
  const categoryMap: Record<string, string> = {
    'gaming': '🎮',
    'ゲーム': '🎮',
    'テクノロジー': '📱',
    'tech': '📱',
    '料理': '🍳',
    '料理・グルメ': '🍳',
    'cooking': '🍳',
    '美容': '💄',
    '美容・コスメ': '💄',
    'beauty': '💄',
    'フィットネス': '🏃‍♂️',
    'fitness': '🏃‍♂️',
    'ライフスタイル': '🌟',
    'lifestyle': '🌟',
    '教育': '📚',
    'education': '📚',
    'ハウツー＆スタイル': '🎨',
    'howto': '🎨'
  };
  
  return categoryMap[category.toLowerCase()] || AVATAR_ICONS[Math.floor(Math.random() * AVATAR_ICONS.length)];
};

// 詳細表示モーダル
function InfluencerDetailModal({ 
  influencer, 
  isOpen, 
  onClose, 
  onCollaborationProposal,
  isGeneratingProposal 
}: {
  influencer: Influencer | null;
  isOpen: boolean;
  onClose: () => void;
  onCollaborationProposal: (influencer: Influencer) => void;
  isGeneratingProposal: boolean;
}) {
  if (!isOpen || !influencer) return null;

  const hasEmail = influencer.email && influencer.email !== 'null' && influencer.email.trim() !== '';
  const categoryIcon = getCategoryIcon(influencer.category);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl p-8 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* ヘッダー */}
        <div className="flex items-start justify-between mb-6">
          <div className="flex items-start space-x-4">
            <div className="relative">
              {influencer.thumbnailUrl ? (
                <img 
                  src={influencer.thumbnailUrl} 
                  alt={`${influencer.name}のサムネイル`}
                  className="w-20 h-20 rounded-full object-cover border-2 border-gray-200"
                  onError={(e) => {
                    e.currentTarget.style.display = 'none';
                    e.currentTarget.nextElementSibling.style.display = 'flex';
                  }}
                />
              ) : null}
              <div 
                className="w-20 h-20 rounded-full bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center text-3xl"
                style={{ display: influencer.thumbnailUrl ? 'none' : 'flex' }}
              >
                {categoryIcon}
              </div>
              <div className="absolute -bottom-1 -right-1">
                {hasEmail ? (
                  <div className="bg-green-500 rounded-full p-1.5">
                    <MailCheck className="w-4 h-4 text-white" />
                  </div>
                ) : (
                  <div className="bg-gray-400 rounded-full p-1.5">
                    <MailX className="w-4 h-4 text-white" />
                  </div>
                )}
              </div>
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">{influencer.name}</h2>
              <div className="flex items-center space-x-2 mb-2">
                <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-purple-100 text-purple-800">
                  {categoryIcon} {influencer.category}
                </span>
              </div>
              {hasEmail && (
                <div className="flex items-center text-sm text-green-600">
                  <Mail className="w-4 h-4 mr-1" />
                  連絡可能
                </div>
              )}
            </div>
          </div>
          <button 
            onClick={onClose} 
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
          >
            <X className="w-6 h-6 text-gray-400" />
          </button>
        </div>

        {/* 統計情報 */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="text-center p-4 bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl">
            <Users className="w-6 h-6 text-purple-600 mx-auto mb-2" />
            <div className="text-lg font-bold text-gray-900">
              {influencer.subscriberCount ? influencer.subscriberCount.toLocaleString() : 'N/A'}
            </div>
            <div className="text-xs text-gray-600">登録者数</div>
          </div>
          
          <div className="text-center p-4 bg-gradient-to-br from-green-50 to-green-100 rounded-xl">
            <TrendingUp className="w-6 h-6 text-green-600 mx-auto mb-2" />
            <div className="text-lg font-bold text-gray-900">
              {influencer.engagementRate ? `${influencer.engagementRate.toFixed(1)}%` : 'N/A'}
            </div>
            <div className="text-xs text-gray-600">エンゲージメント率</div>
          </div>
          
          <div className="text-center p-4 bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl">
            <Play className="w-6 h-6 text-blue-600 mx-auto mb-2" />
            <div className="text-lg font-bold text-gray-900">
              {influencer.videoCount ? influencer.videoCount.toLocaleString() : 'N/A'}
            </div>
            <div className="text-xs text-gray-600">動画数</div>
          </div>
          
          <div className="text-center p-4 bg-gradient-to-br from-orange-50 to-orange-100 rounded-xl">
            <Eye className="w-6 h-6 text-orange-600 mx-auto mb-2" />
            <div className="text-lg font-bold text-gray-900">
              {influencer.viewCount ? (influencer.viewCount / 1000000).toFixed(1) + 'M' : 'N/A'}
            </div>
            <div className="text-xs text-gray-600">総再生回数</div>
          </div>
        </div>

        {/* 説明 */}
        {influencer.description && (
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">チャンネル紹介</h3>
            <p className="text-gray-600 leading-relaxed bg-gray-50 p-4 rounded-xl">
              {influencer.description}
            </p>
          </div>
        )}

        {/* アクションボタン */}
        <div className="flex space-x-3">
          <button 
            onClick={onClose} 
            className="flex-1 px-6 py-3 bg-gray-100 text-gray-700 rounded-xl font-medium hover:bg-gray-200 transition-colors"
          >
            閉じる
          </button>
          <button 
            onClick={() => onCollaborationProposal(influencer)}
            disabled={isGeneratingProposal || !hasEmail}
            className="flex-1 flex items-center justify-center space-x-2 px-6 py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-xl font-medium hover:from-purple-700 hover:to-blue-700 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
            title={!hasEmail ? 'メールアドレスが未登録です' : ''}
          >
            {isGeneratingProposal ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent" />
                <span>生成中...</span>
              </>
            ) : (
              <>
                <MessageCircle className="w-5 h-5" />
                <span>コラボ提案</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function SearchPage() {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [minSubscribers, setMinSubscribers] = useState('');
  const [maxSubscribers, setMaxSubscribers] = useState('');
  const [hasEmailFilter, setHasEmailFilter] = useState(false);
  const [allInfluencers, setAllInfluencers] = useState<Influencer[]>([]);
  const [filteredResults, setFilteredResults] = useState<Influencer[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [isVisible, setIsVisible] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);
  const [useAI, setUseAI] = useState(false);
  const [aiResults, setAiResults] = useState<AIRecommendationResponse | null>(null);
  
  // 詳細モーダル用の状態
  const [selectedInfluencer, setSelectedInfluencer] = useState<Influencer | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  
  // コラボ提案用の状態
  const [isGeneratingProposal, setIsGeneratingProposal] = useState(false);
  
  // AI推薦用の追加フィールド
  const [productName, setProductName] = useState('');
  const [budgetMin, setBudgetMin] = useState('');
  const [budgetMax, setBudgetMax] = useState('');
  const [targetAudience, setTargetAudience] = useState('');
  const [campaignGoals, setCampaignGoals] = useState('');

  useEffect(() => {
    setIsVisible(true);
    // 初期ロード時に全インフルエンサーを取得
    handleInitialLoad();
  }, []);

  // filteredResults の変化を監視
  useEffect(() => {
    console.log('[useEffect] filteredResults changed:', {
      length: filteredResults?.length,
      isArray: Array.isArray(filteredResults),
      firstItem: filteredResults?.[0]
    });
  }, [filteredResults]);

  // 検索条件変更時のリアルタイムフィルタリング
  useEffect(() => {
    if (allInfluencers.length > 0 && !useAI) {
      const filtered = filterInfluencers(allInfluencers);
      setFilteredResults(filtered);
      console.log('[useEffect] Auto-filtered to', filtered.length, 'results');
    }
  }, [searchQuery, selectedCategory, minSubscribers, maxSubscribers, hasEmailFilter, allInfluencers, useAI]);

  const handleInitialLoad = async () => {
    try {
      setIsSearching(true);
      setError(null);
      
      console.log('[handleInitialLoad] Calling searchInfluencers...');
      const results = await searchInfluencers({});
      console.log('[handleInitialLoad] Search results:', results);
      
      if (results && Array.isArray(results) && results.length > 0) {
        console.log('[handleInitialLoad] Setting allInfluencers with:', results.length, 'items');
        setAllInfluencers(results);
        setFilteredResults(results); // 初期表示は全データ
      } else {
        console.error('[handleInitialLoad] Invalid results received:', results);
        setError('取得したデータが無効です');
      }
      setHasSearched(true);
    } catch (err) {
      console.error('Initial load failed:', err);
      if (err instanceof APIError) {
        setError(`APIエラー: ${err.message}`);
      } else if (err instanceof Error) {
        setError(`エラー: ${err.message}`);
      } else {
        setError('データの読み込みに失敗しました');
      }
      setHasSearched(true);
    } finally {
      setIsSearching(false);
    }
  };

  const categories = ['all', 'gaming', 'ゲーム', 'テクノロジー', '料理', '料理・グルメ', 'フィットネス', '美容', '美容・コスメ', 'ライフスタイル', '教育', 'ハウツー＆スタイル'];

  // クライアントサイドフィルタリング関数
  const filterInfluencers = (influencers: Influencer[]) => {
    return influencers.filter(influencer => {
      // キーワード検索（名前、説明文、カテゴリ）
      const keyword = searchQuery.trim().toLowerCase();
      const matchesKeyword = !keyword || 
        influencer.name.toLowerCase().includes(keyword) ||
        influencer.description.toLowerCase().includes(keyword) ||
        influencer.category.toLowerCase().includes(keyword);

      // カテゴリフィルタ
      const matchesCategory = selectedCategory === 'all' || 
        influencer.category === selectedCategory ||
        (selectedCategory === 'gaming' && influencer.category === 'ゲーム') ||
        (selectedCategory === 'ゲーム' && influencer.category === 'gaming');

      // 登録者数フィルタ
      const minSubs = minSubscribers ? parseInt(minSubscribers) : 0;
      const maxSubs = maxSubscribers ? parseInt(maxSubscribers) : Infinity;
      const matchesSubscribers = influencer.subscriberCount >= minSubs && 
        influencer.subscriberCount <= maxSubs;

      // メールアドレスフィルタ
      const hasEmail = influencer.email && influencer.email !== 'null' && influencer.email.trim() !== '';
      const matchesEmail = !hasEmailFilter || hasEmail;

      return matchesKeyword && matchesCategory && matchesSubscribers && matchesEmail;
    });
  };

  const handleSearch = async () => {
    try {
      setIsSearching(true);
      setError(null);
      
      if (useAI) {
        // AI推薦の場合は /matching ページにリダイレクト
        console.log('[handleSearch] AI推薦実行 - /matchingページに遷移');
        router.push('/matching');
        return;
      } else {
        // クライアントサイドフィルタリングを実行
        console.log('[handleSearch] Applying filters to', allInfluencers.length, 'influencers');
        const filtered = filterInfluencers(allInfluencers);
        console.log('[handleSearch] Filtered results:', filtered.length, 'items');
        
        setFilteredResults(filtered);
        setAiResults(null);
      }
      
      setHasSearched(true);
    } catch (err) {
      if (err instanceof APIError) {
        setError(`検索エラー: ${err.message}`);
      } else {
        setError('検索中にエラーが発生しました');
      }
      console.error('Search failed:', err);
    } finally {
      setIsSearching(false);
    }
  };

  const openModal = (influencer: Influencer) => {
    setSelectedInfluencer(influencer);
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setSelectedInfluencer(null);
  };

  const handleCollaborationProposal = async (influencer: Influencer) => {
    try {
      setIsGeneratingProposal(true);
      
      // ユーザー設定を取得 (settings APIから)
      let userSettings = {};
      try {
        const response = await fetch('/api/settings');
        if (response.ok) {
          const data = await response.json();
          userSettings = data.settings || {};
        }
      } catch (err) {
        console.warn('Settings fetch failed, using defaults:', err);
      }
      
      // AI交渉エージェントを使用してメッセージ生成
      const proposalResponse = await generateCollaborationProposal(influencer, userSettings);
      
      if (proposalResponse.success) {
        // URLエンコードしてメッセージページに遷移
        const encodedMessage = encodeURIComponent(proposalResponse.message);
        const encodedSubject = encodeURIComponent(`【コラボレーションのご提案】${influencer.name}様へ`);
        const recipientEmail = influencer.email || '';
        
        // メッセージページにパラメータ付きで遷移
        router.push(`/messages?to=${encodeURIComponent(recipientEmail)}&subject=${encodedSubject}&body=${encodedMessage}&influencer=${encodeURIComponent(influencer.name)}`);
      } else {
        setError('コラボ提案メッセージの生成に失敗しました');
      }
    } catch (err) {
      console.error('Collaboration proposal error:', err);
      setError('コラボ提案メッセージの生成中にエラーが発生しました');
    } finally {
      setIsGeneratingProposal(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      <Header />
      
      <div className="container mx-auto px-6 py-8">
        {/* メインヘッダー */}
        <div className="bg-white rounded-2xl shadow-lg p-8 mb-8">
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent mb-4">
              インフルエンサー検索
            </h1>
            <p className="text-gray-600 text-lg">YouTubeインフルエンサーを簡単に検索・フィルタリング</p>
            <div className="flex items-center justify-center mt-4 space-x-4">
              <div className="flex items-center text-sm text-gray-500">
                <Users className="w-4 h-4 mr-1" />
                {allInfluencers.length} 人のインフルエンサー
              </div>
              {hasSearched && (
                <div className="flex items-center text-sm text-purple-600">
                  <SearchCheck className="w-4 h-4 mr-1" />
                  {filteredResults.length} 件の結果
                </div>
              )}
            </div>
          </div>

          {/* 検索フォーム */}
          <div className="space-y-6">
            {/* キーワード検索 */}
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Search className="h-5 w-5 text-gray-400" />
              </div>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="インフルエンサー名、カテゴリ、キーワードで検索..."
                className="w-full pl-10 pr-4 py-4 border border-gray-200 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all duration-200 text-lg"
              />
            </div>

            {/* フィルターオプション */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* カテゴリフィルタ */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <Filter className="w-4 h-4 inline mr-1" />
                  カテゴリ
                </label>
                <select
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                >
                  <option value="all">すべてのカテゴリ</option>
                  {categories.filter(cat => cat !== 'all').map(category => (
                    <option key={category} value={category}>{category}</option>
                  ))}
                </select>
              </div>

              {/* 登録者数フィルタ */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <TrendingUp className="w-4 h-4 inline mr-1" />
                  最小登録者数
                </label>
                <input
                  type="number"
                  value={minSubscribers}
                  onChange={(e) => setMinSubscribers(e.target.value)}
                  placeholder="例: 10000"
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <BarChart3 className="w-4 h-4 inline mr-1" />
                  最大登録者数
                </label>
                <input
                  type="number"
                  value={maxSubscribers}
                  onChange={(e) => setMaxSubscribers(e.target.value)}
                  placeholder="例: 1000000"
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>

              {/* メールフィルタ */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <Mail className="w-4 h-4 inline mr-1" />
                  連絡先フィルタ
                </label>
                <div className="flex items-center space-x-3 pt-2">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={hasEmailFilter}
                      onChange={(e) => setHasEmailFilter(e.target.checked)}
                      className="rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">メールありのみ</span>
                  </label>
                </div>
              </div>
            </div>

            {/* 検索ボタン */}
            <div className="flex justify-center pt-4">
              <button
                onClick={handleSearch}
                disabled={isSearching}
                className="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-8 py-4 rounded-xl font-semibold hover:from-purple-700 hover:to-blue-700 transition-all duration-200 disabled:opacity-50 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
              >
                {isSearching ? (
                  <div className="flex items-center">
                    <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent mr-2"></div>
                    検索中...
                  </div>
                ) : (
                  <div className="flex items-center">
                    <Search className="w-5 h-5 mr-2" />
                    検索実行
                  </div>
                )}
              </button>
            </div>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-6">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {/* 検索結果 */}
        {hasSearched && (
          <div className="bg-white rounded-2xl shadow-lg p-8">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-900">
                検索結果
              </h2>
              <div className="flex items-center space-x-4 text-sm text-gray-500">
                <span className="flex items-center">
                  <Target className="w-4 h-4 mr-1" />
                  {filteredResults.length} 件見つかりました
                </span>
              </div>
            </div>

            {filteredResults.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {filteredResults.slice(0, 12).map((influencer) => {
                  const hasEmail = influencer.email && influencer.email !== 'null' && influencer.email.trim() !== '';
                  const categoryIcon = getCategoryIcon(influencer.category);
                  
                  return (
                    <div key={influencer.id} className="bg-white border border-gray-200 rounded-xl p-6 hover:shadow-lg transition-all duration-200 hover:-translate-y-1">
                      {/* チャンネルサムネイルと基本情報 */}
                      <div className="flex items-start space-x-4 mb-4">
                        <div className="relative">
                          {influencer.thumbnailUrl ? (
                            <img 
                              src={influencer.thumbnailUrl} 
                              alt={`${influencer.name}のサムネイル`}
                              className="w-16 h-16 rounded-full object-cover border-2 border-gray-200"
                              onError={(e) => {
                                e.currentTarget.style.display = 'none';
                                e.currentTarget.nextElementSibling.style.display = 'flex';
                              }}
                            />
                          ) : null}
                          <div 
                            className="w-16 h-16 rounded-full bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center text-2xl"
                            style={{ display: influencer.thumbnailUrl ? 'none' : 'flex' }}
                          >
                            {categoryIcon}
                          </div>
                          {/* メールステータス */}
                          <div className="absolute -bottom-1 -right-1">
                            {hasEmail ? (
                              <div className="bg-green-500 rounded-full p-1">
                                <MailCheck className="w-3 h-3 text-white" />
                              </div>
                            ) : (
                              <div className="bg-gray-400 rounded-full p-1">
                                <MailX className="w-3 h-3 text-white" />
                              </div>
                            )}
                          </div>
                        </div>
                        
                        <div className="flex-1 min-w-0">
                          <h3 className="text-lg font-bold text-gray-900 mb-1 truncate">
                            {influencer.name}
                          </h3>
                          <div className="flex items-center space-x-2 mb-2">
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                              {categoryIcon} {influencer.category}
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* 統計情報 */}
                      <div className="grid grid-cols-2 gap-4 mb-4">
                        <div className="text-center p-3 bg-gray-50 rounded-lg">
                          <div className="flex items-center justify-center mb-1">
                            <Users className="w-4 h-4 text-purple-600 mr-1" />
                            <span className="text-xs text-gray-500">登録者</span>
                          </div>
                          <div className="text-lg font-bold text-gray-900">
                            {influencer.subscriberCount ? influencer.subscriberCount.toLocaleString() : 'N/A'}
                          </div>
                        </div>
                        
                        <div className="text-center p-3 bg-gray-50 rounded-lg">
                          <div className="flex items-center justify-center mb-1">
                            <TrendingUp className="w-4 h-4 text-green-600 mr-1" />
                            <span className="text-xs text-gray-500">エンゲージ</span>
                          </div>
                          <div className="text-lg font-bold text-gray-900">
                            {influencer.engagementRate ? `${influencer.engagementRate.toFixed(1)}%` : 'N/A'}
                          </div>
                        </div>
                      </div>

                      {/* 説明文 */}
                      {influencer.description && (
                        <p className="text-sm text-gray-600 mb-4 line-clamp-2">
                          {influencer.description.length > 100 
                            ? `${influencer.description.substring(0, 100)}...` 
                            : influencer.description
                          }
                        </p>
                      )}

                      {/* アクションボタン */}
                      <div className="flex space-x-2">
                        <button
                          onClick={() => openModal(influencer)}
                          className="flex-1 flex items-center justify-center space-x-1 bg-purple-600 text-white py-2 px-4 rounded-lg hover:bg-purple-700 transition-colors text-sm font-medium"
                        >
                          <Info className="w-4 h-4" />
                          <span>詳細</span>
                        </button>
                        <button
                          onClick={() => handleCollaborationProposal(influencer)}
                          disabled={isGeneratingProposal || !hasEmail}
                          className="flex-1 flex items-center justify-center space-x-1 bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
                          title={!hasEmail ? 'メールアドレスが未登録です' : ''}
                        >
                          {isGeneratingProposal ? (
                            <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
                          ) : (
                            <MessageCircle className="w-4 h-4" />
                          )}
                          <span>{isGeneratingProposal ? '生成中' : '提案'}</span>
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="text-center py-12">
                <div className="mb-4">
                  <SearchCheck className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">検索結果が見つかりません</h3>
                  <p className="text-gray-500">検索条件を変更して再度お試しください</p>
                </div>
                <div className="text-sm text-gray-400">
                  <p>ヒント:</p>
                  <ul className="list-disc list-inside space-y-1 mt-2">
                    <li>キーワードを変更してみてください</li>
                    <li>カテゴリフィルタを「すべて」に設定してみてください</li>
                    <li>登録者数の範囲を広げてみてください</li>
                  </ul>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      <InfluencerDetailModal
        influencer={selectedInfluencer}
        isOpen={isModalOpen}
        onClose={closeModal}
        onCollaborationProposal={handleCollaborationProposal}
        isGeneratingProposal={isGeneratingProposal}
      />
    </div>
  );
}