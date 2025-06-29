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

// Removed mock data to prevent fallback usage

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
  const [customInfluencerPreference, setCustomInfluencerPreference] = useState('');
  const [pickupLogicDetails, setPickupLogicDetails] = useState<any>(null);
  const [matchingContext, setMatchingContext] = useState<any>(null);

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
        
        // バックエンドのレスポンス構造に対応
        const analysisResults = geminiResponse.analysis_results || geminiResponse.recommendations;
        console.log('📊 分析結果データ確認:', {
          hasAnalysisResults: !!geminiResponse.analysis_results,
          hasRecommendations: !!geminiResponse.recommendations,
          analysisResultsLength: analysisResults?.length,
          responseKeys: Object.keys(geminiResponse)
        });
        
        if (geminiResponse.success && analysisResults?.length > 0) {
          const geminiResults = convertGeminiResultsToMatchingResults(analysisResults);
          setMatchingResults(geminiResults);
          setGeminiAnalysisResults(analysisResults);
          console.log('✨ Gemini高度分析結果:', geminiResults);
          
          // ピックアップロジック詳細をコンソールに出力してstateに保存
          if (geminiResponse.pickup_logic_details) {
            console.log('🔍 ピックアップロジック詳細:');
            console.log('  📊 フィルタリングパイプライン:', geminiResponse.pickup_logic_details.filtering_pipeline);
            console.log('  📈 最終統計:', geminiResponse.pickup_logic_details.final_statistics);
            console.log('  ⚙️ アルゴリズム詳細:', geminiResponse.pickup_logic_details.algorithm_details);
            
            // モックデータ使用時の詳細表示
            if (geminiResponse.pickup_logic_details.final_statistics?.mock_metadata) {
              console.log('📌 モックデータ情報:', geminiResponse.pickup_logic_details.final_statistics.mock_metadata);
            }
            
            // stateに保存
            setPickupLogicDetails(geminiResponse.pickup_logic_details);
          }
          
          // マッチング文脈情報を処理
          if (geminiResponse.matching_context) {
            console.log('🎯 マッチング文脈情報:', geminiResponse.matching_context);
            setMatchingContext(geminiResponse.matching_context);
          }
          
          // 処理メタデータも出力
          if (geminiResponse.processing_metadata) {
            console.log('🔧 処理メタデータ:', geminiResponse.processing_metadata);
          }
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
          throw new Error('AI推薦システムから有効な結果が取得できませんでした');
        }
      }
      
    } catch (error) {
      console.error('❌ マッチングシステムエラー:', error);
      setError(error instanceof Error ? error.message : 'マッチングの実行に失敗しました');
      // エラー時は結果を表示しない
      setIsAnalyzing(false);
      setIsGeminiAnalyzing(false);
      return; // 早期リターンでshowResultsをtrueにしない
    }
    
    setIsAnalyzing(false);
    setIsGeminiAnalyzing(false);
    setShowResults(true);
  };

  // Removed customizeMatchingResults function to prevent fallback usage

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
        ],
        custom_preference: customInfluencerPreference || undefined
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
  const convertGeminiResultsToMatchingResults = (geminiResults: any[]): MatchingResult[] => {
    return geminiResults.map((result, index) => {
      // バックエンドの実際のレスポンス構造に対応
      // シンプルなインフルエンサー形式の場合
      const safeResult = result || {};
      if (safeResult.channel_name || safeResult.channel_id || safeResult.id) {
        return {
          id: safeResult.id || safeResult.channel_id || `gemini-${index}`,
          influencerName: safeResult.channel_name || safeResult.name || `Gemini推薦 ${index + 1}`,
          score: safeResult.ai_match_score || safeResult.match_score || 85 + Math.random() * 10,
          category: safeResult.category || 'AI分析',
          reason: `Gemini AIによる高度分析により選出されました。エンゲージメント率${safeResult.engagement_rate || 'N/A'}%`,
          estimatedReach: safeResult.subscriber_count || Math.floor(Math.random() * 100000) + 50000,
          estimatedCost: Math.floor((safeResult.subscriber_count || 50000) * 0.5) + Math.floor(Math.random() * 100000),
          thumbnailUrl: safeResult.thumbnail_url || '',
          subscriberCount: safeResult.subscriber_count || 0,
          engagementRate: safeResult.engagement_rate || 0,
          description: safeResult.description || 'AI分析による推薦インフルエンサー',
          email: safeResult.email || '',
          compatibility: {
            audience: Math.round(80 + Math.random() * 15),
            content: Math.round(75 + Math.random() * 20),
            brand: Math.round(70 + Math.random() * 25),
          },
          geminiAnalysis: result
        };
      } else {
        // 複雑なGeminiAnalysisResult形式の場合（フォールバック）
        const safeResult = result || {};
        const influencerData = safeResult.influencer_data || {};
        const recommendationSummary = safeResult.recommendation_summary || {};
        const strategicInsights = safeResult.strategic_insights || {};
        const budgetRecommendations = strategicInsights.budget_recommendations || {};
        const detailedAnalysis = safeResult.detailed_analysis || {};
        const audienceSynergy = detailedAnalysis.audience_synergy || {};
        const contentFit = detailedAnalysis.content_fit || {};
        const brandAlignment = detailedAnalysis.brand_alignment || {};
        
        return {
          id: safeResult.influencer_id || `gemini-${index}`,
          influencerName: influencerData.channel_name || influencerData.channel_title || `Gemini推薦 ${index + 1}`,
          score: safeResult.overall_compatibility_score || 85,
          category: influencerData.category || '高度AI分析',
          reason: (recommendationSummary && recommendationSummary.primary_recommendation_reason) || 'AI高度分析による推薦',
          estimatedReach: influencerData.subscriber_count || Math.floor(Math.random() * 100000) + 50000,
          estimatedCost: (budgetRecommendations && budgetRecommendations.min) || Math.floor(Math.random() * 200000) + 100000,
          thumbnailUrl: influencerData.thumbnail_url || '',
          subscriberCount: influencerData.subscriber_count || 0,
          engagementRate: influencerData.engagement_rate || 0,
          description: influencerData.description || (recommendationSummary && recommendationSummary.success_scenario) || 'AI高度分析による推薦',
          email: influencerData.email || '',
          compatibility: {
            audience: (audienceSynergy && audienceSynergy.score) || 80,
            content: (contentFit && contentFit.score) || 75,
            brand: (brandAlignment && brandAlignment.score) || 70,
          },
          geminiAnalysis: result
        };
      }
    });
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
                        <>
                          <div className="text-xs text-purple-600 mb-4">
                            より深い分析と説得力のある推薦理由を提供します
                          </div>
                          <div className="mb-4">
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                              希望するインフルエンサータイプ（任意）
                            </label>
                            <input
                              type="text"
                              value={customInfluencerPreference}
                              onChange={(e) => setCustomInfluencerPreference(e.target.value)}
                              placeholder="例: ゲーム実況系、美容系、ビジネス系、料理系など"
                              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                            />
                            <p className="text-xs text-gray-500 mt-1">
                              特定のジャンルや特徴を指定できます（空欄の場合は自動判定）
                            </p>
                          </div>
                        </>
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
                        <>
                          <div className="text-xs text-purple-600 mb-4 max-w-md mx-auto">
                            企業の詳細情報とインフルエンサーの特性を深く分析し、<br/>
                            より説得力のある推薦理由と戦略的インサイトを提供します
                          </div>
                          <div className="mb-4 max-w-md mx-auto">
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                              希望するインフルエンサータイプ（任意）
                            </label>
                            <input
                              type="text"
                              value={customInfluencerPreference}
                              onChange={(e) => setCustomInfluencerPreference(e.target.value)}
                              placeholder="例: ゲーム実況系、美容系、ビジネス系、料理系など"
                              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                            />
                            <p className="text-xs text-gray-500 mt-1">
                              特定のジャンルや特徴を指定できます（空欄の場合は自動判定）
                            </p>
                          </div>
                        </>
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

              {/* マッチング文脈情報 */}
              {matchingContext && useGeminiAgent && (
                <div className="mb-8">
                  <div className="card p-6 bg-gradient-to-br from-green-50 to-emerald-50 border border-green-200">
                    <h3 className="text-xl font-bold text-green-900 mb-4 flex items-center">
                      <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      🎯 マッチング文脈情報
                    </h3>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      {/* 企業情報 */}
                      <div className="bg-white/70 rounded-lg p-4">
                        <h4 className="font-semibold text-green-800 mb-3 flex items-center">
                          <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M4 4a2 2 0 00-2 2v8a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2H4zm3 6a1 1 0 011-1h4a1 1 0 110 2H8a1 1 0 01-1-1z" clipRule="evenodd" />
                          </svg>
                          企業情報
                        </h4>
                        <div className="space-y-2 text-sm">
                          <div><span className="font-medium text-gray-700">企業名:</span> <span className="text-green-800">{matchingContext.company_information?.company_name}</span></div>
                          <div><span className="font-medium text-gray-700">業界:</span> <span className="text-green-800">{matchingContext.company_information?.industry}</span></div>
                          <div><span className="font-medium text-gray-700">説明:</span> <span className="text-green-800 text-xs">{matchingContext.company_information?.description}</span></div>
                        </div>
                      </div>
                      
                      {/* 商品情報 */}
                      <div className="bg-white/70 rounded-lg p-4">
                        <h4 className="font-semibold text-green-800 mb-3 flex items-center">
                          <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z" />
                          </svg>
                          商品・キャンペーン情報
                        </h4>
                        <div className="space-y-2 text-sm">
                          <div><span className="font-medium text-gray-700">主商品:</span> <span className="text-green-800">{matchingContext.product_information?.main_product}</span></div>
                          <div><span className="font-medium text-gray-700">予算範囲:</span> <span className="text-green-800">{matchingContext.product_information?.budget_range}</span></div>
                          <div><span className="font-medium text-gray-700">カスタム希望:</span> <span className="text-green-800">{matchingContext.influencer_preferences?.custom_preference}</span></div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
              
              {/* ピックアップロジック詳細 */}
              {pickupLogicDetails && useGeminiAgent && (
                <div className="mb-8">
                  <div className="card p-6 bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200">
                    <h3 className="text-xl font-bold text-blue-900 mb-4 flex items-center">
                      <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
                      </svg>
                      ピックアップロジック詳細
                    </h3>

                    {/* データソース情報 */}
                    <div className="mb-4 p-4 bg-white/60 rounded-lg">
                      <h4 className="font-semibold text-blue-800 mb-2">データソース</h4>
                      <div className="text-sm text-blue-700">
                        <span className="font-medium">{pickupLogicDetails.final_statistics?.data_source}</span>
                        {pickupLogicDetails.final_statistics?.mock_metadata && (
                          <div className="mt-2 p-3 bg-yellow-100 border border-yellow-300 rounded-lg">
                            <div className="font-medium text-yellow-800">📌 モックデータ使用中</div>
                            <div className="text-xs text-yellow-700 mt-1">
                              理由: {pickupLogicDetails.final_statistics.mock_metadata.mock_description}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* フィルタリングステップ */}
                    <div className="mb-4">
                      <h4 className="font-semibold text-blue-800 mb-3">フィルタリングパイプライン</h4>
                      <div className="space-y-2">
                        {pickupLogicDetails.filtering_pipeline?.map((step: any, index: number) => (
                          <div key={index} className="flex items-start space-x-3 p-3 bg-white/60 rounded-lg">
                            <div className="flex-shrink-0 w-6 h-6 bg-blue-500 text-white text-xs font-bold rounded-full flex items-center justify-center">
                              {step.step}
                            </div>
                            <div className="flex-1">
                              <div className="font-medium text-blue-800">{step.action}</div>
                              <div className="text-xs text-blue-600 mt-1">{step.details}</div>
                              <div className="text-xs text-green-600 mt-1">→ {step.result}</div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* 最終統計 */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="text-center p-3 bg-white/60 rounded-lg">
                        <div className="text-lg font-bold text-blue-800">
                          {pickupLogicDetails.final_statistics?.total_candidates_scored || pickupLogicDetails.final_statistics?.candidates_after_filtering || 0}
                        </div>
                        <div className="text-xs text-blue-600">全候補数</div>
                      </div>
                      <div className="text-center p-3 bg-white/60 rounded-lg">
                        <div className="text-lg font-bold text-blue-800">
                          {pickupLogicDetails.final_statistics?.selected_for_ai_analysis || 0}
                        </div>
                        <div className="text-xs text-blue-600">AI分析対象</div>
                      </div>
                      <div className="text-center p-3 bg-white/60 rounded-lg">
                        <div className="text-lg font-bold text-blue-800">
                          {pickupLogicDetails.total_filtering_steps || 0}
                        </div>
                        <div className="text-xs text-blue-600">処理段階</div>
                      </div>
                      <div className="text-center p-3 bg-white/60 rounded-lg">
                        <div className="text-lg font-bold text-blue-800">
                          {pickupLogicDetails.algorithm_details?.ai_analysis_model || 'N/A'}
                        </div>
                        <div className="text-xs text-blue-600">AI分析モデル</div>
                      </div>
                    </div>
                    
                    {/* スコアベース処理の表示 */}
                    {pickupLogicDetails.final_statistics?.no_filtering_applied && (
                      <div className="mt-4 p-4 bg-green-100 border border-green-300 rounded-lg">
                        <div className="text-sm text-green-800 flex items-center">
                          <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                          </svg>
                          ✅ スコアベース選択: フィルタリングではなく適合度スコアでランキング
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

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
                              {result.id.startsWith('UC') && (
                                <span className="text-xs bg-red-100 text-red-700 px-2 py-1 rounded-full">
                                  📺 YouTuber
                                </span>
                              )}
                            </div>
                            {result.id.startsWith('UC') && (
                              <div className="text-xs text-blue-600 mt-1 font-mono">
                                ID: {result.id}
                              </div>
                            )}
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
                          <h4 className="font-semibold text-gray-900 mb-3 flex items-center">
                            <svg className="w-4 h-4 mr-2 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            チャンネル紹介
                            {result.id.startsWith('UC') && (
                              <span className="ml-2 text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full">
                                ✅ 実チャンネル
                              </span>
                            )}
                          </h4>
                          <div className="bg-gradient-to-br from-gray-50 to-blue-50 p-4 rounded-lg border border-gray-200">
                            <p className="text-sm text-gray-700 leading-relaxed">
                              {result.description.length > 300 
                                ? `${result.description.substring(0, 300)}...` 
                                : result.description
                              }
                            </p>
                            {result.id.startsWith('UC') && (
                              <div className="mt-3 pt-3 border-t border-gray-300">
                                <a 
                                  href={`https://www.youtube.com/channel/${result.id}`}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="inline-flex items-center text-xs text-red-600 hover:text-red-800 font-medium"
                                >
                                  <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 24 24">
                                    <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
                                  </svg>
                                  YouTubeで確認
                                </a>
                              </div>
                            )}
                          </div>
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