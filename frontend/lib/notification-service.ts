interface NotificationData {
  title: string;
  body: string;
  icon?: string;
  tag?: string;
  data?: any;
}

interface GmailNotification {
  type: 'new_email' | 'email_reply' | 'important_email';
  threadId: string;
  messageId: string;
  from: string;
  subject: string;
  snippet: string;
  timestamp: number;
}

class NotificationService {
  private static instance: NotificationService;
  private permission: NotificationPermission = 'default';
  private listeners: Map<string, Function[]> = new Map();

  private constructor() {
    this.checkPermission();
  }

  static getInstance(): NotificationService {
    if (!NotificationService.instance) {
      NotificationService.instance = new NotificationService();
    }
    return NotificationService.instance;
  }

  private checkPermission(): void {
    if ('Notification' in window) {
      this.permission = Notification.permission;
    }
  }

  async requestPermission(): Promise<boolean> {
    if (!('Notification' in window)) {
      console.warn('このブラウザは通知をサポートしていません');
      return false;
    }

    if (this.permission === 'granted') {
      return true;
    }

    const permission = await Notification.requestPermission();
    this.permission = permission;
    
    if (permission === 'granted') {
      console.log('✅ 通知許可が取得されました');
      return true;
    } else {
      console.log('❌ 通知許可が拒否されました');
      return false;
    }
  }

  showNotification(data: NotificationData): Notification | null {
    if (this.permission !== 'granted') {
      console.warn('通知許可がありません');
      return null;
    }

    const notification = new Notification(data.title, {
      body: data.body,
      icon: data.icon || '/favicon.ico',
      tag: data.tag,
      data: data.data,
      requireInteraction: true,
      silent: false,
    });

    // クリックイベントを設定
    notification.onclick = (event) => {
      event.preventDefault();
      
      // InfuMatchのタブにフォーカス、なければ新しいタブで開く
      if (window.parent) {
        window.parent.focus();
      } else {
        window.focus();
      }
      
      // 通知データに基づいてページ遷移
      if (data.data?.threadId) {
        const url = `/messages?thread=${data.data.threadId}`;
        if (window.location.pathname !== '/messages') {
          window.location.href = url;
        }
      }
      
      notification.close();
    };

    // 自動で閉じる（10秒後）
    setTimeout(() => {
      notification.close();
    }, 10000);

    return notification;
  }

  showGmailNotification(notification: GmailNotification): Notification | null {
    let title = '';
    let icon = '';
    
    switch (notification.type) {
      case 'new_email':
        title = '📧 新しいメール';
        icon = '📧';
        break;
      case 'email_reply':
        title = '↩️ 返信メール';
        icon = '↩️';
        break;
      case 'important_email':
        title = '⭐ 重要なメール';
        icon = '⭐';
        break;
    }

    return this.showNotification({
      title: `${title} - ${notification.from}`,
      body: `件名: ${notification.subject}\n${notification.snippet}`,
      icon: `/icons/${notification.type}.png`,
      tag: `gmail-${notification.threadId}`,
      data: {
        type: notification.type,
        threadId: notification.threadId,
        messageId: notification.messageId,
        timestamp: notification.timestamp,
      },
    });
  }

  // イベントリスナー管理
  addEventListener(event: string, callback: Function): void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event)!.push(callback);
  }

  removeEventListener(event: string, callback: Function): void {
    if (this.listeners.has(event)) {
      const callbacks = this.listeners.get(event)!;
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    }
  }

  private emit(event: string, data: any): void {
    if (this.listeners.has(event)) {
      this.listeners.get(event)!.forEach(callback => callback(data));
    }
  }

  // バックグラウンド通知チェック
  startBackgroundCheck(intervalMs: number = 60000): void {
    if (!('Notification' in window) || this.permission !== 'granted') {
      console.warn('通知が利用できないため、バックグラウンドチェックを開始できません');
      return;
    }

    console.log(`🔔 バックグラウンド通知チェック開始 (${intervalMs}ms間隔)`);
    
    setInterval(async () => {
      try {
        await this.checkForNewEmails();
      } catch (error) {
        console.error('バックグラウンド通知チェックエラー:', error);
      }
    }, intervalMs);
  }

  private async checkForNewEmails(): Promise<void> {
    try {
      // 最新のメールをチェック
      const response = await fetch('/api/gmail/threads?maxResults=5&unread=true');
      
      if (!response.ok) {
        return;
      }

      const data = await response.json();
      const threads = data.threads || [];
      
      // 新しい未読メールがあるかチェック
      const lastCheckTime = this.getLastCheckTime();
      const newThreads = threads.filter((thread: any) => {
        const lastMessage = thread.messages[thread.messages.length - 1];
        const messageTime = parseInt(lastMessage.internalDate);
        return messageTime > lastCheckTime;
      });

      // 新しいメールの通知を表示
      newThreads.forEach((thread: any) => {
        const lastMessage = thread.messages[thread.messages.length - 1];
        const from = this.getEmailFromHeader(lastMessage);
        const subject = this.getSubjectFromHeader(lastMessage);
        
        this.showGmailNotification({
          type: 'new_email',
          threadId: thread.id,
          messageId: lastMessage.id,
          from,
          subject,
          snippet: thread.snippet,
          timestamp: parseInt(lastMessage.internalDate),
        });
      });

      // 最後のチェック時間を更新
      this.updateLastCheckTime();
      
    } catch (error) {
      console.error('新着メールチェックエラー:', error);
    }
  }

  private getLastCheckTime(): number {
    const stored = localStorage.getItem('gmail-last-check');
    return stored ? parseInt(stored) : Date.now() - 3600000; // 1時間前をデフォルト
  }

  private updateLastCheckTime(): void {
    localStorage.setItem('gmail-last-check', Date.now().toString());
  }

  private getEmailFromHeader(message: any): string {
    const fromHeader = message.payload.headers.find((h: any) => h.name.toLowerCase() === 'from');
    return fromHeader?.value || 'Unknown';
  }

  private getSubjectFromHeader(message: any): string {
    const subjectHeader = message.payload.headers.find((h: any) => h.name.toLowerCase() === 'subject');
    return subjectHeader?.value || '(件名なし)';
  }

  // 通知音を再生
  playNotificationSound(): void {
    try {
      const audio = new Audio('/sounds/notification.mp3');
      audio.volume = 0.5;
      audio.play().catch(e => console.log('通知音の再生に失敗:', e));
    } catch (error) {
      console.log('通知音の再生に失敗:', error);
    }
  }

  // 通知の有効/無効を切り替え
  async toggleNotifications(): Promise<boolean> {
    if (this.permission === 'granted') {
      // 通知を無効にする（実際はブラウザ設定で制御）
      return false;
    } else {
      return await this.requestPermission();
    }
  }

  // 現在の通知設定状態を取得
  getNotificationStatus(): {
    supported: boolean;
    permission: NotificationPermission;
    enabled: boolean;
  } {
    return {
      supported: 'Notification' in window,
      permission: this.permission,
      enabled: this.permission === 'granted',
    };
  }
}

// プッシュ通知管理
export class PushNotificationManager {
  private static instance: PushNotificationManager;
  private registration: ServiceWorkerRegistration | null = null;

  private constructor() {}

  static getInstance(): PushNotificationManager {
    if (!PushNotificationManager.instance) {
      PushNotificationManager.instance = new PushNotificationManager();
    }
    return PushNotificationManager.instance;
  }

  async initialize(): Promise<boolean> {
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
      console.warn('プッシュ通知がサポートされていません');
      return false;
    }

    try {
      // Service Workerを登録
      this.registration = await navigator.serviceWorker.register('/sw.js');
      console.log('✅ Service Worker registered');
      return true;
    } catch (error) {
      console.error('❌ Service Worker registration failed:', error);
      return false;
    }
  }

  async subscribeToPush(): Promise<PushSubscription | null> {
    if (!this.registration) {
      console.error('Service Workerが登録されていません');
      return null;
    }

    try {
      const subscription = await this.registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: this.urlBase64ToUint8Array(process.env.NEXT_PUBLIC_VAPID_PUBLIC_KEY || ''),
      });

      console.log('✅ Push subscription created');
      return subscription;
    } catch (error) {
      console.error('❌ Push subscription failed:', error);
      return null;
    }
  }

  private urlBase64ToUint8Array(base64String: string): Uint8Array {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);
    for (let i = 0; i < rawData.length; ++i) {
      outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
  }
}

export const notificationService = NotificationService.getInstance();
export const pushNotificationManager = PushNotificationManager.getInstance();