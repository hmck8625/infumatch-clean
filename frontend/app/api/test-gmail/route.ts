import { NextRequest, NextResponse } from 'next/server';
import { google } from 'googleapis';

export async function GET(request: NextRequest) {
  try {
    console.log('🧪 Test Gmail API setup');
    
    // 環境変数チェック
    const envCheck = {
      GOOGLE_CLIENT_ID: !!process.env.GOOGLE_CLIENT_ID,
      GOOGLE_CLIENT_SECRET: !!process.env.GOOGLE_CLIENT_SECRET,
      NEXTAUTH_URL: process.env.NEXTAUTH_URL,
    };
    
    console.log('Environment variables:', envCheck);
    
    // OAuth2クライアント作成テスト
    const oauth2Client = new google.auth.OAuth2(
      process.env.GOOGLE_CLIENT_ID,
      process.env.GOOGLE_CLIENT_SECRET,
      `${process.env.NEXTAUTH_URL}/api/auth/callback/google`
    );
    
    console.log('✓ OAuth2 client created successfully');
    
    // Gmail APIクライアント作成テスト（認証なし）
    const gmail = google.gmail({ version: 'v1', auth: oauth2Client });
    console.log('✓ Gmail API client created successfully');
    
    // 認証URL生成テスト
    const scopes = [
      'https://www.googleapis.com/auth/gmail.readonly',
      'https://www.googleapis.com/auth/gmail.send',
      'https://www.googleapis.com/auth/gmail.compose'
    ];
    
    const authUrl = oauth2Client.generateAuthUrl({
      access_type: 'offline',
      scope: scopes,
      prompt: 'consent'
    });
    
    console.log('✓ Auth URL generated successfully');
    
    return NextResponse.json({
      success: true,
      message: 'Gmail API setup is working correctly',
      environment: envCheck,
      authUrl: authUrl.substring(0, 100) + '...',
      scopes
    });
  } catch (error: any) {
    console.error('❌ Test Gmail API error:', {
      message: error?.message,
      stack: error?.stack,
      name: error?.name
    });
    
    return NextResponse.json(
      { 
        error: 'Gmail API test failed',
        details: error?.message || 'Unknown error'
      },
      { status: 500 }
    );
  }
}