import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth';

/**
 * GET: ユーザー設定を取得
 */
// 一時的な設定保存用（メモリ内）
const userSettings = new Map<string, any>();

// デフォルト設定を生成
function getDefaultSettings(userId: string) {
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

export async function GET(request: NextRequest) {
  try {
    console.log('📞 Settings API GET request received');
    const session = await getServerSession(authOptions);
    
    console.log('🔍 Session debug info:', {
      hasSession: !!session,
      hasUser: !!session?.user,
      hasEmail: !!session?.user?.email,
      email: session?.user?.email,
      name: session?.user?.name,
      id: session?.user?.id,
      expires: session?.expires
    });
    
    if (!session?.user?.email) {
      console.log('❌ No session or email found');
      return NextResponse.json(
        { error: 'Unauthorized - No valid session found' },
        { status: 401 }
      );
    }

    console.log('👤 User email:', session.user.email);
    
    // メモリから設定を取得、なければデフォルト設定
    let settings = userSettings.get(session.user.email);
    if (!settings) {
      settings = getDefaultSettings(session.user.email);
      userSettings.set(session.user.email, settings);
    }
    
    console.log('✅ Settings retrieved successfully (from memory)');
    return NextResponse.json({
      success: true,
      data: settings
    });
  } catch (error) {
    console.error('❌ 設定取得エラー:', error);
    return NextResponse.json(
      { error: 'Failed to get settings', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}

/**
 * PUT: ユーザー設定を更新
 */
export async function PUT(request: NextRequest) {
  try {
    console.log('💾 Settings PUT request received');
    const session = await getServerSession(authOptions);
    
    console.log('🔍 PUT Session debug info:', {
      hasSession: !!session,
      hasUser: !!session?.user,
      hasEmail: !!session?.user?.email,
      email: session?.user?.email,
      name: session?.user?.name,
      id: session?.user?.id,
      expires: session?.expires
    });
    
    if (!session?.user?.email) {
      console.log('❌ No session found for PUT request');
      return NextResponse.json(
        { error: 'Unauthorized - No valid session found' },
        { status: 401 }
      );
    }

    console.log('👤 User email:', session.user.email);
    const body = await request.json();
    
    console.log('📦 Request body received:', JSON.stringify(body, null, 2));
    
    // 既存設定を取得またはデフォルト設定を使用
    let existingSettings = userSettings.get(session.user.email);
    if (!existingSettings) {
      existingSettings = getDefaultSettings(session.user.email);
    }
    
    // 設定をマージして更新
    const updatedSettings = {
      ...existingSettings,
      ...body,
      userId: session.user.email,
      updatedAt: new Date().toISOString(),
      createdAt: existingSettings.createdAt || new Date().toISOString()
    };
    
    // メモリに保存
    userSettings.set(session.user.email, updatedSettings);
    
    console.log('✅ Settings saved successfully (to memory)');
    return NextResponse.json({ 
      success: true, 
      message: 'Settings saved successfully',
      data: updatedSettings 
    });
  } catch (error) {
    console.error('❌ 設定保存エラー:', error);
    console.error('❌ Error stack:', error instanceof Error ? error.stack : 'No stack trace');
    return NextResponse.json(
      { 
        error: 'Failed to save settings',
        details: error instanceof Error ? error.message : 'Unknown error'
      },
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

    const url = new URL(request.url);
    const pathParts = url.pathname.split('/');
    const section = pathParts[pathParts.length - 1];
    
    const body = await request.json();
    
    // 有効なセクションをチェック
    const validSections = ['companyInfo', 'products', 'negotiationSettings', 'matchingSettings'];
    if (!validSections.includes(section)) {
      return NextResponse.json(
        { error: 'Invalid section' },
        { status: 400 }
      );
    }
    
    // メモリ内設定を部分更新
    let existingSettings = userSettings.get(session.user.email);
    if (!existingSettings) {
      existingSettings = getDefaultSettings(session.user.email);
    }
    
    const updatedSettings = {
      ...existingSettings,
      [section]: body,
      updatedAt: new Date().toISOString()
    };
    
    userSettings.set(session.user.email, updatedSettings);
    
    const result = { success: true, data: updatedSettings };
    
    if (result.success) {
      return NextResponse.json({
        success: true,
        message: `${section} updated successfully`,
        data: result.data
      });
    } else {
      return NextResponse.json(
        { error: result.error },
        { status: 500 }
      );
    }
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

    // メモリから設定を削除
    userSettings.delete(session.user.email);
    const result = { success: true };
    
    if (result.success) {
      return NextResponse.json({ 
        success: true, 
        message: 'Settings deleted successfully' 
      });
    } else {
      return NextResponse.json(
        { error: result.error },
        { status: 500 }
      );
    }
  } catch (error) {
    console.error('設定削除エラー:', error);
    return NextResponse.json(
      { error: 'Failed to delete settings' },
      { status: 500 }
    );
  }
}