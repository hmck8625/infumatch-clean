import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from './auth';

export async function withAuth(
  handler: (req: NextRequest, session: any, ...args: any[]) => Promise<NextResponse>
) {
  return async (req: NextRequest, ...args: any[]) => {
    try {
      console.log('🔐 Auth middleware: Getting session...');
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
      
      if (!session?.accessToken) {
        console.log('❌ No access token found');
        return NextResponse.json(
          { error: 'Unauthorized', code: 'NO_SESSION' },
          { status: 401 }
        );
      }

      // セッションにエラーがある場合は再認証を促す
      if (session.error === 'RefreshAccessTokenError') {
        console.log('❌ Token refresh failed');
        return NextResponse.json(
          { 
            error: 'Token refresh failed. Please re-authenticate.',
            code: 'TOKEN_REFRESH_FAILED'
          },
          { status: 401 }
        );
      }
      
      console.log('✅ Auth middleware: Session valid, proceeding...');

      // ハンドラーを実行
      try {
        return await handler(req, session, ...args);
      } catch (error: any) {
        // Gmail APIからのトークンエラーを検知
        if (error?.message === 'TOKEN_EXPIRED') {
          return NextResponse.json(
            { 
              error: 'Access token expired. Please re-authenticate.',
              code: 'TOKEN_EXPIRED'
            },
            { status: 401 }
          );
        }
        throw error;
      }
    } catch (error: any) {
      console.error('❌ Auth middleware error:', {
        message: error?.message,
        stack: error?.stack,
        name: error?.name
      });
      return NextResponse.json(
        { error: 'Internal server error', details: error?.message },
        { status: 500 }
      );
    }
  };
}