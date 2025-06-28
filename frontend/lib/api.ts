/**
 * API Client for InfuMatch Backend
 * 
 * @description バックエンドAPIとの通信を管理するクライアント
 * @author InfuMatch Development Team
 * @version 1.0.0
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

// API レスポンスの型定義
export interface Influencer {
  id: string;
  name: string;
  channelId: string;
  subscriberCount: number;
  viewCount: number;
  videoCount: number;
  category: string;
  description: string;
  thumbnailUrl: string;
  engagementRate: number;
  email?: string;
  aiAnalysis?: {
    target_age?: string;
    top_product?: string;
    match_score?: number;
    safety_score?: number;
  };
  brandSafetyScore?: number;
  selectionReason?: string; // AI選定理由
  createdAt?: string; // チャンネル作成日
}

export interface ChannelResearchRequest {
  channel_id: string;
  channel_title: string;
  channel_data?: any;
  research_categories?: string[];
}

export interface ChannelResearchResponse {
  success: boolean;
  channel_id: string;
  channel_name: string;
  research_timestamp: string;
  basic_info: {
    latest_activity: string;
    growth_trend: string;
    popular_content: string;
    recent_news: string;
    current_status: string;
    activity_level: string;
    last_updated: string;
  };
  reputation_safety: {
    controversy_history: string;
    public_reputation: string;
    brand_risk_level: string;
    content_appropriateness: string;
    safety_score: number;
    risk_factors: string[];
    safety_recommendations: string;
  };
  collaboration_history: {
    collaboration_count: string;
    major_collaborations: string[];
    pr_frequency: string;
    collaboration_types: string[];
    estimated_rates: string;
    collaboration_style: string;
    success_indicators: string;
  };
  market_analysis: {
    market_position: string;
    competitors: string[];
    market_share: string;
    differentiation: string;
    growth_potential: string;
    market_value: string;
    trending_topics: string;
  };
  research_confidence: number;
  summary: string;
  message: string;
}

export interface SearchParams {
  channel_id?: string;
  keyword?: string;
  category?: string;
  min_subscribers?: number;
  max_subscribers?: number;
}

export interface CampaignRequest {
  product_name: string;
  product_details?: Array<{
    name: string;
    category: string;
    targetAudience: string;
    description: string;
    priceRange: string;
  }>;
  company_name?: string;
  company_industry?: string;
  company_description?: string;
  budget_min: number;
  budget_max: number;
  target_audience: string[];
  required_categories: string[];
  exclude_categories?: string[];
  campaign_goals: string;
  min_engagement_rate?: number;
  min_subscribers?: number;
  max_subscribers?: number;
  geographic_focus?: string;
  priority_keywords?: string[];
  exclude_keywords?: string[];
  negotiation_tone?: string;
  key_priorities?: string[];
  special_instructions?: string;
}

export interface AIRecommendation {
  channel_id: string;
  overall_score: number;
  detailed_scores: {
    category_match: number;
    engagement: number;
    audience_fit: number;
    budget_fit: number;
    availability: number;
    risk: number;
  };
  explanation: string;
  rank: number;
}

export interface AIRecommendationResponse {
  success: boolean;
  recommendations: AIRecommendation[];
  ai_evaluation: {
    recommendation_quality: string;
    expected_roi: string;
    portfolio_balance: string;
    key_strengths: string[];
    concerns: string[];
    optimization_suggestions: string[];
  };
  portfolio_optimization: {
    optimized_portfolio: AIRecommendation[];
    optimization_strategy: string;
    diversity_score: number;
  };
  matching_summary: {
    total_candidates: number;
    filtered_candidates: number;
    final_recommendations: number;
    criteria_used: any;
  };
  agent: string;
  timestamp: string;
}

export interface APIError {
  detail: string;
  status: number;
}

export interface CollaborationProposalRequest {
  influencer: Influencer;
  user_settings?: any;
}

export interface CollaborationProposalResponse {
  success: boolean;
  message: string;
  metadata?: {
    personalization_score?: number;
    agent?: string;
    campaign_info?: any;
    type?: string;
  };
}

// Geminiマッチングエージェント用の型定義
export interface GeminiMatchingRequest {
  company_profile: {
    name: string;
    industry: string;
    description: string;
    brand_values: string[];
    target_demographics: string[];
    communication_style: string;
    previous_campaigns?: string[];
  };
  product_portfolio: {
    products: Array<{
      name: string;
      category: string;
      description: string;
      target_audience: string;
      price_range: string;
      unique_selling_points: string[];
      marketing_goals: string[];
    }>;
  };
  campaign_objectives: {
    primary_goals: string[];
    success_metrics: string[];
    budget_range: { min: number; max: number };
    timeline: string;
    geographic_focus: string[];
  };
  influencer_preferences: {
    preferred_categories: string[];
    avoid_categories: string[];
    min_engagement_rate: number;
    subscriber_range: { min: number; max: number };
    content_style_preferences: string[];
    collaboration_types: string[];
    custom_preference?: string;
  };
}

export interface GeminiAnalysisResult {
  influencer_id: string;
  influencer_data?: {
    channel_id: string;
    channel_name: string;
    channel_title: string;
    description: string;
    subscriber_count: number;
    video_count: number;
    view_count: number;
    engagement_rate: number;
    thumbnail_url: string;
    category: string;
    email?: string;
  };
  overall_compatibility_score: number; // 0-100
  detailed_analysis: {
    brand_alignment: {
      score: number;
      reasoning: string;
      key_strengths: string[];
      potential_concerns: string[];
    };
    audience_synergy: {
      score: number;
      demographic_overlap: string;
      engagement_quality: string;
      conversion_potential: string;
    };
    content_fit: {
      score: number;
      style_compatibility: string;
      content_themes_match: string[];
      creative_opportunities: string[];
    };
    business_viability: {
      score: number;
      roi_prediction: string;
      risk_assessment: string;
      long_term_potential: string;
    };
  };
  recommendation_summary: {
    confidence_level: 'High' | 'Medium' | 'Low';
    primary_recommendation_reason: string;
    success_scenario: string;
    collaboration_strategy: string;
    expected_outcomes: string[];
  };
  strategic_insights: {
    best_collaboration_types: string[];
    optimal_campaign_timing: string;
    content_suggestions: string[];
    budget_recommendations: { min: number; max: number; reasoning: string };
  };
}

export interface GeminiMatchingResponse {
  success: boolean;
  analysis_results: GeminiAnalysisResult[];
  portfolio_insights: {
    overall_strategy_score: number;
    portfolio_balance: string;
    diversity_analysis: string;
    optimization_suggestions: string[];
  };
  market_context: {
    industry_trends: string[];
    competitive_landscape: string;
    timing_considerations: string;
  };
  processing_metadata: {
    analysis_duration_ms: number;
    confidence_score: number;
    gemini_model_used: string;
    analysis_timestamp: string;
  };
}

class APIClient {
  private baseURL: string;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  /**
   * 汎用的なAPIリクエスト関数
   */
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    
    console.log('[API Request]', {
      method: options.method || 'GET',
      url,
      endpoint,
      baseURL: this.baseURL
    });
    
    try {
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...options,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        console.error('[API Error Response]', {
          status: response.status,
          statusText: response.statusText,
          errorData,
          url
        });
        throw new APIError(
          errorData.detail || `HTTP ${response.status}: ${response.statusText}`,
          response.status
        );
      }

      const data = await response.json();
      console.log('[API Success Response]', { url, data });
      return data;
    } catch (error) {
      if (error instanceof APIError) {
        throw error;
      }
      
      // ネットワークエラーやその他のエラー
      console.error('[API Request Failed]', {
        error,
        errorMessage: error instanceof Error ? error.message : 'Unknown error',
        errorType: error instanceof Error ? error.constructor.name : typeof error,
        url,
        endpoint,
        baseURL: this.baseURL
      });
      
      // より詳細なエラーメッセージ
      const errorMessage = error instanceof Error 
        ? `ネットワークエラー: ${error.message}`
        : 'ネットワークエラーまたはサーバーに接続できません';
        
      throw new APIError(errorMessage, 0);
    }
  }

  /**
   * インフルエンサー検索API
   */
  async searchInfluencers(params: SearchParams = {}): Promise<Influencer[]> {
    const searchParams = new URLSearchParams();
    
    if (params.channel_id) {
      searchParams.append('channel_id', params.channel_id);
    }
    if (params.keyword) {
      searchParams.append('keyword', params.keyword);
    }
    if (params.category && params.category !== 'all') {
      searchParams.append('category', params.category);
    }
    if (params.min_subscribers) {
      searchParams.append('min_subscribers', params.min_subscribers.toString());
    }
    if (params.max_subscribers) {
      searchParams.append('max_subscribers', params.max_subscribers.toString());
    }

    const query = searchParams.toString();
    const endpoint = `/api/v1/influencers${query ? `?${query}` : ''}`;
    
    // Cloud Runバックエンドのレスポンス形式に対応
    const response = await this.request<{success: boolean, data: any[], metadata?: any}>(endpoint);
    
    // デバッグログを追加
    console.log('[searchInfluencers] Full response:', response);
    console.log('[searchInfluencers] Response type:', typeof response);
    console.log('[searchInfluencers] Has data property:', response && 'data' in response);
    
    // dataプロパティが存在する場合はそれを返す、なければそのまま返す
    if (response && typeof response === 'object' && 'data' in response) {
      console.log('[searchInfluencers] Processing data array:', response.data);
      const mappedData = response.data.map((item: any, index: number) => {
        // AI分析データの安全な抽出
        let aiAnalysis = {};
        let brandSafetyScore = 0;
        
        if (item.ai_analysis && typeof item.ai_analysis === 'object') {
          const ai = item.ai_analysis;
          
          // ネストされたオブジェクトから安全に値を抽出
          aiAnalysis = {
            target_age: ai.advanced?.target_age || ai.full_analysis?.category_tags?.target_age_group || '',
            top_product: ai.advanced?.top_product || ai.full_analysis?.product_matching?.recommended_products?.[0]?.category || '',
            match_score: ai.advanced?.match_score || ai.match_score || 0,
            safety_score: ai.advanced?.safety_score || ai.brand_safety_score || 0
          };
          
          brandSafetyScore = ai.brand_safety_score || ai.advanced?.safety_score || 0;
        }
        
        const mapped = {
          id: item.id || `${index}`,
          name: item.channel_name || item.name || 'Unknown Channel',
          channelId: item.channel_id || item.id || '',
          subscriberCount: item.subscriber_count || item.subscriberCount || 0,
          viewCount: item.view_count || item.viewCount || 0,
          videoCount: item.video_count || item.videoCount || 0,
          category: item.category || '一般',
          description: item.description || '',
          thumbnailUrl: item.thumbnail_url || item.thumbnailUrl || '',
          engagementRate: item.engagement_rate || item.engagementRate || 0,
          email: item.email || '',
          aiAnalysis: aiAnalysis,
          brandSafetyScore: brandSafetyScore
        };
        
        // 各アイテムのマッピング結果をログ出力
        if (index < 3) {
          console.log(`[searchInfluencers] Item ${index} mapping:`, {
            original_ai_analysis: item.ai_analysis,
            mapped_ai_analysis: aiAnalysis,
            mapped: mapped
          });
        }
        
        return mapped;
      });
      
      console.log('[searchInfluencers] Mapped data:', mappedData);
      return mappedData;
    }
    
    // データ形式が期待されるものと異なる場合はエラーを発生
    console.error('[searchInfluencers] Unexpected response format:', response);
    throw new APIError('API response format is invalid - expected {success: boolean, data: array}', 500);
  }

  /**
   * インフルエンサー詳細取得API
   */
  async getInfluencerDetail(influencerId: string): Promise<Influencer> {
    return this.request<Influencer>(`/api/v1/influencers/${influencerId}`);
  }

  /**
   * ヘルスチェックAPI
   */
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    return this.request<{ status: string; timestamp: string }>('/health');
  }

  /**
   * AI推薦API
   */
  async getAIRecommendations(campaign: CampaignRequest): Promise<AIRecommendationResponse> {
    return this.request<AIRecommendationResponse>('/api/v1/ai/recommendations', {
      method: 'POST',
      body: JSON.stringify(campaign),
    });
  }

  /**
   * コラボ提案メッセージ生成API
   */
  async generateCollaborationProposal(
    influencer: Influencer, 
    userSettings?: any
  ): Promise<CollaborationProposalResponse> {
    const requestData: CollaborationProposalRequest = {
      influencer,
      user_settings: userSettings
    };
    
    return this.request<CollaborationProposalResponse>('/api/v1/collaboration-proposal', {
      method: 'POST',
      body: JSON.stringify(requestData),
    });
  }

  /**
   * AI推薦API（GET版）
   */
  async getAIRecommendationsQuery(params: {
    product_name: string;
    budget_min: number;
    budget_max: number;
    target_audience: string;
    required_categories: string;
    campaign_goals: string;
    min_engagement_rate?: number;
    min_subscribers?: number;
    max_subscribers?: number;
    max_recommendations?: number;
  }): Promise<AIRecommendationResponse> {
    const searchParams = new URLSearchParams();
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, value.toString());
      }
    });

    const endpoint = `/api/v1/ai/recommendations?${searchParams.toString()}`;
    return this.request<AIRecommendationResponse>(endpoint);
  }

  /**
   * 単一マッチ評価API
   */
  async evaluateInfluencerMatch(influencerId: string, campaign: CampaignRequest): Promise<any> {
    return this.request<any>('/api/v1/ai/match-evaluation', {
      method: 'POST',
      body: JSON.stringify({
        influencer_id: influencerId,
        campaign: campaign
      }),
    });
  }

  /**
   * AIエージェントステータス確認API
   */
  async getAIAgentsStatus(): Promise<any> {
    return this.request<any>('/api/v1/ai/agents/status');
  }

  /**
   * チャンネル包括的調査API
   */
  async researchChannel(request: ChannelResearchRequest): Promise<ChannelResearchResponse> {
    return this.request<ChannelResearchResponse>('/api/channel-research/research', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  /**
   * チャンネルクイック調査API
   */
  async quickResearchChannel(request: ChannelResearchRequest): Promise<any> {
    return this.request<any>('/api/channel-research/research/quick', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  /**
   * 調査カテゴリ一覧取得API
   */
  async getResearchCategories(): Promise<any> {
    return this.request<any>('/api/channel-research/research/categories');
  }

  /**
   * Geminiマッチングエージェント - 高度な分析API
   */
  async getGeminiMatching(request: GeminiMatchingRequest): Promise<GeminiMatchingResponse> {
    return this.request<GeminiMatchingResponse>('/api/v1/ai/gemini-matching', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  /**
   * Geminiマッチングエージェント - ストリーミング分析API（リアルタイム結果）
   */
  async getGeminiMatchingStream(request: GeminiMatchingRequest): Promise<ReadableStream<GeminiAnalysisResult>> {
    const response = await fetch(`${this.baseURL}/api/v1/ai/gemini-matching/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new APIError(`HTTP ${response.status}: ${response.statusText}`, response.status);
    }

    return response.body as ReadableStream<GeminiAnalysisResult>;
  }
}

// API クライアントのシングルトンインスタンス
export const apiClient = new APIClient();

// 便利関数
export const searchInfluencers = (params: SearchParams) => 
  apiClient.searchInfluencers(params);

export const getInfluencerDetail = (id: string) => 
  apiClient.getInfluencerDetail(id);

export const checkAPIHealth = () => 
  apiClient.healthCheck();

export const getAIRecommendations = (campaign: CampaignRequest) =>
  apiClient.getAIRecommendations(campaign);

export const evaluateInfluencerMatch = (influencerId: string, campaign: CampaignRequest) =>
  apiClient.evaluateInfluencerMatch(influencerId, campaign);

export const getAIAgentsStatus = () =>
  apiClient.getAIAgentsStatus();

export const generateCollaborationProposal = (influencer: Influencer, userSettings?: any) =>
  apiClient.generateCollaborationProposal(influencer, userSettings);

export const researchChannel = (request: ChannelResearchRequest) =>
  apiClient.researchChannel(request);

export const quickResearchChannel = (request: ChannelResearchRequest) =>
  apiClient.quickResearchChannel(request);

export const getResearchCategories = () =>
  apiClient.getResearchCategories();

// エラーハンドリング用のカスタムエラークラス
export class APIError extends Error {
  public status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = 'APIError';
    this.status = status;
  }
}