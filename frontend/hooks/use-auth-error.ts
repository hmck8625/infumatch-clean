import { useSession, signIn } from 'next-auth/react';
import { useEffect } from 'react';

interface AuthErrorResponse {
  error: string;
  code: string;
}

export function useAuthError() {
  const { data: session, status } = useSession();

  const handleAuthError = (error: any) => {
    if (error?.code === 'TOKEN_EXPIRED' || error?.code === 'TOKEN_REFRESH_FAILED') {
      // シンプルなalertとconfirmで代替
      const shouldRelogin = confirm('認証が期限切れです。再ログインしますか？');
      if (shouldRelogin) {
        signIn('google');
      }
      return true;
    }
    
    if (error?.code === 'NO_SESSION') {
      const shouldLogin = confirm('ログインが必要です。ログインしますか？');
      if (shouldLogin) {
        signIn('google');
      }
      return true;
    }

    return false;
  };

  const handleApiResponse = async (response: Response) => {
    if (response.status === 401) {
      try {
        const errorData: AuthErrorResponse = await response.json();
        return handleAuthError(errorData);
      } catch {
        return handleAuthError({ code: 'NO_SESSION' });
      }
    }
    return false;
  };

  // セッションレベルでのエラーチェック
  useEffect(() => {
    if (session?.error === 'RefreshAccessTokenError') {
      handleAuthError({ code: 'TOKEN_REFRESH_FAILED' });
    }
  }, [session?.error]);

  return {
    handleAuthError,
    handleApiResponse,
    isAuthenticated: status === 'authenticated' && !session?.error,
  };
}