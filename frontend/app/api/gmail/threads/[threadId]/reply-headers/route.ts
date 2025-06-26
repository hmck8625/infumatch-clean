import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/lib/auth';
import { GmailService } from '@/lib/gmail';

export async function GET(
  request: NextRequest,
  { params }: { params: { threadId: string } }
) {
  try {
    const session = await getServerSession(authOptions);
    
    if (!session?.accessToken) {
      return NextResponse.json(
        { error: 'Authentication required' },
        { status: 401 }
      );
    }

    const threadId = params.threadId;
    const { searchParams } = new URL(request.url);
    const messageId = searchParams.get('messageId');

    if (!messageId) {
      return NextResponse.json(
        { error: 'messageId parameter is required' },
        { status: 400 }
      );
    }

    console.log('📧 Getting reply headers for threadId:', threadId, 'messageId:', messageId);

    // GmailServiceのインスタンスを作成
    const gmailService = new GmailService(session.accessToken);
    
    // 返信ヘッダー情報を取得
    const replyHeaders = await gmailService.getReplyHeaders(messageId);
    
    console.log('📧 Reply headers retrieved:', replyHeaders);

    return NextResponse.json(replyHeaders);
  } catch (error: any) {
    console.error('❌ Reply headers API error:', error);
    
    // トークンエラーの場合
    if (error.message === 'TOKEN_EXPIRED') {
      return NextResponse.json(
        { error: 'Token expired', requiresReauth: true },
        { status: 401 }
      );
    }
    
    return NextResponse.json(
      { 
        error: 'Failed to get reply headers',
        details: error.message || 'Unknown error'
      },
      { status: 500 }
    );
  }
}