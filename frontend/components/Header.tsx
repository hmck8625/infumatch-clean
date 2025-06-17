'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState } from 'react';
import { useSession, signOut } from 'next-auth/react';
import { 
  Menu, 
  X, 
  User, 
  LogOut,
  Settings as SettingsIcon,
  Bell,
  ChevronDown
} from 'lucide-react';

interface HeaderProps {
  variant?: 'default' | 'transparent' | 'glass';
  showAuth?: boolean;
  extraActions?: React.ReactNode;
}

interface NavigationItem {
  name: string;
  href: string;
  description?: string;
}

const navigation: NavigationItem[] = [
  { name: '検索', href: '/search', description: 'インフルエンサー検索' },
  { name: 'AIマッチング', href: '/matching', description: 'AI推薦システム' },
  { name: 'メッセージ', href: '/messages', description: 'コラボ交渉' },
  { name: '設定', href: '/settings', description: 'アカウント設定' },
];

export default function Header({ 
  variant = 'default', 
  showAuth = true,
  extraActions 
}: HeaderProps) {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  // NextAuth.jsを使用した実際の認証状態
  const { data: session, status } = useSession();
  const isAuthenticated = status === 'authenticated';
  const user = session?.user || null;

  const getHeaderStyle = () => {
    switch (variant) {
      case 'transparent':
        return 'bg-transparent';
      case 'glass':
        return 'bg-white/80 backdrop-blur-md shadow-sm border-b border-gray-200/50';
      default:
        return 'bg-white shadow-sm border-b border-gray-200';
    }
  };

  const getLogoStyle = () => {
    switch (variant) {
      case 'transparent':
        return 'text-white';
      default:
        return 'bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent';
    }
  };

  const getNavStyle = () => {
    switch (variant) {
      case 'transparent':
        return 'text-white/80 hover:text-white';
      default:
        return 'text-gray-600 hover:text-indigo-600';
    }
  };

  const handleLogout = async () => {
    setUserMenuOpen(false);
    await signOut({ callbackUrl: '/' });
  };

  return (
    <header className={`sticky top-0 z-50 transition-all duration-200 ${getHeaderStyle()}`}>
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* ロゴ */}
          <div className="flex items-center">
            <Link href="/" className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gradient-to-br from-purple-600 to-blue-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">IM</span>
              </div>
              <span className={`text-2xl font-bold ${getLogoStyle()}`}>
                InfuMatch
              </span>
            </Link>
          </div>

          {/* デスクトップナビゲーション */}
          <nav className="hidden md:flex space-x-8">
            {navigation.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={`relative px-3 py-2 text-sm font-medium transition-colors ${
                    isActive
                      ? 'text-indigo-600 font-semibold'
                      : getNavStyle()
                  }`}
                >
                  {item.name}
                  {isActive && (
                    <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-indigo-600 rounded-full" />
                  )}
                </Link>
              );
            })}
          </nav>

          {/* 右側のアクション */}
          <div className="flex items-center space-x-4">
            {/* 追加アクション */}
            {extraActions}

            {/* 認証関連 */}
            {showAuth && (
              <div className="flex items-center space-x-4">
                {isAuthenticated ? (
                  <div className="relative">
                    {/* 通知ベル */}
                    <button className="p-2 text-gray-400 hover:text-gray-600 transition-colors">
                      <Bell className="w-5 h-5" />
                    </button>

                    {/* ユーザーメニュー */}
                    <div className="relative">
                      <button
                        onClick={() => setUserMenuOpen(!userMenuOpen)}
                        className="flex items-center space-x-3 p-2 rounded-lg hover:bg-gray-100 transition-colors"
                      >
                        <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-blue-500 rounded-full flex items-center justify-center">
                          <User className="w-4 h-4 text-white" />
                        </div>
                        <div className="hidden md:block text-left">
                          <div className="text-sm font-medium text-gray-900">{user?.name || 'ユーザー'}</div>
                          <div className="text-xs text-gray-500">{user?.email || ''}</div>
                        </div>
                        <ChevronDown className="w-4 h-4 text-gray-400" />
                      </button>

                      {/* ユーザーメニュードロップダウン */}
                      {userMenuOpen && (
                        <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg border border-gray-200 py-1">
                          <Link
                            href="/settings"
                            className="flex items-center space-x-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                            onClick={() => setUserMenuOpen(false)}
                          >
                            <SettingsIcon className="w-4 h-4" />
                            <span>設定</span>
                          </Link>
                          <button
                            onClick={handleLogout}
                            className="flex items-center space-x-2 w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                          >
                            <LogOut className="w-4 h-4" />
                            <span>ログアウト</span>
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="flex items-center space-x-2">
                    <Link
                      href="/auth/signin"
                      className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
                    >
                      ログイン
                    </Link>
                    <Link
                      href="/auth/signup"
                      className="px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-purple-600 to-blue-600 rounded-lg hover:from-purple-700 hover:to-blue-700 transition-all duration-200"
                    >
                      新規登録
                    </Link>
                  </div>
                )}
              </div>
            )}

            {/* モバイルメニューボタン */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100 transition-colors"
            >
              {mobileMenuOpen ? (
                <X className="w-6 h-6" />
              ) : (
                <Menu className="w-6 h-6" />
              )}
            </button>
          </div>
        </div>

        {/* モバイルメニュー */}
        {mobileMenuOpen && (
          <div className="md:hidden border-t border-gray-200 py-4">
            <div className="space-y-1">
              {navigation.map((item) => {
                const isActive = pathname === item.href;
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={`block px-3 py-2 text-base font-medium rounded-md transition-colors ${
                      isActive
                        ? 'text-indigo-600 bg-indigo-50'
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                    }`}
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    <div>{item.name}</div>
                    {item.description && (
                      <div className="text-xs text-gray-500 mt-1">{item.description}</div>
                    )}
                  </Link>
                );
              })}
            </div>

            {/* モバイル認証セクション */}
            {showAuth && (
              <div className="mt-4 pt-4 border-t border-gray-200">
                {isAuthenticated ? (
                  <div className="space-y-2">
                    <div className="flex items-center space-x-3 px-3 py-2">
                      <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-blue-500 rounded-full flex items-center justify-center">
                        <User className="w-4 h-4 text-white" />
                      </div>
                      <div>
                        <div className="text-sm font-medium text-gray-900">{user?.name || 'ユーザー'}</div>
                        <div className="text-xs text-gray-500">{user?.email || ''}</div>
                      </div>
                    </div>
                    <button
                      onClick={handleLogout}
                      className="flex items-center space-x-2 w-full px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-md"
                    >
                      <LogOut className="w-4 h-4" />
                      <span>ログアウト</span>
                    </button>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <Link
                      href="/auth/signin"
                      className="block w-full px-3 py-2 text-center text-sm font-medium text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      ログイン
                    </Link>
                    <Link
                      href="/auth/signup"
                      className="block w-full px-3 py-2 text-center text-sm font-medium text-white bg-gradient-to-r from-purple-600 to-blue-600 rounded-md hover:from-purple-700 hover:to-blue-700"
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      新規登録
                    </Link>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </header>
  );
}