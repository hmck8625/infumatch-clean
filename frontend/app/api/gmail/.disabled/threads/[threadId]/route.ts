import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
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
        { error: 'Unauthorized', code: 'NO_SESSION' },
        { status: 401 }
      );
    }

    // セッションにエラーがある場合は再認証を促す
    if (session.error === 'RefreshAccessTokenError') {
      return NextResponse.json(
        { 
          error: 'Token refresh failed. Please re-authenticate.',
          code: 'TOKEN_REFRESH_FAILED'
        },
        { status: 401 }
      );
    }

    const gmailService = new GmailService(session.accessToken, session.user?.email || 'default');
    
    try {
      const thread = await gmailService.getThread(params.threadId);
      return NextResponse.json({ thread });
    } catch (gmailError: any) {
      // Gmail APIからのトークンエラーを検知
      if (gmailError?.message === 'TOKEN_EXPIRED') {
        return NextResponse.json(
          { 
            error: 'Access token expired. Please re-authenticate.',
            code: 'TOKEN_EXPIRED'
          },
          { status: 401 }
        );
      }
      throw gmailError;
    }
  } catch (error) {
    console.error('Gmail thread詳細API エラー:', error);
    return NextResponse.json(
      { error: 'Failed to fetch email thread' },
      { status: 500 }
    );
  }
}