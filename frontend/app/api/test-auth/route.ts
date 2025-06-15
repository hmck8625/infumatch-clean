import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth';

// Force dynamic rendering for this API route
export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  try {
    console.log('🧪 Test auth API called');
    
    // セッション情報を取得
    const session = await getServerSession(authOptions);
    
    console.log('Session details:', {
      hasSession: !!session,
      hasUser: !!session?.user,
      userEmail: session?.user?.email,
      hasAccessToken: !!session?.accessToken,
      tokenLength: session?.accessToken?.length,
      hasError: !!session?.error,
      error: session?.error
    });
    
    // 環境変数チェック
    const envCheck = {
      GOOGLE_CLIENT_ID: !!process.env.GOOGLE_CLIENT_ID,
      GOOGLE_CLIENT_SECRET: !!process.env.GOOGLE_CLIENT_SECRET,
      NEXTAUTH_URL: process.env.NEXTAUTH_URL,
      NEXTAUTH_SECRET: !!process.env.NEXTAUTH_SECRET
    };
    
    console.log('Environment variables:', envCheck);
    
    return NextResponse.json({
      success: true,
      session: {
        hasSession: !!session,
        hasUser: !!session?.user,
        userEmail: session?.user?.email,
        hasAccessToken: !!session?.accessToken,
        tokenLength: session?.accessToken?.length,
        hasError: !!session?.error,
        error: session?.error
      },
      environment: envCheck
    });
  } catch (error: any) {
    console.error('❌ Test auth API error:', {
      message: error?.message,
      stack: error?.stack,
      name: error?.name
    });
    
    return NextResponse.json(
      { 
        error: 'Test auth failed',
        details: error?.message || 'Unknown error'
      },
      { status: 500 }
    );
  }
}