import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth';

// Firestore操作のためのサーバーサイド関数
import { initializeApp, getApps, cert } from 'firebase-admin/app';
import { getFirestore } from 'firebase-admin/firestore';
import path from 'path';

// Firebase Admin初期化
let adminApp;
let adminDb = null;

try {
  // 既存のアプリがあるかチェック
  const existingApps = getApps();
  adminApp = existingApps.length > 0 ? existingApps[0] : null;
  
  if (!adminApp) {
    // サービスアカウントキーのパス  
    const serviceAccountPath = path.join(process.cwd(), '..', 'hackathon-462905-7d72a76d3742.json');
    
    console.log('🔑 Initializing Firebase Admin with service account...');
    adminApp = initializeApp({
      credential: cert(serviceAccountPath),
      projectId: 'hackathon-462905'
    });
    console.log('✅ Firebase Admin initialized successfully');
  }
  
  if (adminApp) {
    adminDb = getFirestore(adminApp);
  }
} catch (error) {
  console.error('❌ Firebase Admin initialization error:', error);
  // エラーが発生してもアプリを止めない
  adminApp = null;
  adminDb = null;
}

// 設定データの型定義
interface UserSettings {
  userId: string;
  companyInfo: {
    companyName: string;
    industry: string;
    employeeCount: string;
    website: string;
    description: string;
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
  };
  matchingSettings: {
    priorityCategories: string[];
    minSubscribers: number;
    maxSubscribers: number;
    minEngagementRate: number;
    excludeCategories: string[];
    geographicFocus: string[];
  };
  createdAt: string;
  updatedAt: string;
}

/**
 * Firestoreから設定を取得
 */
async function getSettingsFromFirestore(userId: string): Promise<UserSettings | null> {
  if (!adminDb) {
    console.error('Firebase Admin not initialized');
    return null;
  }

  try {
    console.log(`📖 Fetching settings for user: ${userId}`);
    
    const docRef = adminDb.collection('user_settings').doc(userId);
    const doc = await docRef.get();

    if (doc.exists) {
      const data = doc.data() as UserSettings;
      console.log('✅ Settings found in Firestore');
      return data;
    } else {
      console.log('📄 No settings found, returning default settings');
      return getDefaultSettings(userId);
    }
  } catch (error) {
    console.error('❌ Error fetching settings from Firestore:', error);
    return null;
  }
}

/**
 * Firestoreに設定を保存
 */
async function saveSettingsToFirestore(userId: string, settings: Partial<UserSettings>): Promise<UserSettings | null> {
  if (!adminDb) {
    console.error('Firebase Admin not initialized');
    return null;
  }

  try {
    console.log(`💾 Saving settings for user: ${userId}`);
    
    const docRef = adminDb.collection('user_settings').doc(userId);
    const now = new Date().toISOString();
    
    // 既存設定を取得
    const existing = await getSettingsFromFirestore(userId);
    const baseSettings = existing || getDefaultSettings(userId);
    
    // 更新データをマージ
    const updatedSettings: UserSettings = {
      ...baseSettings,
      ...settings,
      userId,
      updatedAt: now,
      createdAt: baseSettings.createdAt || now
    };

    await docRef.set(updatedSettings, { merge: true });
    
    console.log('✅ Settings saved successfully');
    return updatedSettings;
  } catch (error) {
    console.error('❌ Error saving settings to Firestore:', error);
    return null;
  }
}

/**
 * デフォルト設定を生成
 */
function getDefaultSettings(userId: string): UserSettings {
  const now = new Date().toISOString();
  
  return {
    userId,
    companyInfo: {
      companyName: '',
      industry: '',
      employeeCount: '',
      website: '',
      description: ''
    },
    products: [],
    negotiationSettings: {
      preferredTone: 'professional',
      responseTimeExpectation: '24時間以内',
      budgetFlexibility: 'medium',
      decisionMakers: [],
      communicationPreferences: ['email']
    },
    matchingSettings: {
      priorityCategories: [],
      minSubscribers: 1000,
      maxSubscribers: 1000000,
      minEngagementRate: 2.0,
      excludeCategories: [],
      geographicFocus: ['日本']
    },
    createdAt: now,
    updatedAt: now
  };
}

/**
 * GET: ユーザー設定を取得
 */
export async function GET(request: NextRequest) {
  try {
    const session = await getServerSession(authOptions);
    
    if (!session?.user?.email) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    // ユーザーIDとしてemailを使用
    const userId = session.user.email;
    
    // Firestoreから設定を取得
    const settings = await getSettingsFromFirestore(userId);
    
    if (!settings) {
      return NextResponse.json(
        { error: 'Failed to fetch settings' },
        { status: 500 }
      );
    }
    
    return NextResponse.json({
      success: true,
      data: settings
    });
  } catch (error) {
    console.error('設定取得エラー:', error);
    return NextResponse.json(
      { error: 'Failed to get settings' },
      { status: 500 }
    );
  }
}

/**
 * PUT: ユーザー設定を更新
 */
export async function PUT(request: NextRequest) {
  try {
    const session = await getServerSession(authOptions);
    
    if (!session?.user?.email) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    const body = await request.json();
    const userId = session.user.email;
    
    // バリデーション
    if (body.companyInfo && !body.companyInfo.companyName) {
      return NextResponse.json(
        { error: 'Company name is required' },
        { status: 400 }
      );
    }

    // Firestoreに設定を保存
    const updatedSettings = await saveSettingsToFirestore(userId, body);
    
    if (!updatedSettings) {
      return NextResponse.json(
        { error: 'Failed to save settings' },
        { status: 500 }
      );
    }

    return NextResponse.json({ 
      success: true, 
      message: 'Settings saved successfully',
      data: updatedSettings 
    });
  } catch (error) {
    console.error('設定保存エラー:', error);
    return NextResponse.json(
      { error: 'Failed to save settings' },
      { status: 500 }
    );
  }
}

/**
 * POST: 設定の特定セクションを更新
 */
export async function POST(request: NextRequest) {
  try {
    const session = await getServerSession(authOptions);
    
    if (!session?.user?.email) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    const { section, data } = await request.json();
    const userId = session.user.email;
    
    if (!section || !data) {
      return NextResponse.json(
        { error: 'Section and data are required' },
        { status: 400 }
      );
    }

    // 現在の設定を取得
    const currentSettings = await getSettingsFromFirestore(userId);
    if (!currentSettings) {
      return NextResponse.json(
        { error: 'Failed to fetch current settings' },
        { status: 500 }
      );
    }

    // 指定セクションを更新
    const updatedSettings = {
      ...currentSettings,
      [section]: data,
      updatedAt: new Date().toISOString()
    };

    // Firestoreに保存
    const result = await saveSettingsToFirestore(userId, updatedSettings);
    
    if (!result) {
      return NextResponse.json(
        { error: 'Failed to update settings' },
        { status: 500 }
      );
    }

    return NextResponse.json({ 
      success: true, 
      message: `${section} updated successfully`,
      data: result 
    });
  } catch (error) {
    console.error('設定更新エラー:', error);
    return NextResponse.json(
      { error: 'Failed to update settings' },
      { status: 500 }
    );
  }
}

/**
 * DELETE: ユーザー設定を削除
 */
export async function DELETE(request: NextRequest) {
  try {
    const session = await getServerSession(authOptions);
    
    if (!session?.user?.email) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    const userId = session.user.email;
    
    if (!adminDb) {
      return NextResponse.json(
        { error: 'Database not available' },
        { status: 500 }
      );
    }

    console.log(`🗑️ Deleting settings for user: ${userId}`);
    
    const docRef = adminDb.collection('user_settings').doc(userId);
    await docRef.delete();
    
    console.log('✅ Settings deleted successfully');

    return NextResponse.json({ 
      success: true, 
      message: 'Settings deleted successfully' 
    });
  } catch (error) {
    console.error('設定削除エラー:', error);
    return NextResponse.json(
      { error: 'Failed to delete settings' },
      { status: 500 }
    );
  }
}