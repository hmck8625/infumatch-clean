import { google } from 'googleapis';
import { OAuth2Client } from 'google-auth-library';
import { GmailQuotaManager, GMAIL_API_COSTS, type GmailOperation } from './rate-limiter';

export interface EmailThread {
  id: string;
  snippet: string;
  historyId: string;
  messages: GmailMessage[];
  labels?: string[];
  lastMessageDate?: Date;
  unread?: boolean;
  important?: boolean;
}

export interface SearchFilters {
  query?: string;
  from?: string;
  to?: string;
  subject?: string;
  hasAttachment?: boolean;
  isUnread?: boolean;
  isImportant?: boolean;
  dateAfter?: Date;
  dateBefore?: Date;
  labels?: string[];
  maxResults?: number;
}

export interface SearchOptions {
  pageToken?: string;
  includeSpamTrash?: boolean;
  labelIds?: string[];
}

export interface Attachment {
  attachmentId: string;
  size: number;
  filename: string;
  mimeType: string;
  data?: string; // Base64エンコードされたデータ
}

export interface GmailMessage {
  id: string;
  threadId: string;
  labelIds: string[];
  snippet: string;
  payload: {
    headers: Array<{ name: string; value: string }>;
    body?: {
      data?: string;
      attachmentId?: string;
      size?: number;
    };
    parts?: Array<{
      mimeType: string;
      filename?: string;
      body?: {
        data?: string;
        attachmentId?: string;
        size?: number;
      };
      parts?: Array<{
        mimeType: string;
        filename?: string;
        body?: {
          data?: string;
          attachmentId?: string;
          size?: number;
        };
      }>;
    }>;
  };
  internalDate: string;
  attachments?: Attachment[];
}

export class GmailService {
  private gmail;
  private auth: OAuth2Client;
  private quotaManager: GmailQuotaManager;
  private userId: string;

  constructor(accessToken: string, userId: string = 'default') {
    this.auth = new google.auth.OAuth2();
    this.auth.setCredentials({ access_token: accessToken });
    this.userId = userId;
    this.quotaManager = GmailQuotaManager.getInstance();
    
    this.gmail = google.gmail({ 
      version: 'v1', 
      auth: this.auth 
    });
  }

  // Gmail API呼び出し前のレート制限チェック
  private async checkRateLimit(operation: GmailOperation): Promise<void> {
    const quota = await this.quotaManager.checkQuota(this.userId, operation);
    
    if (!quota.allowed) {
      console.log(`⏳ Rate limit for ${operation}, waiting ${quota.retryAfter}ms`);
      await this.quotaManager.waitForQuota(this.userId, operation);
    }
    
    // クォータ使用量を記録
    const cost = GMAIL_API_COSTS[operation];
    this.quotaManager.updateQuotaUsage(this.userId, operation, cost);
  }

  // トークンエラーをチェックして適切なエラーを投げる
  private checkTokenError(error: any): never {
    if (error?.response?.status === 401 || 
        error?.message?.includes('invalid_grant') ||
        error?.message?.includes('Token has been expired or revoked')) {
      throw new Error('TOKEN_EXPIRED');
    }
    throw error;
  }

  // 高度な検索機能付きメールスレッド取得
  async searchThreads(filters: SearchFilters = {}, options: SearchOptions = {}): Promise<{ threads: EmailThread[]; nextPageToken?: string }> {
    try {
      console.log('🔍 Starting advanced Gmail search');
      console.log('Search filters:', filters);
      
      // レート制限チェック
      await this.checkRateLimit('threads.list');
      
      // Gmail検索クエリを構築
      const query = this.buildSearchQuery(filters);
      console.log('Gmail search query:', query);

      const response = await this.gmail.users.threads.list({
        userId: 'me',
        q: query,
        maxResults: filters.maxResults || 20,
        pageToken: options.pageToken,
        includeSpamTrash: options.includeSpamTrash || false,
        labelIds: options.labelIds,
      });
      
      console.log('Gmail API response status:', response.status);
      console.log('Threads found:', response.data.threads?.length || 0);

      const threads = response.data.threads || [];
      
      if (threads.length === 0) {
        console.log('No threads found, returning empty array');
        return { threads: [], nextPageToken: response.data.nextPageToken };
      }
      
      console.log('Fetching detailed thread information...');
      const detailedThreads = await Promise.all(
        threads.map(async (thread, index) => {
          try {
            console.log(`Fetching thread ${index + 1}/${threads.length}: ${thread.id}`);
            await this.checkRateLimit('threads.get');
            
            const threadDetail = await this.gmail.users.threads.get({
              userId: 'me',
              id: thread.id!,
              format: 'full',
            });

            const messages = threadDetail.data.messages?.map(msg => this.formatMessage(msg)) || [];
            const lastMessage = messages[messages.length - 1];
            
            return {
              id: thread.id!,
              snippet: threadDetail.data.snippet || '',
              historyId: threadDetail.data.historyId || '',
              messages,
              labels: this.extractLabels(threadDetail.data),
              lastMessageDate: lastMessage ? new Date(parseInt(lastMessage.internalDate)) : undefined,
              unread: this.checkUnreadStatus(threadDetail.data),
              important: this.checkImportantStatus(threadDetail.data),
            };
          } catch (threadError) {
            console.error(`Error fetching thread ${thread.id}:`, threadError);
            return null;
          }
        })
      );
      
      const validThreads = detailedThreads.filter(thread => thread !== null) as EmailThread[];
      console.log(`Successfully fetched ${validThreads.length} threads`);
      
      return { 
        threads: validThreads, 
        nextPageToken: response.data.nextPageToken 
      };
    } catch (error: any) {
      console.error('❌ Gmail search error:', {
        message: error?.message,
        stack: error?.stack,
        response: error?.response?.data,
        status: error?.response?.status,
        code: error?.code
      });
      this.checkTokenError(error);
    }
  }

  // インフルエンサーとのメールスレッドを取得（後方互換性のため保持）
  async getInfluencerThreads(influencerEmail?: string): Promise<EmailThread[]> {
    const filters: SearchFilters = {
      maxResults: 20
    };
    
    if (influencerEmail) {
      filters.from = influencerEmail;
    } else {
      filters.query = 'in:sent OR in:inbox';
    }
    
    const result = await this.searchThreads(filters);
    return result?.threads || [];
  }

  // 検索クエリを構築
  private buildSearchQuery(filters: SearchFilters): string {
    const queryParts: string[] = [];
    
    if (filters.query) {
      queryParts.push(filters.query);
    }
    
    if (filters.from) {
      queryParts.push(`from:${filters.from}`);
    }
    
    if (filters.to) {
      queryParts.push(`to:${filters.to}`);
    }
    
    if (filters.subject) {
      queryParts.push(`subject:"${filters.subject}"`);
    }
    
    if (filters.hasAttachment) {
      queryParts.push('has:attachment');
    }
    
    if (filters.isUnread) {
      queryParts.push('is:unread');
    }
    
    if (filters.isImportant) {
      queryParts.push('is:important');
    }
    
    if (filters.dateAfter) {
      const dateStr = filters.dateAfter.toISOString().split('T')[0];
      queryParts.push(`after:${dateStr}`);
    }
    
    if (filters.dateBefore) {
      const dateStr = filters.dateBefore.toISOString().split('T')[0];
      queryParts.push(`before:${dateStr}`);
    }
    
    if (filters.labels && filters.labels.length > 0) {
      filters.labels.forEach(label => {
        queryParts.push(`label:${label}`);
      });
    }
    
    return queryParts.length > 0 ? queryParts.join(' ') : 'in:inbox';
  }

  // ラベル情報を抽出
  private extractLabels(threadData: any): string[] {
    const labels: string[] = [];
    
    if (threadData.messages) {
      threadData.messages.forEach((message: any) => {
        if (message.labelIds) {
          labels.push(...message.labelIds);
        }
      });
    }
    
    return Array.from(new Set(labels));
  }

  // 未読状態をチェック
  private checkUnreadStatus(threadData: any): boolean {
    if (threadData.messages) {
      return threadData.messages.some((message: any) => 
        message.labelIds && message.labelIds.includes('UNREAD')
      );
    }
    return false;
  }

  // 重要状態をチェック
  private checkImportantStatus(threadData: any): boolean {
    if (threadData.messages) {
      return threadData.messages.some((message: any) => 
        message.labelIds && message.labelIds.includes('IMPORTANT')
      );
    }
    return false;
  }

  // メールラベル一覧を取得
  async getLabels(): Promise<any[]> {
    try {
      await this.checkRateLimit('labels.list');
      
      const response = await this.gmail.users.labels.list({
        userId: 'me',
      });
      
      return response.data.labels || [];
    } catch (error) {
      console.error('Gmail labels取得エラー:', error);
      this.checkTokenError(error);
      return [];
    }
  }

  // メールを即座検索（単純なキーワード検索）
  async quickSearch(keyword: string, maxResults: number = 10): Promise<EmailThread[]> {
    const result = await this.searchThreads({
      query: keyword,
      maxResults
    });
    return result?.threads || [];
  }

  // 高度なフィルタリング
  async getFilteredThreads(
    influencerEmail?: string,
    hasAttachment?: boolean,
    isUnread?: boolean,
    dateAfter?: Date,
    maxResults: number = 20
  ): Promise<EmailThread[]> {
    const filters: SearchFilters = {
      maxResults
    };
    
    if (influencerEmail) {
      filters.from = influencerEmail;
    }
    
    if (hasAttachment !== undefined) {
      filters.hasAttachment = hasAttachment;
    }
    
    if (isUnread !== undefined) {
      filters.isUnread = isUnread;
    }
    
    if (dateAfter) {
      filters.dateAfter = dateAfter;
    }
    
    const result = await this.searchThreads(filters);
    return result?.threads || [];
  }

  // 特定のスレッドの詳細を取得
  async getThread(threadId: string): Promise<EmailThread> {
    try {
      // レート制限チェック
      await this.checkRateLimit('threads.get');
      
      const response = await this.gmail.users.threads.get({
        userId: 'me',
        id: threadId,
        format: 'full',
      });

      return {
        id: threadId,
        snippet: response.data.snippet || '',
        historyId: response.data.historyId || '',
        messages: response.data.messages?.map(this.formatMessage) || [],
      };
    } catch (error) {
      console.error('Gmail thread詳細取得エラー:', error);
      this.checkTokenError(error);
    }
  }

  // メールを送信（正しいスレッド返信）
  async sendReply(threadId: string, to: string, subject: string, body: string, replyToMessageId?: string): Promise<void> {
    try {
      // レート制限チェック
      await this.checkRateLimit('messages.send');
      
      let raw: string;
      
      if (replyToMessageId) {
        // 正しい返信ヘッダーを取得して使用
        const replyHeaders = await this.getReplyHeaders(replyToMessageId);
        raw = this.createRawReplyMessage(to, replyHeaders.subject, body, replyHeaders);
      } else {
        // フォールバック: 従来の方法
        raw = this.createRawMessage(to, subject, body, threadId);
      }
      
      await this.gmail.users.messages.send({
        userId: 'me',
        requestBody: {
          raw: raw,
          threadId: threadId,
        },
      });
    } catch (error) {
      console.error('Gmail送信エラー:', error);
      this.checkTokenError(error);
    }
  }

  // 新しいメールを送信
  async sendNewMessage(to: string, subject: string, body: string): Promise<void> {
    try {
      // レート制限チェック
      await this.checkRateLimit('messages.send');
      
      const raw = this.createRawMessage(to, subject, body);
      
      await this.gmail.users.messages.send({
        userId: 'me',
        requestBody: {
          raw: raw,
        },
      });
    } catch (error) {
      console.error('Gmail新規送信エラー:', error);
      this.checkTokenError(error);
    }
  }

  // ユーザープロフィールを取得
  async getProfile() {
    try {
      // レート制限チェック
      await this.checkRateLimit('profile.get');
      
      const response = await this.gmail.users.getProfile({
        userId: 'me',
      });
      return response.data;
    } catch (error) {
      console.error('Gmail profile取得エラー:', error);
      this.checkTokenError(error);
    }
  }

  // 添付ファイルを取得
  async getAttachment(messageId: string, attachmentId: string): Promise<string | null> {
    try {
      // レート制限チェック
      await this.checkRateLimit('attachments.get');
      
      const response = await this.gmail.users.messages.attachments.get({
        userId: 'me',
        messageId: messageId,
        id: attachmentId,
      });
      
      return response.data.data || null;
    } catch (error) {
      console.error('添付ファイル取得エラー:', error);
      this.checkTokenError(error);
    }
  }

  // 添付ファイル付きメールを送信
  async sendWithAttachments(
    to: string, 
    subject: string, 
    body: string, 
    attachments: File[] = [],
    threadId?: string,
    replyToMessageId?: string
  ): Promise<void> {
    try {
      // レート制限チェック
      await this.checkRateLimit('messages.send');
      
      let replyHeaders;
      if (replyToMessageId) {
        replyHeaders = await this.getReplyHeaders(replyToMessageId);
      }
      
      const raw = await this.createMultipartMessage(to, subject, body, attachments, threadId, replyHeaders);
      
      await this.gmail.users.messages.send({
        userId: 'me',
        requestBody: {
          raw: raw,
          threadId: threadId,
        },
      });
    } catch (error) {
      console.error('添付ファイル付きメール送信エラー:', error);
      this.checkTokenError(error);
    }
  }

  // メッセージのフォーマット
  private formatMessage(message: any): GmailMessage {
    const attachments = this.extractAttachments(message.payload);
    
    return {
      id: message.id,
      threadId: message.threadId,
      labelIds: message.labelIds || [],
      snippet: message.snippet || '',
      payload: message.payload,
      internalDate: message.internalDate,
      attachments: attachments.length > 0 ? attachments : undefined,
    };
  }

  // 添付ファイル情報を抽出
  private extractAttachments(payload: any): Attachment[] {
    const attachments: Attachment[] = [];
    
    const extractFromPart = (part: any) => {
      // 添付ファイルの条件：filename が存在し、attachmentId がある
      if (part.filename && part.body?.attachmentId && part.body?.size > 0) {
        attachments.push({
          attachmentId: part.body.attachmentId,
          size: part.body.size,
          filename: part.filename,
          mimeType: part.mimeType || 'application/octet-stream',
        });
      }
      
      // 再帰的にpartsを処理
      if (part.parts) {
        part.parts.forEach(extractFromPart);
      }
    };
    
    if (payload.parts) {
      payload.parts.forEach(extractFromPart);
    }
    
    return attachments;
  }

  // RAWメッセージを作成
  private createRawMessage(to: string, subject: string, body: string, threadId?: string): string {
    const messageParts = [
      `To: ${to}`,
      `Subject: ${subject}`,
      'Content-Type: text/html; charset=utf-8',
      'MIME-Version: 1.0',
      '',
      body,
    ];

    if (threadId) {
      messageParts.splice(2, 0, `In-Reply-To: ${threadId}`);
      messageParts.splice(3, 0, `References: ${threadId}`);
    }

    const message = messageParts.join('\r\n');
    return Buffer.from(message).toString('base64').replace(/\+/g, '-').replace(/\//g, '_');
  }

  // 正しい返信用RAWメッセージを作成（RFC 2822準拠）
  private createRawReplyMessage(to: string, subject: string, body: string, replyHeaders: {
    messageId: string;
    references: string;
    subject: string;
    inReplyTo: string;
  }): string {
    const messageParts = [
      `To: ${to}`,
      `Subject: ${replyHeaders.subject}`,
      `In-Reply-To: ${replyHeaders.inReplyTo}`,
      `References: ${replyHeaders.references}`,
      'Content-Type: text/html; charset=utf-8',
      'MIME-Version: 1.0',
      '',
      body,
    ];

    const message = messageParts.join('\r\n');
    return Buffer.from(message).toString('base64').replace(/\+/g, '-').replace(/\//g, '_');
  }

  // マルチパート（添付ファイル付き）メッセージを作成
  private async createMultipartMessage(
    to: string, 
    subject: string, 
    body: string, 
    attachments: File[] = [],
    threadId?: string,
    replyHeaders?: {
      messageId: string;
      references: string;
      subject: string;
      inReplyTo: string;
    }
  ): Promise<string> {
    const boundary = `boundary_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    const messageParts = [
      `To: ${to}`,
      `Subject: ${replyHeaders?.subject || subject}`,
      'MIME-Version: 1.0',
      `Content-Type: multipart/mixed; boundary="${boundary}"`,
    ];

    if (replyHeaders) {
      // RFC 2822準拠の正しい返信ヘッダーを使用
      messageParts.push(`In-Reply-To: ${replyHeaders.inReplyTo}`);
      messageParts.push(`References: ${replyHeaders.references}`);
    } else if (threadId) {
      // フォールバック: 従来の方法
      messageParts.push(`In-Reply-To: ${threadId}`);
      messageParts.push(`References: ${threadId}`);
    }

    messageParts.push(''); // 空行

    // メール本文
    messageParts.push(`--${boundary}`);
    messageParts.push('Content-Type: text/html; charset=utf-8');
    messageParts.push('Content-Transfer-Encoding: 8bit');
    messageParts.push('');
    messageParts.push(body);
    messageParts.push('');

    // 添付ファイル
    for (const file of attachments) {
      const fileData = await this.fileToBase64(file);
      
      messageParts.push(`--${boundary}`);
      messageParts.push(`Content-Type: ${file.type || 'application/octet-stream'}`);
      messageParts.push('Content-Transfer-Encoding: base64');
      messageParts.push(`Content-Disposition: attachment; filename="${file.name}"`);
      messageParts.push('');
      messageParts.push(fileData);
      messageParts.push('');
    }

    messageParts.push(`--${boundary}--`);

    const message = messageParts.join('\r\n');
    return Buffer.from(message).toString('base64').replace(/\+/g, '-').replace(/\//g, '_');
  }

  // ファイルをBase64に変換
  private fileToBase64(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        const base64 = (reader.result as string).split(',')[1];
        resolve(base64);
      };
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  }

  // Base64デコード
  static decodeBase64(data: string): string {
    try {
      return Buffer.from(data, 'base64').toString('utf-8');
    } catch (error) {
      return '';
    }
  }

  // メール本文を取得（添付ファイルを除外）
  static getEmailBody(message: GmailMessage): string {
    const { payload } = message;
    
    // シンプルなテキスト/HTMLメッセージ
    if (payload.body?.data && !payload.body?.attachmentId) {
      return this.decodeBase64(payload.body.data);
    }

    // マルチパートメッセージ
    if (payload.parts) {
      for (const part of payload.parts) {
        // 添付ファイルではないテキスト/HTMLパートを探す
        if ((part.mimeType === 'text/html' || part.mimeType === 'text/plain') && 
            !part.filename && part.body?.data && !part.body?.attachmentId) {
          return this.decodeBase64(part.body.data);
        }
        
        // ネストしたパーツも確認
        if (part.parts) {
          for (const nestedPart of part.parts) {
            if ((nestedPart.mimeType === 'text/html' || nestedPart.mimeType === 'text/plain') && 
                !nestedPart.filename && nestedPart.body?.data && !nestedPart.body?.attachmentId) {
              return this.decodeBase64(nestedPart.body.data);
            }
          }
        }
      }
    }

    return message.snippet;
  }

  // 添付ファイルのダウンロードURL生成
  static createDownloadUrl(attachment: Attachment): string {
    if (attachment.data) {
      const blob = new Blob([this.base64ToArrayBuffer(attachment.data)], { 
        type: attachment.mimeType 
      });
      return URL.createObjectURL(blob);
    }
    return '';
  }

  // Base64をArrayBufferに変換
  static base64ToArrayBuffer(base64: string): ArrayBuffer {
    const binaryString = atob(base64.replace(/-/g, '+').replace(/_/g, '/'));
    const bytes = new Uint8Array(binaryString.length);
    for (let i = 0; i < binaryString.length; i++) {
      bytes[i] = binaryString.charCodeAt(i);
    }
    return bytes.buffer;
  }

  // ファイルサイズを人間が読める形式に変換
  static formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  // ヘッダーから特定の値を取得
  static getHeader(message: GmailMessage, headerName: string): string {
    const header = message.payload.headers.find(
      h => h.name.toLowerCase() === headerName.toLowerCase()
    );
    return header?.value || '';
  }

  // 返信用のヘッダー情報を取得
  async getReplyHeaders(messageId: string): Promise<{
    messageId: string;
    references: string;
    subject: string;
    inReplyTo: string;
  }> {
    try {
      // レート制限チェック
      await this.checkRateLimit('messages.get');
      
      const response = await this.gmail.users.messages.get({
        userId: 'me',
        id: messageId,
        format: 'metadata',
        metadataHeaders: ['Message-ID', 'References', 'Subject', 'In-Reply-To']
      });

      const headers = response.data.payload?.headers || [];
      let originalMessageId = '';
      let originalReferences = '';
      let originalSubject = '';
      let originalInReplyTo = '';

      headers.forEach((header: any) => {
        const name = header.name.toLowerCase();
        if (name === 'message-id') {
          originalMessageId = header.value;
        } else if (name === 'references') {
          originalReferences = header.value;
        } else if (name === 'subject') {
          originalSubject = header.value;
        } else if (name === 'in-reply-to') {
          originalInReplyTo = header.value;
        }
      });

      // 返信用の件名を作成（Re:を付加、既にある場合は追加しない）
      const replySubject = originalSubject.toLowerCase().startsWith('re:') 
        ? originalSubject 
        : `Re: ${originalSubject}`;

      // References ヘッダーを構築（RFC 2822準拠）
      // 既存のReferenceesに元メッセージのMessage-IDを追加
      const updatedReferences = originalReferences 
        ? `${originalReferences} ${originalMessageId}`.trim()
        : originalMessageId;

      return {
        messageId: originalMessageId,
        references: updatedReferences,
        subject: replySubject,
        inReplyTo: originalMessageId
      };
    } catch (error) {
      console.error('返信ヘッダー取得エラー:', error);
      this.checkTokenError(error);
      
      // フォールバック: 基本的な返信ヘッダーを返す
      return {
        messageId: `<${messageId}@gmail.googlemail.com>`,
        references: `<${messageId}@gmail.googlemail.com>`,
        subject: 'Re: (Subject unavailable)',
        inReplyTo: `<${messageId}@gmail.googlemail.com>`
      };
    }
  }

  // 添付ファイルの種類を判定
  static getAttachmentIcon(mimeType: string): string {
    if (mimeType.startsWith('image/')) return '🖼️';
    if (mimeType.includes('pdf')) return '📄';
    if (mimeType.includes('word') || mimeType.includes('document')) return '📝';
    if (mimeType.includes('excel') || mimeType.includes('spreadsheet')) return '📊';
    if (mimeType.includes('powerpoint') || mimeType.includes('presentation')) return '📋';
    if (mimeType.includes('zip') || mimeType.includes('rar') || mimeType.includes('archive')) return '🗜️';
    if (mimeType.startsWith('audio/')) return '🎵';
    if (mimeType.startsWith('video/')) return '🎬';
    return '📎';
  }
}