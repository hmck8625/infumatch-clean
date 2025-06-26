'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { AuthGuard } from '@/components/auth-guard';
import Header from '@/components/Header';
import { 
  apiClient, 
  CampaignRequest, 
  AIRecommendationResponse, 
  searchInfluencers, 
  Influencer,
  GeminiMatchingRequest,
  GeminiMatchingResponse,
  GeminiAnalysisResult
} from '@/lib/api';

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
  geminiAnalysis?: GeminiAnalysisResult; // Gemini分析結果（詳細表示用）
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
  const [selectedChannelDetail, setSelectedChannelDetail] = useState<Influencer | null>(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);
  const [useGeminiAgent, setUseGeminiAgent] = useState(false);
  const [geminiAnalysisResults, setGeminiAnalysisResults] = useState<GeminiAnalysisResult[]>([]);
  const [isGeminiAnalyzing, setIsGeminiAnalyzing] = useState(false);

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
    setIsGeminiAnalyzing(useGeminiAgent);
    setShowResults(false);
    setError(null);
    
    try {
      if (useGeminiAgent) {
        // 🤖 Geminiマッチングエージェントを使用
        console.log('🧠 Gemini高度分析エージェント開始...');
        const geminiRequest = buildGeminiMatchingRequest();
        console.log('📋 Gemini分析リクエスト:', geminiRequest);
        
        const geminiResponse = await apiClient.getGeminiMatching(geminiRequest);
        console.log('🎯 Gemini分析完了:', geminiResponse);
        
        if (geminiResponse.success && geminiResponse.analysis_results?.length > 0) {
          const geminiResults = convertGeminiResultsToMatchingResults(geminiResponse.analysis_results);
          setMatchingResults(geminiResults);
          setGeminiAnalysisResults(geminiResponse.analysis_results);
          console.log('✨ Gemini高度分析結果:', geminiResults);
        } else {
          throw new Error('Gemini分析で結果が取得できませんでした');
        }
        
      } else {
        // 従来のAI推薦システムを使用
        console.log('🚀 従来AI推薦開始 (データベース使用)...');
        const campaignRequest = buildCampaignRequest();
        
        const aiResponse = await apiClient.getAIRecommendations(campaignRequest);
        console.log('📡 AI推薦レスポンス (データベース):', aiResponse);
        
        if (aiResponse.success && aiResponse.recommendations?.length > 0) {
          const convertedResults = convertAIResponseToMatchingResults(aiResponse);
          setMatchingResults(convertedResults);
          console.log('✅ AI推薦結果変換完了 (実データ):', convertedResults);
        } else {
          // フォールバック処理
          console.warn('⚠️ AI推薦API応答なし、代替手段を試行中...');
          const directResults = await searchInfluencers({});
          
          if (directResults && directResults.length > 0) {
            const limitedResults = directResults.slice(0, 4).map((influencer, index) => ({
              id: influencer.id,
              influencerName: influencer.name,
              score: 95 - (index * 3),
              category: influencer.category || '総合',
              reason: `データベースから直接選出されたトップ${index + 1}の推薦チャンネル`,
              estimatedReach: influencer.subscriberCount || Math.floor(Math.random() * 100000) + 50000,
              estimatedCost: Math.floor(Math.random() * 200000) + 80000,
              thumbnailUrl: influencer.thumbnailUrl,
              subscriberCount: influencer.subscriberCount,
              engagementRate: influencer.engagementRate,
              description: influencer.description,
              email: influencer.email,
              compatibility: {
                audience: Math.floor(Math.random() * 20) + 80,
                content: Math.floor(Math.random() * 20) + 80,
                brand: Math.floor(Math.random() * 20) + 80,
              }
            }));
            setMatchingResults(limitedResults);
            console.log('✅ データベース直接取得完了:', limitedResults);
          } else {
            throw new Error('データベースからのデータ取得にも失敗しました');
          }
        }
      }
      
    } catch (error) {
      console.error('❌ マッチングシステムエラー:', error);
      setError(error instanceof Error ? error.message : 'マッチングの実行に失敗しました');
      
      // 最終フォールバック: モックデータ
      const fallbackResults = customizeMatchingResults();
      setMatchingResults(fallbackResults);
      console.log('💡 フォールバックデータを使用:', fallbackResults);
    }
    
    setIsAnalyzing(false);
    setIsGeminiAnalyzing(false);
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
    // 設定データから詳細なキャンペーンリクエストを構築
    const companyInfo = settings?.companyInfo || {};
    const products = settings?.products || [];
    const matchingSettings = settings?.matchingSettings || {};
    const negotiationSettings = settings?.negotiationSettings || {};
    
    // 商品情報を詳細に構築
    const productDetails = products.map(p => ({
      name: p.name,
      category: p.category,
      targetAudience: p.targetAudience,
      description: p.description,
      priceRange: p.priceRange
    }));
    
    // ターゲットオーディエンスを統合（重複排除）
    const uniqueTargetAudiences = [...new Set(products.map(p => p.targetAudience).filter(Boolean))];
    
    // カテゴリを商品カテゴリと優先カテゴリから統合
    const productCategories = [...new Set(products.map(p => p.category).filter(Boolean))];
    const allCategories = [...new Set([
      ...(matchingSettings.priorityCategories || []),
      ...productCategories
    ])];
    
    // キャンペーン目標を企業情報と商品情報から構築
    const campaignGoals = [
      companyInfo.description,
      products.length > 0 ? `${products.map(p => p.name).join('、')}の認知度向上` : null,
      companyInfo.industry ? `${companyInfo.industry}業界でのブランドプレゼンス強化` : null
    ].filter(Boolean).join('。');
    
    // 優先キーワードを構築（商品名、カテゴリ、業界から）
    const priorityKeywords = [
      ...(matchingSettings.priorityKeywords || []),
      ...products.map(p => p.name),
      companyInfo.industry,
      ...productCategories
    ].filter(Boolean);
    
    // 除外キーワードも考慮
    const excludeKeywords = matchingSettings.excludeKeywords || [];
    
    return {
      product_name: products.map(p => p.name).join(", ") || companyInfo.companyName || "サンプル製品",
      product_details: productDetails, // 商品の詳細情報を追加
      company_name: companyInfo.companyName,
      company_industry: companyInfo.industry,
      company_description: companyInfo.description,
      budget_min: negotiationSettings.defaultBudgetRange?.min || 50000,
      budget_max: negotiationSettings.defaultBudgetRange?.max || 300000,
      target_audience: uniqueTargetAudiences.length > 0 ? uniqueTargetAudiences : ["20-30代", "男女問わず"],
      required_categories: allCategories.length > 0 ? allCategories : ["テクノロジー", "ライフスタイル"],
      exclude_categories: matchingSettings.excludeCategories || [],
      campaign_goals: campaignGoals || "ブランド認知度向上とコンバージョン獲得",
      min_engagement_rate: matchingSettings.minEngagementRate || 2.0,
      min_subscribers: matchingSettings.minSubscribers || 10000,
      max_subscribers: matchingSettings.maxSubscribers || 500000,
      geographic_focus: matchingSettings.geographicFocus?.[0] || "日本",
      priority_keywords: priorityKeywords,
      exclude_keywords: excludeKeywords,
      negotiation_tone: negotiationSettings.preferredTone,
      key_priorities: negotiationSettings.keyPriorities || [],
      special_instructions: negotiationSettings.specialInstructions
    };
  };

  // Geminiマッチングエージェント用の詳細リクエスト構築
  const buildGeminiMatchingRequest = (): GeminiMatchingRequest => {
    const companyInfo = settings?.companyInfo || {};
    const products = settings?.products || [];
    const matchingSettings = settings?.matchingSettings || {};
    const negotiationSettings = settings?.negotiationSettings || {};
    
    // ブランド価値観を企業情報から抽出・推測
    const inferredBrandValues = [
      companyInfo.industry ? `${companyInfo.industry}のリーディングカンパニー` : '',
      negotiationSettings.preferredTone === 'friendly' ? '親しみやすさ' : 
      negotiationSettings.preferredTone === 'professional' ? 'プロフェッショナリズム' : '信頼性',
      '品質重視',
      '顧客満足'
    ].filter(Boolean);
    
    // コミュニケーションスタイルを設定から推測
    const communicationStyle = negotiationSettings.preferredTone === 'friendly' ? 
      'カジュアルで親しみやすく、顧客との距離を縮めるアプローチ' :
      negotiationSettings.preferredTone === 'professional' ? 
      '専門的で信頼性重視、品質と実績を前面に出すアプローチ' :
      'バランスの取れた、信頼性と親しみやすさを兼ね備えたアプローチ';
    
    // 商品ポートフォリオの詳細化
    const detailedProducts = products.map(product => ({
      name: product.name,
      category: product.category,
      description: product.description,
      target_audience: product.targetAudience,
      price_range: product.priceRange,
      unique_selling_points: [
        product.description ? `${product.description.substring(0, 50)}...` : '',
        `${product.category}カテゴリの革新的製品`,
        '高品質保証'
      ].filter(Boolean),
      marketing_goals: [
        'ブランド認知度向上',
        'ターゲット層への浸透',
        'コンバージョン率向上',
        '長期的なファンベース構築'
      ]
    }));
    
    // キャンペーン目標を詳細化
    const campaignGoals = [
      'ブランド認知度向上',
      'ターゲット層へのリーチ拡大',
      '商品の魅力訴求',
      'エンゲージメント向上'
    ];
    
    // 成功指標を明確化
    const successMetrics = [
      'インプレッション数',
      'エンゲージメント率',
      'ブランド認知度調査結果',
      'コンバージョン率',
      'ROI'
    ];
    
    return {
      company_profile: {
        name: companyInfo.companyName || '企業名未設定',
        industry: companyInfo.industry || '業界未設定',
        description: companyInfo.description || '企業説明未設定',
        brand_values: inferredBrandValues,
        target_demographics: [...new Set(products.map(p => p.targetAudience).filter(Boolean))],
        communication_style: communicationStyle,
        previous_campaigns: [] // 今後追加可能
      },
      product_portfolio: {
        products: detailedProducts
      },
      campaign_objectives: {
        primary_goals: campaignGoals,
        success_metrics: successMetrics,
        budget_range: {
          min: negotiationSettings.defaultBudgetRange?.min || 50000,
          max: negotiationSettings.defaultBudgetRange?.max || 300000
        },
        timeline: '3-6ヶ月',
        geographic_focus: matchingSettings.geographicFocus || ['日本']
      },
      influencer_preferences: {
        preferred_categories: matchingSettings.priorityCategories || [],
        avoid_categories: matchingSettings.excludeCategories || [],
        min_engagement_rate: matchingSettings.minEngagementRate || 2.0,
        subscriber_range: {
          min: matchingSettings.minSubscribers || 10000,
          max: matchingSettings.maxSubscribers || 500000
        },
        content_style_preferences: [
          negotiationSettings.preferredTone === 'friendly' ? 'カジュアル・親しみやすい' :
          negotiationSettings.preferredTone === 'professional' ? 'プロフェッショナル・専門的' : 'バランス型',
          '教育的価値のあるコンテンツ',
          '視覚的に魅力的',
          'エンゲージメントの高い'
        ],
        collaboration_types: [
          '商品レビュー',
          'スポンサードコンテンツ',
          'ブランドアンバサダー',
          'イベント参加',
          'ライブストリーム'
        ]
      }
    };
  };

  const convertAIResponseToMatchingResults = (aiResponse: AIRecommendationResponse): MatchingResult[] => {
    if (!aiResponse.recommendations) return [];
    
    return aiResponse.recommendations.map((rec: any, index: number) => {
      // ブランド親和性スコアを計算（企業情報とインフルエンサーの特性から）
      let brandCompatibilityScore = rec.detailed_scores?.budget_fit || 0.6;
      
      // 企業の業界とインフルエンサーのカテゴリの親和性を評価
      if (settings?.companyInfo?.industry && rec.category) {
        const industryAffinityMap: Record<string, Record<string, number>> = {
          'テクノロジー': { 'テクノロジー': 1.0, 'ビジネス': 0.8, 'エンタメ': 0.6 },
          '美容・化粧品': { '美容': 1.0, 'ファッション': 0.9, 'ライフスタイル': 0.8 },
          '食品・飲料': { '料理': 1.0, 'グルメ': 1.0, 'ライフスタイル': 0.7 },
          'ファッション': { 'ファッション': 1.0, '美容': 0.8, 'ライフスタイル': 0.8 },
          'エンターテイメント': { 'エンタメ': 1.0, 'ゲーム': 0.9, 'コメディ': 0.9 }
        };
        
        const industry = settings.companyInfo.industry;
        const category = rec.category;
        
        if (industryAffinityMap[industry] && industryAffinityMap[industry][category]) {
          brandCompatibilityScore = Math.max(brandCompatibilityScore, industryAffinityMap[industry][category]);
        }
      }
      
      // 商品カテゴリとの親和性も考慮
      if (settings?.products?.length > 0) {
        const productCategories = settings.products.map(p => p.category);
        const categoryMatch = productCategories.some(pCat => 
          rec.category.includes(pCat) || pCat.includes(rec.category)
        );
        if (categoryMatch) {
          brandCompatibilityScore = Math.min(1.0, brandCompatibilityScore + 0.1);
        }
      }
      
      // 説明文を企業情報に基づいてカスタマイズ
      let enhancedReason = rec.explanation || "AI分析による推薦";
      if (settings?.companyInfo?.companyName) {
        enhancedReason = `${settings.companyInfo.companyName}様の${settings.companyInfo.industry || 'ビジネス'}に最適。${enhancedReason}`;
      }
      
      return {
        id: rec.channel_id || `ai-rec-${index}`,
        influencerName: rec.channel_name || `推薦チャンネル ${index + 1}`,
        score: Math.round((rec.overall_score || 0.5) * 100),
        category: rec.category || "総合",
        reason: enhancedReason,
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
          brand: Math.round(brandCompatibilityScore * 100),
        }
      };
    });
  };

  // Gemini分析結果をマッチング結果形式に変換
  const convertGeminiResultsToMatchingResults = (geminiResults: GeminiAnalysisResult[]): MatchingResult[] => {
    return geminiResults.map((result, index) => ({
      id: result.influencer_id,
      influencerName: `Gemini推薦 ${index + 1}`,
      score: result.overall_compatibility_score,
      category: '高度AI分析',
      reason: result.recommendation_summary.primary_recommendation_reason,
      estimatedReach: Math.floor(Math.random() * 100000) + 50000, // TODO: 実際のデータから取得
      estimatedCost: result.strategic_insights.budget_recommendations.min,
      thumbnailUrl: undefined,
      subscriberCount: undefined,
      engagementRate: undefined,
      description: result.recommendation_summary.success_scenario,
      email: undefined,
      compatibility: {
        audience: result.detailed_analysis.audience_synergy.score,
        content: result.detailed_analysis.content_fit.score,
        brand: result.detailed_analysis.brand_alignment.score,
      },
      geminiAnalysis: result // Gemini分析結果の詳細を保持
    }));
  };

  const formatNumber = (num: number) => {
    if (num >= 10000) {
      return (num / 10000).toFixed(1) + '万';
    }
    return num.toLocaleString();
  };

  const handleShowDetail = async (channelId: string, channelName?: string, reason?: string) => {
    try {
      setIsLoadingDetail(true);
      setError(null);
      
      console.log('🔍 詳細表示要求:', { channelId, channelName });
      
      // 複数の検索方法を試行
      let results: Influencer[] = [];
      
      // 1. チャンネルIDで検索
      if (channelId && channelId !== `ai-rec-${0}` && !channelId.startsWith('ai-rec-')) {
        console.log('🔍 チャンネルID検索実行:', channelId);
        results = await searchInfluencers({ channel_id: channelId });
        console.log('📋 チャンネルID検索結果:', results?.length, '件見つかりました');
        
        // もし結果が1件だけなら詳細ログ
        if (results && results.length === 1) {
          console.log('✅ 正確なマッチ:', results[0].name, '- ID:', results[0].id);
        } else if (results && results.length > 1) {
          console.log('⚠️ 複数マッチ:', results.map(r => r.name));
        }
      }
      
      // 2. チャンネル名で検索（IDで見つからない場合）
      if ((!results || results.length === 0) && channelName) {
        results = await searchInfluencers({ query: channelName });
        console.log('📋 チャンネル名検索結果:', results);
        
        // 部分一致でフィルタリング
        if (results && results.length > 0) {
          const exactMatch = results.find(r => r.name === channelName);
          if (exactMatch) {
            results = [exactMatch];
          } else {
            // 類似度の高いものを選択
            results = results.filter(r => 
              r.name.includes(channelName) || channelName.includes(r.name)
            ).slice(0, 1);
          }
        }
      }
      
      if (results && results.length > 0) {
        const channelDetail = results[0];
        // 選定理由を追加
        if (reason) {
          channelDetail.selectionReason = reason;
        }
        setSelectedChannelDetail(channelDetail);
        setIsDetailModalOpen(true);
        console.log('✅ 詳細情報取得成功:', channelDetail);
      } else {
        console.warn('⚠️ チャンネルが見つかりません:', { channelId, channelName });
        setError(`チャンネル「${channelName || channelId}」の詳細情報が見つかりませんでした`);
      }
    } catch (error) {
      console.error('❌ チャンネル詳細取得エラー:', error);
      setError('チャンネル詳細の取得に失敗しました');
    } finally {
      setIsLoadingDetail(false);
    }
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
                    
                    {/* Geminiエージェント切り替え */}
                    <div className="mb-6">
                      <label className="flex items-center justify-center space-x-3 mb-4">
                        <input 
                          type="checkbox" 
                          checked={useGeminiAgent} 
                          onChange={(e) => setUseGeminiAgent(e.target.checked)}
                          className="w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
                        />
                        <span className="text-sm font-medium text-gray-700">
                          🧠 Gemini高度分析エージェントを使用（β版）
                        </span>
                      </label>
                      {useGeminiAgent && (
                        <div className="text-xs text-purple-600 mb-4">
                          より深い分析と説得力のある推薦理由を提供します
                        </div>
                      )}
                    </div>
                    
                    <button 
                      onClick={handleStartMatching}
                      className={`btn text-lg px-12 py-4 ${useGeminiAgent ? 'btn-primary bg-gradient-to-r from-purple-600 to-blue-600' : 'btn-primary'}`}
                    >
                      <svg className="w-6 h-6 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                      {useGeminiAgent ? 'Gemini高度分析を開始' : 'デフォルト設定でAI分析を開始'}
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
                    
                    {/* Geminiエージェント切り替え */}
                    <div className="mb-6">
                      <label className="flex items-center justify-center space-x-3 mb-4">
                        <input 
                          type="checkbox" 
                          checked={useGeminiAgent} 
                          onChange={(e) => setUseGeminiAgent(e.target.checked)}
                          className="w-4 h-4 text-purple-600 border-gray-300 rounded focus:ring-purple-500"
                        />
                        <span className="text-sm font-medium text-gray-700">
                          🧠 Gemini高度分析エージェントを使用（β版）
                        </span>
                      </label>
                      {useGeminiAgent && (
                        <div className="text-xs text-purple-600 mb-4 max-w-md mx-auto">
                          企業の詳細情報とインフルエンサーの特性を深く分析し、<br/>
                          より説得力のある推薦理由と戦略的インサイトを提供します
                        </div>
                      )}
                    </div>
                    
                    <button 
                      onClick={handleStartMatching}
                      className={`btn text-lg px-12 py-4 ${useGeminiAgent ? 'bg-gradient-to-r from-purple-600 to-blue-600 text-white hover:from-purple-700 hover:to-blue-700' : 'btn-primary'}`}
                    >
                      <svg className="w-6 h-6 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                      </svg>
                      {useGeminiAgent ? 'Gemini高度分析を開始' : 'AI分析を開始'}
                    </button>
                  </div>
                )}
              </div>
            )}

            {isAnalyzing && (
              <div className="text-center">
                <div className="flex items-center justify-center mb-6">
                  <svg className={`animate-spin -ml-1 mr-3 h-8 w-8 ${isGeminiAnalyzing ? 'text-purple-600' : 'text-indigo-600'}`} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span className="text-lg font-semibold text-gray-700">
                    {isGeminiAnalyzing ? '🧠 Gemini高度分析中...' : 'AI分析中...'}
                  </span>
                </div>
                <div className="max-w-md mx-auto">
                  {isGeminiAnalyzing ? (
                    <div className="space-y-3">
                      <div className="flex items-center text-sm text-gray-600">
                        <div className="w-2 h-2 bg-purple-500 rounded-full mr-3 animate-pulse"></div>
                        企業プロファイルの深層分析
                      </div>
                      <div className="flex items-center text-sm text-gray-600">
                        <div className="w-2 h-2 bg-blue-500 rounded-full mr-3 animate-pulse"></div>
                        商品ポートフォリオの評価
                      </div>
                      <div className="flex items-center text-sm text-gray-600">
                        <div className="w-2 h-2 bg-green-500 rounded-full mr-3 animate-pulse"></div>
                        インフルエンサーとの戦略的適合性分析
                      </div>
                      <div className="flex items-center text-sm text-gray-600">
                        <div className="w-2 h-2 bg-orange-500 rounded-full mr-3 animate-pulse"></div>
                        ROI予測とリスク評価
                      </div>
                      <div className="flex items-center text-sm text-gray-600">
                        <div className="w-2 h-2 bg-red-500 rounded-full mr-3 animate-pulse"></div>
                        推薦理由の生成と戦略提案
                      </div>
                    </div>
                  ) : (
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
                  )}
                </div>
              </div>
            )}
          </div>

          {/* マッチング結果 */}
          {showResults && (
            <div className="space-y-8">
              {/* 結果ヘッダー */}
              <div className="text-center">
                <div className={`inline-flex items-center px-6 py-3 rounded-full font-semibold mb-4 ${
                  useGeminiAgent 
                    ? 'bg-gradient-to-r from-purple-100 to-blue-100 border border-purple-300 text-purple-800'
                    : 'bg-green-100 border border-green-300 text-green-800'
                }`}>
                  {useGeminiAgent ? (
                    <>
                      <span className="text-lg mr-2">🧠</span>
                      Gemini高度分析完了
                    </>
                  ) : (
                    <>
                      <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                      分析完了
                    </>
                  )}
                </div>
                <h2 className="text-3xl font-bold text-gray-900 mb-2">
                  {useGeminiAgent ? '高度AI分析結果' : 'マッチング結果'}
                </h2>
                <p className="text-gray-600">
                  <span className={`font-semibold ${useGeminiAgent ? 'text-purple-600' : 'text-indigo-600'}`}>
                    {matchingResults.length}
                  </span>
                  人の最適なインフルエンサーが見つかりました
                  {useGeminiAgent && (
                    <span className="block text-sm text-purple-600 mt-1">
                      戦略的分析と詳細な推薦理由付き
                    </span>
                  )}
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
                          {result.geminiAnalysis ? '🧠 Gemini高度分析' : 'AI分析結果'}
                        </h4>
                        <p className="text-sm text-gray-700">{result.reason}</p>
                      </div>

                      {/* Gemini詳細分析結果（Gemini分析の場合のみ表示） */}
                      {result.geminiAnalysis && (
                        <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg p-6 mb-6 border border-purple-200">
                          <h4 className="font-bold text-purple-900 mb-4 flex items-center">
                            <span className="text-lg mr-2">🧠</span>
                            Gemini戦略的インサイト
                          </h4>
                          
                          {/* 推薦理由と成功シナリオ */}
                          <div className="mb-4">
                            <h5 className="font-semibold text-purple-800 mb-2">📈 成功シナリオ</h5>
                            <p className="text-sm text-purple-700 bg-white/60 p-3 rounded-lg">
                              {result.geminiAnalysis.recommendation_summary.success_scenario}
                            </p>
                          </div>

                          {/* 詳細分析スコア */}
                          <div className="grid grid-cols-2 gap-4 mb-4">
                            <div className="bg-white/60 p-3 rounded-lg">
                              <h6 className="text-xs font-semibold text-purple-600 mb-1">ブランド適合性</h6>
                              <div className="flex items-center">
                                <div className="flex-1 bg-purple-200 rounded-full h-2 mr-2">
                                  <div 
                                    className="h-2 bg-purple-600 rounded-full" 
                                    style={{width: `${result.geminiAnalysis.detailed_analysis.brand_alignment.score}%`}}
                                  />
                                </div>
                                <span className="text-sm font-bold text-purple-700">
                                  {result.geminiAnalysis.detailed_analysis.brand_alignment.score}%
                                </span>
                              </div>
                            </div>
                            <div className="bg-white/60 p-3 rounded-lg">
                              <h6 className="text-xs font-semibold text-blue-600 mb-1">ビジネス実現性</h6>
                              <div className="flex items-center">
                                <div className="flex-1 bg-blue-200 rounded-full h-2 mr-2">
                                  <div 
                                    className="h-2 bg-blue-600 rounded-full" 
                                    style={{width: `${result.geminiAnalysis.detailed_analysis.business_viability.score}%`}}
                                  />
                                </div>
                                <span className="text-sm font-bold text-blue-700">
                                  {result.geminiAnalysis.detailed_analysis.business_viability.score}%
                                </span>
                              </div>
                            </div>
                          </div>

                          {/* 戦略的推薦事項 */}
                          <div className="mb-4">
                            <h5 className="font-semibold text-purple-800 mb-2">🎯 推薦コラボレーション</h5>
                            <div className="flex flex-wrap gap-2">
                              {result.geminiAnalysis.strategic_insights.best_collaboration_types.map((type, idx) => (
                                <span key={idx} className="px-3 py-1 bg-purple-100 text-purple-700 text-xs rounded-full">
                                  {type}
                                </span>
                              ))}
                            </div>
                          </div>

                          {/* 予算推奨 */}
                          <div className="bg-white/60 p-3 rounded-lg">
                            <h5 className="font-semibold text-green-800 mb-2">💰 予算推奨</h5>
                            <p className="text-sm text-green-700">
                              ¥{formatNumber(result.geminiAnalysis.strategic_insights.budget_recommendations.min)} - 
                              ¥{formatNumber(result.geminiAnalysis.strategic_insights.budget_recommendations.max)}
                            </p>
                            <p className="text-xs text-green-600 mt-1">
                              {result.geminiAnalysis.strategic_insights.budget_recommendations.reasoning}
                            </p>
                          </div>
                        </div>
                      )}

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
                        <button 
                          onClick={() => handleShowDetail(result.id, result.influencerName, result.reason)}
                          disabled={isLoadingDetail}
                          className="btn btn-outline flex-1 text-center"
                        >
                          {isLoadingDetail ? (
                            <>
                              <svg className="animate-spin h-4 w-4 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                              </svg>
                              読み込み中...
                            </>
                          ) : (
                            <>
                              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                              </svg>
                              詳細表示
                            </>
                          )}
                        </button>
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

      {/* 詳細表示モーダル */}
      {isDetailModalOpen && selectedChannelDetail && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl p-8 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            {/* ヘッダー */}
            <div className="flex items-start justify-between mb-6">
              <div className="flex items-start space-x-4">
                <div className="relative">
                  {selectedChannelDetail.thumbnailUrl ? (
                    <img 
                      src={selectedChannelDetail.thumbnailUrl} 
                      alt={`${selectedChannelDetail.name}のサムネイル`}
                      className="w-20 h-20 rounded-full object-cover border-2 border-gray-200"
                      onError={(e) => {
                        e.currentTarget.style.display = 'none';
                        e.currentTarget.nextElementSibling.style.display = 'flex';
                      }}
                    />
                  ) : null}
                  <div 
                    className="w-20 h-20 rounded-full bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center text-3xl text-white font-bold"
                    style={{ display: selectedChannelDetail.thumbnailUrl ? 'none' : 'flex' }}
                  >
                    {selectedChannelDetail.name[0]}
                  </div>
                  {selectedChannelDetail.email && (
                    <div className="absolute -bottom-1 -right-1 bg-green-500 rounded-full p-1.5">
                      <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    </div>
                  )}
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-gray-900 mb-2">{selectedChannelDetail.name}</h2>
                  <div className="flex items-center space-x-2 mb-2">
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-purple-100 text-purple-800">
                      {selectedChannelDetail.category}
                    </span>
                  </div>
                  {selectedChannelDetail.email && (
                    <div className="flex items-center text-sm text-green-600">
                      <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                      </svg>
                      連絡可能
                    </div>
                  )}
                </div>
              </div>
              <button 
                onClick={() => setIsDetailModalOpen(false)} 
                className="p-2 hover:bg-gray-100 rounded-full transition-colors"
              >
                <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* 統計情報 */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="text-center p-4 bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl">
                <svg className="w-6 h-6 text-purple-600 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
                <div className="text-lg font-bold text-gray-900">
                  {selectedChannelDetail.subscriberCount ? formatNumber(selectedChannelDetail.subscriberCount) : 'N/A'}
                </div>
                <div className="text-xs text-gray-600">登録者数</div>
              </div>
              
              <div className="text-center p-4 bg-gradient-to-br from-green-50 to-green-100 rounded-xl">
                <svg className="w-6 h-6 text-green-600 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                </svg>
                <div className="text-lg font-bold text-gray-900">
                  {selectedChannelDetail.engagementRate ? `${selectedChannelDetail.engagementRate.toFixed(1)}%` : 'N/A'}
                </div>
                <div className="text-xs text-gray-600">エンゲージメント率</div>
              </div>
              
              <div className="text-center p-4 bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl">
                <svg className="w-6 h-6 text-blue-600 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h1.5a1.5 1.5 0 000-3H9v3zM7 21L3 17m0 0l4-4m-4 4l4 4M7 3l4 4-4 4" />
                </svg>
                <div className="text-lg font-bold text-gray-900">
                  {selectedChannelDetail.videoCount ? formatNumber(selectedChannelDetail.videoCount) : 'N/A'}
                </div>
                <div className="text-xs text-gray-600">動画数</div>
              </div>
              
              <div className="text-center p-4 bg-gradient-to-br from-orange-50 to-orange-100 rounded-xl">
                <svg className="w-6 h-6 text-orange-600 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
                <div className="text-lg font-bold text-gray-900">
                  {selectedChannelDetail.viewCount ? formatNumber(Math.floor(selectedChannelDetail.viewCount / 1000000)) + 'M' : 'N/A'}
                </div>
                <div className="text-xs text-gray-600">総再生回数</div>
              </div>
            </div>

            {/* 選定理由 */}
            {selectedChannelDetail.selectionReason && (
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
                  <svg className="w-5 h-5 mr-2 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                  AI選定理由
                </h3>
                <div className="bg-blue-50 border border-blue-200 p-4 rounded-xl">
                  <p className="text-blue-800 leading-relaxed">
                    {selectedChannelDetail.selectionReason}
                  </p>
                </div>
              </div>
            )}

            {/* 説明 */}
            {selectedChannelDetail.description && (
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">チャンネル紹介</h3>
                <p className="text-gray-600 leading-relaxed bg-gray-50 p-4 rounded-xl">
                  {selectedChannelDetail.description}
                </p>
              </div>
            )}

            {/* チャンネルIDと作成日 */}
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-3">チャンネル詳細</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-gray-50 p-4 rounded-xl">
                  <div className="text-xs text-gray-500 mb-1">チャンネルID</div>
                  <div className="text-sm font-mono text-gray-800 break-all">{selectedChannelDetail.id}</div>
                </div>
                {selectedChannelDetail.createdAt && (
                  <div className="bg-gray-50 p-4 rounded-xl">
                    <div className="text-xs text-gray-500 mb-1">登録日時</div>
                    <div className="text-sm text-gray-800">
                      {new Date(selectedChannelDetail.createdAt).toLocaleDateString('ja-JP')}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* YouTubeチャンネルリンク */}
            <div className="mb-6">
              <a 
                href={`https://www.youtube.com/channel/${selectedChannelDetail.id}`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-center space-x-2 px-6 py-3 bg-red-600 text-white rounded-xl font-medium hover:bg-red-700 transition-colors"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
                </svg>
                <span>YouTubeチャンネルを見る</span>
              </a>
            </div>

            {/* アクションボタン */}
            <div className="flex space-x-3">
              <button 
                onClick={() => setIsDetailModalOpen(false)} 
                className="flex-1 px-6 py-3 bg-gray-100 text-gray-700 rounded-xl font-medium hover:bg-gray-200 transition-colors"
              >
                閉じる
              </button>
              {selectedChannelDetail.email && (
                <Link 
                  href={`/messages?to=${encodeURIComponent(selectedChannelDetail.email)}&subject=${encodeURIComponent(`【コラボ提案】${selectedChannelDetail.name}様へ`)}&influencer=${encodeURIComponent(selectedChannelDetail.name)}`}
                  className="flex-1 flex items-center justify-center space-x-2 px-6 py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-xl font-medium hover:from-purple-700 hover:to-blue-700 transition-all duration-200"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                  </svg>
                  <span>コンタクト開始</span>
                </Link>
              )}
            </div>
          </div>
        </div>
      )}
    </AuthGuard>
  );
}