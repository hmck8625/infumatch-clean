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
  Handshake,
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

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl p-6 max-w-md w-full">
        <h2 className="text-xl font-bold mb-4">{influencer.name}</h2>
        <p className="text-gray-600 mb-4">{influencer.description}</p>
        <div className="flex justify-end space-x-2">
          <button onClick={onClose} className="px-4 py-2 bg-gray-200 rounded">
            閉じる
          </button>
          <button 
            onClick={() => onCollaborationProposal(influencer)}
            disabled={isGeneratingProposal}
            className="px-4 py-2 bg-purple-600 text-white rounded disabled:opacity-50"
          >
            {isGeneratingProposal ? '生成中...' : 'コラボ提案'}
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
        <div className="bg-white rounded-2xl shadow-lg p-8 mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4 text-center">インフルエンサー検索</h1>
          <p className="text-gray-600 text-lg text-center mb-8">YouTubeインフルエンサーを検索</p>
          
          <div className="flex justify-center">
            <button
              onClick={handleSearch}
              disabled={isSearching}
              className="bg-purple-600 text-white px-8 py-4 rounded-xl font-semibold hover:bg-purple-700 transition-colors disabled:opacity-50"
            >
              {isSearching ? '検索中...' : '検索実行'}
            </button>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-6">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {hasSearched && filteredResults.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredResults.slice(0, 12).map((influencer) => (
              <div key={influencer.id} className="bg-white rounded-xl shadow-lg p-6">
                <h3 className="text-xl font-bold mb-2">{influencer.name}</h3>
                <p className="text-gray-600 mb-4">{influencer.category}</p>
                <div className="flex justify-between text-sm text-gray-500 mb-4">
                  <span>{influencer.subscriberCount?.toLocaleString()} 登録者</span>
                  <span>{influencer.engagementRate?.toFixed(1)}% エンゲージ</span>
                </div>
                <div className="flex space-x-2">
                  <button
                    onClick={() => openModal(influencer)}
                    className="flex-1 bg-purple-600 text-white py-2 px-4 rounded-lg hover:bg-purple-700 transition-colors"
                  >
                    詳細
                  </button>
                  <button
                    onClick={() => handleCollaborationProposal(influencer)}
                    disabled={isGeneratingProposal}
                    className="flex-1 bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50"
                  >
                    {isGeneratingProposal ? '生成中' : '提案'}
                  </button>
                </div>
              </div>
            ))}
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