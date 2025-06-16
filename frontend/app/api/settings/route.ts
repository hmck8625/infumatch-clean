import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth';

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
    
    // バックエンドAPIから設定を取得
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
    const apiResponse = await fetch(`${backendUrl}/api/v1/user/settings?user_id=${encodeURIComponent(session.user.email)}`);
    
    if (apiResponse.ok) {
      const data = await apiResponse.json();
      console.log('✅ Settings retrieved from backend successfully');
      return NextResponse.json({
        success: true,
        data: data
      });
    } else if (apiResponse.status === 404) {
      // デフォルト設定を返す
      const defaultSettings = {
        userId: session.user.email,
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
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      };
      
      return NextResponse.json({
        success: true,
        data: defaultSettings,
        fallback: true,
        message: 'デフォルト設定を使用しています'
      });
    } else {
      console.error('❌ Failed to get settings from backend:', apiResponse.status);
      return NextResponse.json(
        { error: 'バックエンドから設定を取得できませんでした' },
        { status: 500 }
      );
    }
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
    
    // バックエンドAPIに設定を保存
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
    const apiResponse = await fetch(`${backendUrl}/api/v1/user/settings`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: session.user.email,
        settings: body
      })
    });
    
    if (apiResponse.ok) {
      const data = await apiResponse.json();
      console.log('✅ Settings saved to backend successfully');
      return NextResponse.json({ 
        success: true, 
        message: 'Settings saved successfully',
        data: data 
      });
    } else {
      console.error('❌ Failed to save settings to backend:', apiResponse.status);
      const errorText = await apiResponse.text();
      console.error('❌ Backend error details:', errorText);
      return NextResponse.json(
        { error: 'バックエンドへの保存に失敗しました' },
        { status: 500 }
      );
    }
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
    
    // Firestoreの設定セクションを更新
    const result = await firestoreSettingsService.updateSettingsSection(
      session.user.email, 
      section as any, 
      body
    );
    
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

    // Firestoreから設定を削除
    const result = await firestoreSettingsService.deleteUserSettings(session.user.email);
    
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