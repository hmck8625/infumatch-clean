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
}

export interface SearchParams {
  keyword?: string;
  category?: string;
  min_subscribers?: number;
  max_subscribers?: number;
}

export interface CampaignRequest {
  product_name: string;
  budget_min: number;
  budget_max: number;
  target_audience: string[];
  required_categories: string[];
  campaign_goals: string;
  min_engagement_rate?: number;
  min_subscribers?: number;
  max_subscribers?: number;
  geographic_focus?: string;
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
    
    // フォールバック: 古い形式もサポート
    console.log('[searchInfluencers] Using fallback, returning response as-is:', response);
    return response as Influencer[];
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

// エラーハンドリング用のカスタムエラークラス
export class APIError extends Error {
  public status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = 'APIError';
    this.status = status;
  }
}