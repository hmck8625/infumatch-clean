import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth';

// バックエンドAPIのURL
const BACKEND_API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * GET: ユーザー設定を取得
 */
export async function GET(request: NextRequest) {
  try {
    console.log('📞 Settings API GET request received');
    const session = await getServerSession(authOptions);
    
    if (!session?.user?.email) {
      console.log('❌ No session or email found');
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    console.log('👤 User email:', session.user.email);
    
    // バックエンドAPIにリクエストを転送
    const response = await fetch(`${BACKEND_API_URL}/api/settings`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${session.user.email}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      console.error('❌ Backend API error:', response.status);
      const errorText = await response.text();
      console.error('❌ Error details:', errorText);
      
      // エラーでもデフォルト設定を返す
      const defaultSettings = getDefaultSettings(session.user.email);
      return NextResponse.json({
        success: true,
        data: defaultSettings,
        fallback: true,
        message: 'Using default settings - backend not available'
      });
    }

    const data = await response.json();
    console.log('✅ Settings retrieved successfully from backend');
    
    return NextResponse.json({
      success: true,
      data: data
    });
  } catch (error) {
    console.error('❌ 設定取得エラー:', error);
    
    // エラーが発生した場合もデフォルト設定を返す
    try {
      const session = await getServerSession(authOptions);
      if (session?.user?.email) {
        const defaultSettings = getDefaultSettings(session.user.email);
        
        return NextResponse.json({
          success: true,
          data: defaultSettings,
          fallback: true,
          message: 'Using default settings due to error',
          error: error instanceof Error ? error.message : 'Unknown error'
        });
      }
    } catch (fallbackError) {
      console.error('❌ Fallback also failed:', fallbackError);
    }
    
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
    
    if (!session?.user?.email) {
      console.log('❌ No session found for PUT request');
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    console.log('👤 User email:', session.user.email);
    const body = await request.json();
    
    console.log('📦 Request body received:', JSON.stringify(body, null, 2));
    
    // バックエンドAPIにリクエストを転送
    const response = await fetch(`${BACKEND_API_URL}/api/settings`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${session.user.email}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body)
    });

    if (!response.ok) {
      console.error('❌ Backend API error:', response.status);
      const errorText = await response.text();
      console.error('❌ Error details:', errorText);
      
      return NextResponse.json(
        { error: 'Failed to save settings' },
        { status: response.status }
      );
    }

    const data = await response.json();
    console.log('✅ Settings saved successfully to backend');
    
    return NextResponse.json({ 
      success: true, 
      message: 'Settings saved successfully',
      data: data 
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
    
    // バックエンドAPIにリクエストを転送
    const response = await fetch(`${BACKEND_API_URL}/api/settings/section/${section}`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${session.user.email}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body)
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('❌ Backend API error:', errorText);
      
      return NextResponse.json(
        { error: 'Failed to update settings section' },
        { status: response.status }
      );
    }

    const data = await response.json();
    
    return NextResponse.json(data);
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

    // バックエンドAPIにリクエストを転送
    const response = await fetch(`${BACKEND_API_URL}/api/settings`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${session.user.email}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('❌ Backend API error:', errorText);
      
      return NextResponse.json(
        { error: 'Failed to delete settings' },
        { status: response.status }
      );
    }

    const data = await response.json();
    
    return NextResponse.json(data);
  } catch (error) {
    console.error('設定削除エラー:', error);
    return NextResponse.json(
      { error: 'Failed to delete settings' },
      { status: 500 }
    );
  }
}

/**
 * デフォルト設定を生成
 */
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