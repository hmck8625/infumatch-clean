/**
 * Firestore Admin SDK for Server-side Operations
 * 
 * @description サーバーサイドでのFirestore操作（Admin SDK使用）
 */

import { initializeApp, getApps, cert } from 'firebase-admin/app';
import { getFirestore } from 'firebase-admin/firestore';

// Firebase Admin SDKの初期化
let adminApp: any;
let adminDb: any;

try {
  if (getApps().length === 0) {
    // Google Cloud環境では自動認証を使用
    adminApp = initializeApp({
      projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID || 'hackathon-462905'
    });
  } else {
    adminApp = getApps()[0];
  }
  
  adminDb = getFirestore(adminApp);
  console.log('✅ Firebase Admin SDK initialized successfully');
} catch (error) {
  console.error('❌ Firebase Admin SDK initialization failed:', error);
}

export { adminDb };

// 設定データの型定義（クライアント側と同一）
export interface UserSettings {
  id?: string;
  userId: string;
  companyInfo: {
    companyName: string;
    industry: string;
    employeeCount: string;
    website: string;
    description: string;
    contactPerson?: string;
    contactEmail?: string;
  };
  products: Array<{
    id: string;
    name: string;
    category: string;
    targetAudience: string;
    priceRange: string;
    description: string;
  }>;
  negotiationSettings: {
    preferredTone: string;
    responseTimeExpectation: string;
    budgetFlexibility: string;
    decisionMakers: string[];
    communicationPreferences: string[];
    specialInstructions?: string;
    keyPriorities?: string[];
    avoidTopics?: string[];
  };
  matchingSettings: {
    priorityCategories: string[];
    minSubscribers: number;
    maxSubscribers: number;
    minEngagementRate: number;
    excludeCategories: string[];
    geographicFocus: string[];
    priorityKeywords?: string[];
    excludeKeywords?: string[];
  };
  createdAt: string;
  updatedAt: string;
}

export interface FirestoreResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}

/**
 * Firestore Admin CRUD操作クラス
 */
export class FirestoreAdminService {
  private readonly COLLECTION_NAME = 'user_settings';

  /**
   * ユーザー設定を取得（Admin SDK）
   */
  async getUserSettings(userId: string): Promise<FirestoreResponse<UserSettings>> {
    try {
      console.log(`📖 [Admin] Fetching settings for user: ${userId}`);
      
      if (!adminDb) {
        console.error('❌ Admin Firestore not initialized');
        return { 
          success: false, 
          error: 'Firestore Admin not available' 
        };
      }
      
      const docRef = adminDb.collection(this.COLLECTION_NAME).doc(userId);
      const docSnap = await docRef.get();

      if (docSnap.exists) {
        const data = docSnap.data() as UserSettings;
        console.log('✅ [Admin] Settings found in Firestore');
        return { success: true, data };
      } else {
        console.log('📄 [Admin] No settings found, returning default settings');
        const defaultSettings = this.getDefaultSettings(userId);
        return { success: true, data: defaultSettings };
      }
    } catch (error) {
      console.error('❌ [Admin] Error fetching settings:', error);
      return { 
        success: false, 
        error: `設定の取得に失敗しました: ${(error as Error).message}` 
      };
    }
  }

  /**
   * ユーザー設定を保存（Admin SDK）
   */
  async saveUserSettings(userId: string, settings: Partial<UserSettings>): Promise<FirestoreResponse<UserSettings>> {
    try {
      console.log(`💾 [Admin] Saving settings for user: ${userId}`);
      
      if (!adminDb) {
        console.error('❌ Admin Firestore not initialized');
        return { 
          success: false, 
          error: 'Firestore Admin not available' 
        };
      }
      
      const docRef = adminDb.collection(this.COLLECTION_NAME).doc(userId);
      const now = new Date().toISOString();
      
      // 既存設定を取得
      const existing = await this.getUserSettings(userId);
      const baseSettings = existing.data || this.getDefaultSettings(userId);
      
      // 更新データをマージ
      const updatedSettings: UserSettings = {
        ...baseSettings,
        ...settings,
        userId,
        updatedAt: now,
        createdAt: baseSettings.createdAt || now
      };

      await docRef.set(updatedSettings, { merge: true });
      
      console.log('✅ [Admin] Settings saved successfully');
      return { success: true, data: updatedSettings };
    } catch (error) {
      console.error('❌ [Admin] Error saving settings:', error);
      return { 
        success: false, 
        error: `設定の保存に失敗しました: ${(error as Error).message}` 
      };
    }
  }

  /**
   * デフォルト設定を生成
   */
  private getDefaultSettings(userId: string): UserSettings {
    const now = new Date().toISOString();
    
    return {
      userId,
      companyInfo: {
        companyName: '',
        industry: '',
        employeeCount: '',
        website: '',
        description: '',
        contactPerson: '',
        contactEmail: ''
      },
      products: [],
      negotiationSettings: {
        preferredTone: 'professional',
        responseTimeExpectation: '24時間以内',
        budgetFlexibility: 'medium',
        decisionMakers: [],
        communicationPreferences: ['email'],
        specialInstructions: '',
        keyPriorities: [],
        avoidTopics: []
      },
      matchingSettings: {
        priorityCategories: [],
        minSubscribers: 1000,
        maxSubscribers: 1000000,
        minEngagementRate: 2.0,
        excludeCategories: [],
        geographicFocus: ['日本'],
        priorityKeywords: [],
        excludeKeywords: []
      },
      createdAt: now,
      updatedAt: now
    };
  }
}

// シングルトンインスタンス
export const firestoreAdminService = new FirestoreAdminService();