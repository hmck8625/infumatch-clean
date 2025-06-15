'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { searchInfluencers, getAIRecommendations, generateCollaborationProposal, Influencer, APIError, CampaignRequest, AIRecommendationResponse } from '@/lib/api';
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
  Sparkles
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
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto relative">
        {/* ヘッダー */}
        <div className="sticky top-0 bg-white border-b border-gray-200 p-6 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-blue-500 rounded-full flex items-center justify-center text-2xl">
              {categoryIcon}
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">{influencer.name}</h2>
              <p className="text-gray-500">{influencer.category}</p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* コンテンツ */}
        <div className="p-6 space-y-6">
          {/* 基本情報 */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-4">
              <div className="flex items-center space-x-2 mb-2">
                <Users className="w-5 h-5 text-blue-600" />
                <span className="text-sm font-medium text-blue-900">登録者数</span>
              </div>
              <p className="text-2xl font-bold text-blue-900">
                {influencer.subscriberCount?.toLocaleString()}人
              </p>
            </div>
            
            <div className="bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl p-4">
              <div className="flex items-center space-x-2 mb-2">
                <Eye className="w-5 h-5 text-green-600" />
                <span className="text-sm font-medium text-green-900">総視聴回数</span>
              </div>
              <p className="text-2xl font-bold text-green-900">
                {influencer.viewCount?.toLocaleString()}回
              </p>
            </div>

            <div className="bg-gradient-to-r from-purple-50 to-pink-50 rounded-xl p-4">
              <div className="flex items-center space-x-2 mb-2">
                <Play className="w-5 h-5 text-purple-600" />
                <span className="text-sm font-medium text-purple-900">動画数</span>
              </div>
              <p className="text-2xl font-bold text-purple-900">
                {influencer.videoCount?.toLocaleString()}本
              </p>
            </div>
          </div>

          {/* エンゲージメント率 */}
          <div className="bg-gradient-to-r from-orange-50 to-red-50 rounded-xl p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <TrendingUp className="w-5 h-5 text-orange-600" />
                <span className="text-sm font-medium text-orange-900">エンゲージメント率</span>
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold text-orange-900">{influencer.engagementRate?.toFixed(2)}%</p>
                <p className="text-xs text-orange-700">
                  {influencer.engagementRate && influencer.engagementRate > 3 ? '高' : 
                   influencer.engagementRate && influencer.engagementRate > 1 ? '中' : '低'}
                </p>
              </div>
            </div>
          </div>

          {/* 連絡先情報 */}
          <div className="bg-gray-50 rounded-xl p-4">
            <div className="flex items-center space-x-2 mb-3">
              <Mail className="w-5 h-5 text-gray-600" />
              <span className="font-medium text-gray-900">連絡先</span>
            </div>
            <div className="flex items-center space-x-2">
              {hasEmail ? (
                <>
                  <MailCheck className="w-4 h-4 text-green-600" />
                  <span className="text-green-800 font-medium">メールアドレス有り</span>
                  <span className="text-gray-600">({influencer.email})</span>
                </>
              ) : (
                <>
                  <MailX className="w-4 h-4 text-red-600" />
                  <span className="text-red-800 font-medium">メールアドレス無し</span>
                  <span className="text-gray-600">YouTubeコメント経由での連絡が必要</span>
                </>
              )}
            </div>
          </div>

          {/* AI分析情報 */}
          {influencer.aiAnalysis && Object.keys(influencer.aiAnalysis).length > 0 && (
            <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-xl p-4">
              <div className="flex items-center space-x-2 mb-3">
                <Sparkles className="w-5 h-5 text-indigo-600" />
                <span className="font-medium text-indigo-900">AI分析情報</span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                {influencer.aiAnalysis.target_age && (
                  <div>
                    <span className="text-indigo-700 font-medium">ターゲット年齢:</span>
                    <span className="ml-2 text-indigo-900">{influencer.aiAnalysis.target_age}</span>
                  </div>
                )}
                {influencer.aiAnalysis.top_product && (
                  <div>
                    <span className="text-indigo-700 font-medium">推奨商品:</span>
                    <span className="ml-2 text-indigo-900">{influencer.aiAnalysis.top_product}</span>
                  </div>
                )}
                {influencer.aiAnalysis.match_score && (
                  <div>
                    <span className="text-indigo-700 font-medium">マッチ度:</span>
                    <span className="ml-2 text-indigo-900">{(influencer.aiAnalysis.match_score * 100).toFixed(0)}%</span>
                  </div>
                )}
                {influencer.brandSafetyScore && (
                  <div>
                    <span className="text-indigo-700 font-medium">ブランド安全性:</span>
                    <span className="ml-2 text-indigo-900">{(influencer.brandSafetyScore * 100).toFixed(0)}%</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* 説明文 */}
          <div className="bg-white border border-gray-200 rounded-xl p-4">
            <div className="flex items-center space-x-2 mb-3">
              <Info className="w-5 h-5 text-gray-600" />
              <span className="font-medium text-gray-900">チャンネル説明</span>
            </div>
            <p className="text-gray-700 leading-relaxed">{influencer.description}</p>
          </div>

          {/* 追加情報 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            {influencer.country && (
              <div className="flex items-center space-x-2">
                <Globe className="w-4 h-4 text-gray-500" />
                <span className="text-gray-600">国: {influencer.country}</span>
              </div>
            )}
            {influencer.language && (
              <div className="flex items-center space-x-2">
                <Calendar className="w-4 h-4 text-gray-500" />
                <span className="text-gray-600">言語: {influencer.language}</span>
              </div>
            )}
          </div>

          {/* アクションボタン */}
          <div className="flex space-x-3 pt-4 border-t border-gray-200">
            <button 
              onClick={() => onCollaborationProposal(influencer)}
              disabled={isGeneratingProposal}
              className="flex-1 bg-gradient-to-r from-purple-600 to-blue-600 text-white py-3 px-4 rounded-xl font-medium hover:from-purple-700 hover:to-blue-700 transition-all duration-200 flex items-center justify-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isGeneratingProposal ? (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              ) : (
                <Target className="w-4 h-4" />
              )}
              <span>{isGeneratingProposal ? 'AI生成中...' : 'コラボ提案'}</span>
            </button>
            <button 
              onClick={() => window.open(`https://www.youtube.com/channel/${influencer.channelId}`, '_blank')}
              className="flex-1 border border-gray-300 text-gray-700 py-3 px-4 rounded-xl font-medium hover:bg-gray-50 transition-colors flex items-center justify-center space-x-2"
            >
              <ExternalLink className="w-4 h-4" />
              <span>チャンネル確認</span>
            </button>
          </div>
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

  const handleInitialLoad = async () => {
    try {
      setIsSearching(true);
      setError(null);
      
      const results = await searchInfluencers({});
      setFilteredResults(results);
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

  const handleSearch = async () => {
    try {
      setIsSearching(true);
      setError(null);
      
      if (useAI) {
        // AI推薦の実行
        await handleAIRecommendation();
      } else {
        // 通常検索の実行
        const searchParams = {
          keyword: searchQuery.trim() || undefined,
          category: selectedCategory !== 'all' ? selectedCategory : undefined,
          min_subscribers: minSubscribers ? parseInt(minSubscribers) : undefined,
          max_subscribers: maxSubscribers ? parseInt(maxSubscribers) : undefined,
        };

        const results = await searchInfluencers(searchParams);
        setFilteredResults(results);
        
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

  const handleAIRecommendation = async () => {
    try {
      // AI推薦に必要なフィールドの検証
      if (!productName || !budgetMin || !budgetMax || !targetAudience || !campaignGoals) {
        setError('AI推薦には商品名、予算、ターゲット層、キャンペーン目標の入力が必要です');
        return;
      }

      const campaign: CampaignRequest = {
        product_name: productName,
        budget_min: parseInt(budgetMin),
        budget_max: parseInt(budgetMax),
        target_audience: targetAudience.split(',').map(t => t.trim()),
        required_categories: selectedCategory !== 'all' ? [selectedCategory] : [],
        campaign_goals: campaignGoals,
        min_engagement_rate: 2.0,
        min_subscribers: minSubscribers ? parseInt(minSubscribers) : undefined,
        max_subscribers: maxSubscribers ? parseInt(maxSubscribers) : undefined,
        geographic_focus: '日本'
      };

      const recommendations = await getAIRecommendations(campaign);
      setAiResults(recommendations);
      setFilteredResults([]);
    } catch (err) {
      if (err instanceof APIError) {
        setError(`AI推薦エラー: ${err.message}`);
      } else {
        setError('AI推薦中にエラーが発生しました');
      }
      console.error('AI recommendation failed:', err);
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
      {/* ヘッダー */}
      <div className="bg-white shadow-sm border-b">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <Link href="/" className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
              InfuMatch
            </Link>
            <nav className="hidden md:flex space-x-8">
              <Link href="/search" className="text-purple-600 font-medium">検索</Link>
              <Link href="/messages" className="text-gray-600 hover:text-purple-600 transition-colors">メッセージ</Link>
              <Link href="/matching" className="text-gray-600 hover:text-purple-600 transition-colors">AIマッチング</Link>
              <Link href="/settings" className="text-gray-600 hover:text-purple-600 transition-colors">設定</Link>
            </nav>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-6 py-8">
        {/* 検索セクション */}
        <div className={`bg-white rounded-2xl shadow-lg p-8 mb-8 transform transition-all duration-1000 ${isVisible ? 'translate-y-0 opacity-100' : 'translate-y-10 opacity-0'}`}>
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-gray-900 mb-4">インフルエンサー検索</h1>
            <p className="text-gray-600 text-lg">AIが最適なYouTubeインフルエンサーを見つけます</p>
          </div>

          {/* AI/通常検索切り替え */}
          <div className="flex justify-center mb-6">
            <div className="bg-gray-100 p-1 rounded-xl">
              <button
                onClick={() => setUseAI(false)}
                className={`px-6 py-2 rounded-lg font-medium transition-all ${!useAI ? 'bg-white text-purple-600 shadow-sm' : 'text-gray-600'}`}
              >
                通常検索
              </button>
              <button
                onClick={() => setUseAI(true)}
                className={`px-6 py-2 rounded-lg font-medium transition-all ${useAI ? 'bg-white text-purple-600 shadow-sm' : 'text-gray-600'}`}
              >
                AI推薦
              </button>
            </div>
          </div>

          {useAI ? (
            /* AI推薦フォーム */
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">商品名</label>
                  <input
                    type="text"
                    value={productName}
                    onChange={(e) => setProductName(e.target.value)}
                    placeholder="例: プレミアム調味料セット"
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">ターゲット層</label>
                  <input
                    type="text"
                    value={targetAudience}
                    onChange={(e) => setTargetAudience(e.target.value)}
                    placeholder="例: 20-40代女性, 料理好き"
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">予算下限（円）</label>
                  <input
                    type="number"
                    value={budgetMin}
                    onChange={(e) => setBudgetMin(e.target.value)}
                    placeholder="20000"
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">予算上限（円）</label>
                  <input
                    type="number"
                    value={budgetMax}
                    onChange={(e) => setBudgetMax(e.target.value)}
                    placeholder="100000"
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">キャンペーン目標</label>
                <textarea
                  value={campaignGoals}
                  onChange={(e) => setCampaignGoals(e.target.value)}
                  placeholder="例: ブランド認知度向上と商品売上増加を目指し、料理動画内で自然な商品紹介を行いたい"
                  rows={3}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>
            </div>
          ) : (
            /* 通常検索フォーム */
            <div className="space-y-6">
              <div className="relative">
                <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="キーワードを入力..."
                  className="w-full pl-12 pr-4 py-4 text-lg border border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">カテゴリ</label>
                  <select
                    value={selectedCategory}
                    onChange={(e) => setSelectedCategory(e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  >
                    {categories.map(category => (
                      <option key={category} value={category}>
                        {category === 'all' ? 'すべて' : category}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">最小登録者数</label>
                  <input
                    type="number"
                    value={minSubscribers}
                    onChange={(e) => setMinSubscribers(e.target.value)}
                    placeholder="1000"
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">最大登録者数</label>
                  <input
                    type="number"
                    value={maxSubscribers}
                    onChange={(e) => setMaxSubscribers(e.target.value)}
                    placeholder="1000000"
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  />
                </div>
              </div>
            </div>
          )}

          <div className="flex justify-center mt-8">
            <button
              onClick={handleSearch}
              disabled={isSearching}
              className="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-8 py-4 rounded-xl font-semibold text-lg hover:from-purple-700 hover:to-blue-700 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2 shadow-lg"
            >
              {isSearching ? (
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
              ) : useAI ? (
                <Sparkles className="w-5 h-5" />
              ) : (
                <Search className="w-5 h-5" />
              )}
              <span>{isSearching ? '検索中...' : useAI ? 'AI推薦実行' : '検索実行'}</span>
            </button>
          </div>
        </div>

        {/* エラー表示 */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-6">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {/* 検索結果 */}
        {hasSearched && (
          <div className={`transform transition-all duration-1000 ${isVisible ? 'translate-y-0 opacity-100' : 'translate-y-10 opacity-0'}`}>
            {filteredResults.length > 0 ? (
              <div>
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-2xl font-bold text-gray-900">
                    検索結果 ({filteredResults.length}件)
                  </h2>
                  <div className="flex items-center space-x-2 text-gray-600">
                    <Filter className="w-4 h-4" />
                    <span className="text-sm">フィルタ適用済み</span>
                  </div>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {filteredResults.map((influencer) => {
                    const hasEmail = influencer.email && influencer.email !== 'null' && influencer.email.trim() !== '';
                    const categoryIcon = getCategoryIcon(influencer.category);
                    
                    return (
                      <div key={influencer.id} className="bg-white rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 overflow-hidden group">
                        {/* カード画像部分 */}
                        <div className="h-48 bg-gradient-to-br from-purple-500 to-blue-500 relative overflow-hidden">
                          <div className="absolute inset-0 bg-black/20"></div>
                          <div className="absolute inset-0 flex items-center justify-center">
                            <div className="text-6xl">{categoryIcon}</div>
                          </div>
                          
                          {/* ステータスバッジ */}
                          <div className="absolute top-4 left-4">
                            <span className="bg-white/90 text-gray-800 px-3 py-1 rounded-full text-xs font-medium">
                              {influencer.category}
                            </span>
                          </div>
                          
                          {/* メール状態バッジ */}
                          <div className="absolute top-4 right-4">
                            {hasEmail ? (
                              <div className="bg-green-500 text-white p-2 rounded-full">
                                <MailCheck className="w-4 h-4" />
                              </div>
                            ) : (
                              <div className="bg-red-500 text-white p-2 rounded-full">
                                <MailX className="w-4 h-4" />
                              </div>
                            )}
                          </div>
                        </div>
                        
                        {/* カード内容 */}
                        <div className="p-6">
                          <h3 className="text-xl font-bold text-gray-900 mb-2 line-clamp-2">
                            {influencer.name}
                          </h3>
                          
                          <p className="text-gray-600 text-sm mb-4 line-clamp-3">
                            {influencer.description}
                          </p>
                          
                          {/* 統計情報 */}
                          <div className="grid grid-cols-3 gap-4 mb-4">
                            <div className="text-center">
                              <div className="flex items-center justify-center mb-1">
                                <Users className="w-4 h-4 text-blue-500" />
                              </div>
                              <p className="text-sm font-semibold text-gray-900">
                                {influencer.subscriberCount?.toLocaleString()}
                              </p>
                              <p className="text-xs text-gray-500">登録者</p>
                            </div>
                            
                            <div className="text-center">
                              <div className="flex items-center justify-center mb-1">
                                <Play className="w-4 h-4 text-green-500" />
                              </div>
                              <p className="text-sm font-semibold text-gray-900">
                                {influencer.videoCount?.toLocaleString()}
                              </p>
                              <p className="text-xs text-gray-500">動画数</p>
                            </div>
                            
                            <div className="text-center">
                              <div className="flex items-center justify-center mb-1">
                                <TrendingUp className="w-4 h-4 text-purple-500" />
                              </div>
                              <p className="text-sm font-semibold text-gray-900">
                                {influencer.engagementRate?.toFixed(1)}%
                              </p>
                              <p className="text-xs text-gray-500">エンゲージ</p>
                            </div>
                          </div>
                          
                          {/* アクションボタン */}
                          <div className="flex space-x-2">
                            <button
                              onClick={() => openModal(influencer)}
                              className="flex-1 bg-purple-600 text-white py-2 px-4 rounded-xl font-medium hover:bg-purple-700 transition-colors flex items-center justify-center space-x-2"
                            >
                              <Info className="w-4 h-4" />
                              <span>詳細</span>
                            </button>
                            <button
                              onClick={() => handleCollaborationProposal(influencer)}
                              disabled={isGeneratingProposal}
                              className="flex-1 bg-gradient-to-r from-green-600 to-emerald-600 text-white py-2 px-4 rounded-xl font-medium hover:from-green-700 hover:to-emerald-700 transition-colors flex items-center justify-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                              {isGeneratingProposal ? (
                                <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white"></div>
                              ) : (
                                <Target className="w-4 h-4" />
                              )}
                              <span className="text-xs">{isGeneratingProposal ? 'AI生成中' : '提案'}</span>
                            </button>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            ) : (
              <div className="text-center py-12">
                <Search className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-gray-900 mb-2">検索結果が見つかりませんでした</h3>
                <p className="text-gray-600">検索条件を変更して再度お試しください</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* 詳細モーダル */}
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