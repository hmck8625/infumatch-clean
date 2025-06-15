interface RateLimitConfig {
  maxRequests: number;
  windowMs: number;
  minInterval: number;
}

interface RequestRecord {
  timestamp: number;
  count: number;
}

class RateLimiter {
  private requests: Map<string, RequestRecord[]> = new Map();
  private lastRequestTime: Map<string, number> = new Map();
  private config: RateLimitConfig;

  constructor(config: RateLimitConfig) {
    this.config = config;
  }

  async checkRateLimit(key: string): Promise<{ allowed: boolean; retryAfter?: number }> {
    const now = Date.now();
    const windowStart = now - this.config.windowMs;

    // 現在のリクエスト履歴を取得
    let userRequests = this.requests.get(key) || [];
    
    // 期限切れのリクエストを削除
    userRequests = userRequests.filter(req => req.timestamp > windowStart);
    
    // 最小間隔チェック
    const lastRequest = this.lastRequestTime.get(key) || 0;
    const timeSinceLastRequest = now - lastRequest;
    
    if (timeSinceLastRequest < this.config.minInterval) {
      const retryAfter = this.config.minInterval - timeSinceLastRequest;
      return { allowed: false, retryAfter };
    }

    // リクエスト数チェック
    const totalRequests = userRequests.reduce((sum, req) => sum + req.count, 0);
    
    if (totalRequests >= this.config.maxRequests) {
      const oldestRequest = userRequests[0];
      const retryAfter = oldestRequest ? oldestRequest.timestamp + this.config.windowMs - now : this.config.windowMs;
      return { allowed: false, retryAfter: Math.max(retryAfter, 0) };
    }

    // リクエストを記録
    userRequests.push({ timestamp: now, count: 1 });
    this.requests.set(key, userRequests);
    this.lastRequestTime.set(key, now);

    return { allowed: true };
  }

  async waitForRateLimit(key: string): Promise<void> {
    const result = await this.checkRateLimit(key);
    
    if (!result.allowed && result.retryAfter) {
      console.log(`⏳ Rate limit hit, waiting ${result.retryAfter}ms...`);
      await new Promise(resolve => setTimeout(resolve, result.retryAfter));
      return this.waitForRateLimit(key); // 再帰的にチェック
    }
  }

  getStats(key: string): { requestCount: number; windowStart: number } {
    const now = Date.now();
    const windowStart = now - this.config.windowMs;
    const userRequests = this.requests.get(key) || [];
    const validRequests = userRequests.filter(req => req.timestamp > windowStart);
    const requestCount = validRequests.reduce((sum, req) => sum + req.count, 0);
    
    return { requestCount, windowStart };
  }

  reset(key?: string): void {
    if (key) {
      this.requests.delete(key);
      this.lastRequestTime.delete(key);
    } else {
      this.requests.clear();
      this.lastRequestTime.clear();
    }
  }
}

// Gmail API専用のレート制限設定
const gmailRateLimiter = new RateLimiter({
  maxRequests: 100, // 1分間に100リクエスト
  windowMs: 60 * 1000, // 1分間
  minInterval: 100, // 最小100ms間隔
});

// Gmail APIクォータ管理クラス
export class GmailQuotaManager {
  private static instance: GmailQuotaManager;
  private rateLimiter: RateLimiter;
  private quotaUsage: Map<string, { used: number; limit: number; resetTime: number }> = new Map();

  private constructor() {
    this.rateLimiter = gmailRateLimiter;
  }

  static getInstance(): GmailQuotaManager {
    if (!GmailQuotaManager.instance) {
      GmailQuotaManager.instance = new GmailQuotaManager();
    }
    return GmailQuotaManager.instance;
  }

  async checkQuota(userId: string, operation: string): Promise<{ allowed: boolean; retryAfter?: number }> {
    const key = `${userId}:${operation}`;
    return this.rateLimiter.checkRateLimit(key);
  }

  async waitForQuota(userId: string, operation: string): Promise<void> {
    const key = `${userId}:${operation}`;
    await this.rateLimiter.waitForRateLimit(key);
  }

  updateQuotaUsage(userId: string, operation: string, cost: number): void {
    const key = `${userId}:${operation}`;
    const now = Date.now();
    const current = this.quotaUsage.get(key) || { used: 0, limit: 1000, resetTime: now + 24 * 60 * 60 * 1000 };
    
    // 日次リセットチェック
    if (now > current.resetTime) {
      current.used = 0;
      current.resetTime = now + 24 * 60 * 60 * 1000;
    }
    
    current.used += cost;
    this.quotaUsage.set(key, current);
    
    console.log(`📊 Quota usage for ${operation}: ${current.used}/${current.limit}`);
  }

  getQuotaStatus(userId: string, operation: string): { used: number; limit: number; remaining: number } {
    const key = `${userId}:${operation}`;
    const quota = this.quotaUsage.get(key) || { used: 0, limit: 1000, resetTime: 0 };
    
    return {
      used: quota.used,
      limit: quota.limit,
      remaining: quota.limit - quota.used
    };
  }

  getRateLimitStats(userId: string, operation: string): { requestCount: number; windowStart: number } {
    const key = `${userId}:${operation}`;
    return this.rateLimiter.getStats(key);
  }
}

// Gmail API操作のコスト定義
export const GMAIL_API_COSTS = {
  'threads.list': 1,
  'threads.get': 1,
  'messages.list': 1,
  'messages.get': 1,
  'messages.send': 1,
  'attachments.get': 1,
  'labels.list': 1,
  'profile.get': 1,
} as const;

export type GmailOperation = keyof typeof GMAIL_API_COSTS;