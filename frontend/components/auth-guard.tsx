'use client';

import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { useEffect, ReactNode } from 'react';

interface AuthGuardProps {
  children: ReactNode;
  requireAuth?: boolean;
  fallbackUrl?: string;
}

/**
 * 認証ガードコンポーネント
 * 
 * 認証が必要なページを保護し、未認証の場合はサインインページにリダイレクト
 */
export function AuthGuard({ 
  children, 
  requireAuth = true, 
  fallbackUrl = '/auth/signin' 
}: AuthGuardProps) {
  const { data: session, status } = useSession();
  const router = useRouter();

  useEffect(() => {
    if (requireAuth && status === 'unauthenticated') {
      router.push(fallbackUrl);
    }
  }, [status, requireAuth, fallbackUrl, router]);

  // ローディング状態
  if (status === 'loading') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p className="text-gray-600">認証状態を確認中...</p>
        </div>
      </div>
    );
  }

  // 認証が必要だが未認証の場合
  if (requireAuth && !session) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center">
        <div className="text-center">
          <div className="mb-4">
            <svg className="w-16 h-16 text-gray-400 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">認証が必要です</h2>
          <p className="text-gray-600 mb-4">この機能を利用するにはログインが必要です。</p>
          <button
            onClick={() => router.push(fallbackUrl)}
            className="btn btn-primary"
          >
            ログインページへ
          </button>
        </div>
      </div>
    );
  }

  // 認証済みまたは認証不要の場合、子コンポーネントを表示
  return <>{children}</>;
}

/**
 * 認証済みユーザー情報表示コンポーネント
 */
export function UserInfo() {
  const { data: session } = useSession();

  if (!session?.user) {
    return null;
  }

  return (
    <div className="flex items-center space-x-3">
      {session.user.image && (
        <img
          src={session.user.image}
          alt={session.user.name || 'User'}
          className="w-8 h-8 rounded-full"
        />
      )}
      <div className="text-sm">
        <p className="font-medium text-gray-900">{session.user.name}</p>
        <p className="text-gray-500">{session.user.email}</p>
      </div>
    </div>
  );
}

/**
 * ログイン状態に応じて異なるコンテンツを表示するコンポーネント
 */
export function AuthContent({ 
  authenticated, 
  unauthenticated 
}: { 
  authenticated: ReactNode;
  unauthenticated: ReactNode;
}) {
  const { data: session, status } = useSession();

  if (status === 'loading') {
    return (
      <div className="flex items-center justify-center p-4">
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return <>{session ? authenticated : unauthenticated}</>;
}