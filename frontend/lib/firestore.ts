/**
 * Firestore Client for Settings Management
 * 
 * @description ユーザー設定データの永続化とCRUD操作を管理
 * @author InfuMatch Development Team
 * @version 1.0.0
 */

import { initializeApp, getApps, getApp } from 'firebase/app';
import { 
  getFirestore, 
  doc, 
  getDoc, 
  setDoc, 
  updateDoc, 
  deleteDoc,
  collection,
  query,
  where,
  getDocs,
  DocumentData,
  FirestoreError
} from 'firebase/firestore';
import { getAuth, connectAuthEmulator } from 'firebase/auth';

// Firebase設定
const firebaseConfig = {
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID || 'hackathon-462905',
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN || 'hackathon-462905.firebaseapp.com',
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET || 'hackathon-462905.appspot.com',
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID || '269567634217',
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID || '1:269567634217:web:a1b2c3d4e5f6g7h8i9j0k1l2',
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY || 'AIzaSyBxxxYourActualFirebaseAPIKeyHerexxxx'
};

// Firebase初期化 - ビルド時エラー回避
let app: any;
let db: any; 
let auth: any;

try {
  // 必要な環境変数をチェック
  const requiredVars = {
    projectId: firebaseConfig.projectId,
    apiKey: firebaseConfig.apiKey,
    authDomain: firebaseConfig.authDomain
  };
  
  console.log('🔍 Firebase config check:', {
    hasProjectId: !!requiredVars.projectId,
    hasApiKey: !!requiredVars.apiKey && requiredVars.apiKey !== 'AIzaSyDk1Lm3a9_sampleApiKey_Replace_With_Real_One',
    hasAuthDomain: !!requiredVars.authDomain,
    environment: process.env.NODE_ENV
  });
  
  // 本番環境では常に初期化を試行
  if (process.env.NODE_ENV === 'production' || typeof window !== 'undefined' || process.env.NODE_ENV === 'development') {
    if (!requiredVars.apiKey || requiredVars.apiKey.includes('sample')) {
      throw new Error('Firebase API key is missing or invalid');
    }
    
    app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApp();
    db = getFirestore(app);
    auth = getAuth(app);
    console.log('✅ Firebase initialized successfully');
  }
} catch (error) {
  console.error('❌ Firebase initialization failed:', error);
  console.error('❌ Config used:', firebaseConfig);
  // フォールバック - ダミーオブジェクトを作成
  app = null;
  db = null;
  auth = null;
}

// 開発環境でエミュレータを使用
if (process.env.NODE_ENV === 'development' && typeof window !== 'undefined') {
  try {
    // エミュレータ接続は一度だけ実行
    if (!auth.currentUser && window.location.hostname === 'localhost') {
      // connectAuthEmulator(auth, 'http://localhost:9099', { disableWarnings: true });
    }
  } catch (error) {
    console.log('Firebase emulator already connected');
  }
}

export { db, auth };

// 設定データの型定義
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
 * Firestore CRUD操作クラス
 */
export class FirestoreSettingsService {
  private readonly COLLECTION_NAME = 'user_settings';

  /**
   * ユーザー設定を取得
   */
  async getUserSettings(userId: string): Promise<FirestoreResponse<UserSettings>> {
    try {
      console.log(`📖 Fetching settings for user: ${userId}`);
      
      // ビルド時やFirebase未初期化時のフォールバック
      if (!db) {
        console.warn('⚠️ Firestore not initialized, returning default settings');
        const defaultSettings = this.getDefaultSettings(userId);
        return { success: true, data: defaultSettings };
      }
      
      const docRef = doc(db, this.COLLECTION_NAME, userId);
      const docSnap = await getDoc(docRef);

      if (docSnap.exists()) {
        const data = docSnap.data() as UserSettings;
        console.log('✅ Settings found in Firestore');
        return { success: true, data };
      } else {
        console.log('📄 No settings found, returning default settings');
        const defaultSettings = this.getDefaultSettings(userId);
        return { success: true, data: defaultSettings };
      }
    } catch (error) {
      console.error('❌ Error fetching settings:', error);
      return { 
        success: false, 
        error: `設定の取得に失敗しました: ${(error as Error).message}` 
      };
    }
  }

  /**
   * ユーザー設定を保存
   */
  async saveUserSettings(userId: string, settings: Partial<UserSettings>): Promise<FirestoreResponse<UserSettings>> {
    try {
      console.log(`💾 Saving settings for user: ${userId}`);
      
      // ビルド時やFirebase未初期化時のフォールバック
      if (!db) {
        console.warn('⚠️ Firestore not initialized, cannot save settings');
        return { 
          success: false, 
          error: 'Firestore not available during build time' 
        };
      }
      
      const docRef = doc(db, this.COLLECTION_NAME, userId);
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

      await setDoc(docRef, updatedSettings, { merge: true });
      
      console.log('✅ Settings saved successfully');
      return { success: true, data: updatedSettings };
    } catch (error) {
      console.error('❌ Error saving settings:', error);
      return { 
        success: false, 
        error: `設定の保存に失敗しました: ${(error as Error).message}` 
      };
    }
  }

  /**
   * 特定の設定セクションを更新
   */
  async updateSettingsSection(
    userId: string, 
    section: keyof Omit<UserSettings, 'id' | 'userId' | 'createdAt' | 'updatedAt'>, 
    data: any
  ): Promise<FirestoreResponse<UserSettings>> {
    try {
      console.log(`🔄 Updating ${section} for user: ${userId}`);
      
      const docRef = doc(db, this.COLLECTION_NAME, userId);
      const updateData = {
        [section]: data,
        updatedAt: new Date().toISOString()
      };

      await updateDoc(docRef, updateData);
      
      // 更新後のデータを取得
      const updated = await this.getUserSettings(userId);
      
      console.log(`✅ ${section} updated successfully`);
      return updated;
    } catch (error) {
      console.error(`❌ Error updating ${section}:`, error);
      return { 
        success: false, 
        error: `${section}の更新に失敗しました: ${(error as Error).message}` 
      };
    }
  }

  /**
   * ユーザー設定を削除
   */
  async deleteUserSettings(userId: string): Promise<FirestoreResponse<void>> {
    try {
      console.log(`🗑️ Deleting settings for user: ${userId}`);
      
      const docRef = doc(db, this.COLLECTION_NAME, userId);
      await deleteDoc(docRef);
      
      console.log('✅ Settings deleted successfully');
      return { success: true };
    } catch (error) {
      console.error('❌ Error deleting settings:', error);
      return { 
        success: false, 
        error: `設定の削除に失敗しました: ${(error as Error).message}` 
      };
    }
  }

  /**
   * 複数ユーザーの設定を取得（管理者用）
   */
  async getAllUserSettings(): Promise<FirestoreResponse<UserSettings[]>> {
    try {
      console.log('📚 Fetching all user settings');
      
      const collectionRef = collection(db, this.COLLECTION_NAME);
      const querySnapshot = await getDocs(collectionRef);
      
      const settings: UserSettings[] = [];
      querySnapshot.forEach((doc) => {
        settings.push({ id: doc.id, ...doc.data() } as UserSettings);
      });
      
      console.log(`✅ Found ${settings.length} user settings`);
      return { success: true, data: settings };
    } catch (error) {
      console.error('❌ Error fetching all settings:', error);
      return { 
        success: false, 
        error: `全設定の取得に失敗しました: ${(error as Error).message}` 
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

  /**
   * Firestore接続テスト
   */
  async testConnection(): Promise<FirestoreResponse<string>> {
    try {
      console.log('🔌 Testing Firestore connection');
      
      const testDoc = doc(db, 'connection_test', 'test');
      await setDoc(testDoc, { timestamp: new Date().toISOString() });
      
      console.log('✅ Firestore connection successful');
      return { success: true, data: 'Connection successful' };
    } catch (error) {
      console.error('❌ Firestore connection failed:', error);
      return { 
        success: false, 
        error: `接続テストに失敗しました: ${(error as Error).message}` 
      };
    }
  }
}

// シングルトンインスタンス
export const firestoreSettingsService = new FirestoreSettingsService();