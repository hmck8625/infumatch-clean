import { NextAuthOptions } from 'next-auth';
import GoogleProvider from 'next-auth/providers/google';
import { JWT } from 'next-auth/jwt';

// リフレッシュトークンを使用してアクセストークンを更新
async function refreshAccessToken(token: JWT) {
  try {
    console.log('🔄 Refreshing access token...');
    
    const url = 'https://oauth2.googleapis.com/token';
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        client_id: process.env.GOOGLE_CLIENT_ID!,
        client_secret: process.env.GOOGLE_CLIENT_SECRET!,
        refresh_token: token.refreshToken as string,
        grant_type: 'refresh_token',
      }),
    });

    const refreshedTokens = await response.json();

    if (!response.ok) {
      console.error('❌ Failed to refresh token:', refreshedTokens);
      throw refreshedTokens;
    }

    console.log('✅ Access token refreshed successfully');
    
    return {
      ...token,
      accessToken: refreshedTokens.access_token,
      accessTokenExpires: Date.now() + (refreshedTokens.expires_in ?? 3599) * 1000,
      refreshToken: refreshedTokens.refresh_token ?? token.refreshToken, // 新しいリフレッシュトークンが提供されない場合は既存のものを使用
    };
  } catch (error) {
    console.error('❌ Error refreshing access token:', error);
    
    return {
      ...token,
      error: 'RefreshAccessTokenError',
    };
  }
}

export const authOptions: NextAuthOptions = {
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
      authorization: {
        params: {
          scope: 'openid email profile https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/gmail.send https://www.googleapis.com/auth/gmail.compose',
          access_type: 'offline',
          prompt: 'consent',
        },
      },
    }),
  ],
  callbacks: {
    async jwt({ token, account, user }) {
      // 初回ログイン時
      if (account && user) {
        console.log('🔐 Initial login - storing tokens');
        return {
          ...token,
          accessToken: account.access_token,
          refreshToken: account.refresh_token,
          accessTokenExpires: account.expires_at ? account.expires_at * 1000 : Date.now() + 3600 * 1000,
          id: user.id,
        };
      }

      // アクセストークンがまだ有効な場合はそのまま返す
      if (Date.now() < (token.accessTokenExpires as number)) {
        return token;
      }

      // アクセストークンが期限切れの場合、リフレッシュトークンで更新
      console.log('⏰ Access token expired, refreshing...');
      return refreshAccessToken(token);
    },
    async session({ session, token }) {
      // セッションにアクセストークンとエラー情報を含める
      session.accessToken = token.accessToken as string;
      session.error = token.error as string | undefined;
      
      // トークンエラーがある場合はログ出力
      if (token.error) {
        console.error('⚠️ Session has token error:', token.error);
      }
      
      return session;
    },
  },
  pages: {
    signIn: '/auth/signin',
    error: '/auth/error',
  },
  session: {
    strategy: 'jwt',
  },
};