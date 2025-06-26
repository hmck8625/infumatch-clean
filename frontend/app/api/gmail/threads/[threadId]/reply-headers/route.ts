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

    const { threadId } = params;
    const { searchParams } = new URL(request.url);
    const messageId = searchParams.get('messageId');

    if (!threadId || !messageId) {
      return NextResponse.json(
        { error: 'Missing threadId or messageId' },
        { status: 400 }
      );
    }

    console.log('🔍 Getting reply headers for thread:', threadId, 'message:', messageId);

    // Gmail Serviceを使用して返信ヘッダーを取得
    const gmailService = new GmailService(session.accessToken, session.user?.email || 'default');
    const replyHeaders = await gmailService.getReplyHeaders(messageId);

    console.log('📧 Reply headers retrieved:', replyHeaders);

    return NextResponse.json({
      success: true,
      replyHeaders,
      threadId,
      messageId
    });

  } catch (error: any) {
    console.error('Reply headers API error:', error);
    
    // トークンエラーをクライアントに伝える
    if (error.message === 'TOKEN_EXPIRED') {
      return NextResponse.json(
        { error: 'TOKEN_EXPIRED', message: 'Authentication token has expired' },
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