'use client';

import Link from 'next/link';
import { useState, useEffect } from 'react';
import { signOut, useSession } from 'next-auth/react';
import { AuthContent, UserInfo } from '@/components/auth-guard';

export default function HomePage() {
  const [isVisible, setIsVisible] = useState(false);
  const { data: session } = useSession();

  useEffect(() => {
    setIsVisible(true);
  }, []);

  const handleLogout = async () => {
    try {
      await signOut({ 
        callbackUrl: '/',
        redirect: true 
      });
    } catch (error) {
      console.error('ログアウトエラー:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 relative overflow-hidden">
      {/* 背景アニメーション */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -inset-10 opacity-50">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-purple-500 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-float"></div>
          <div className="absolute top-1/3 right-1/4 w-96 h-96 bg-cyan-500 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-float" style={{animationDelay: '2s'}}></div>
          <div className="absolute bottom-1/4 left-1/3 w-96 h-96 bg-pink-500 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-float" style={{animationDelay: '4s'}}></div>
        </div>
      </div>

      {/* ナビゲーション */}
      <nav className="relative z-10 bg-glass backdrop-blur-md border-b border-white/10">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="text-2xl font-bold text-gradient">
              InfuMatch
            </div>
            <div className="hidden md:flex space-x-8">
              <Link href="/search" className="text-white/80 hover:text-white transition-colors">
                検索
              </Link>
              <Link href="/messages" className="text-white/80 hover:text-white transition-colors">
                メッセージ
              </Link>
              <Link href="/matching" className="text-white/80 hover:text-white transition-colors">
                AIマッチング
              </Link>
              <Link href="/settings" className="text-white/80 hover:text-white transition-colors">
                設定
              </Link>
            </div>
            <AuthContent
              authenticated={
                <div className="flex items-center space-x-4">
                  <UserInfo />
                  <button 
                    onClick={handleLogout}
                    className="btn btn-outline border-white/30 text-white hover:bg-white hover:text-purple-900"
                  >
                    ログアウト
                  </button>
                </div>
              }
              unauthenticated={
                <Link href="/auth/signin">
                  <button className="btn btn-primary">
                    無料で始める
                  </button>
                </Link>
              }
            />
          </div>
        </div>
      </nav>

      {/* メインコンテンツ */}
      <main className="relative z-10 flex-1">
        {/* ヒーローセクション */}
        <section className="container mx-auto px-6 py-20 text-center">
          <div className={`transform transition-all duration-1000 ${isVisible ? 'translate-y-0 opacity-100' : 'translate-y-10 opacity-0'}`}>
            <div className="max-w-4xl mx-auto">
              {/* バッジ */}
              <div className="inline-flex items-center px-4 py-2 rounded-full bg-white/10 border border-white/20 text-white/90 text-sm font-medium mb-8 backdrop-blur-md">
                <span className="w-2 h-2 bg-green-400 rounded-full mr-2 animate-pulse"></span>
                AIエージェントが24/7稼働中
              </div>

              {/* メインタイトル */}
              <h1 className="text-5xl md:text-7xl font-bold text-white mb-8 leading-tight">
                YouTube
                <span className="text-gradient block">Influencer</span>
                <span className="text-white">Matching Agent</span>
              </h1>

              {/* サブタイトル */}
              <p className="text-xl md:text-2xl text-white/80 mb-12 max-w-3xl mx-auto text-balance">
                AIエージェントが最適なYouTubeインフルエンサーを見つけ、
                <br className="hidden md:block" />
                自動で交渉まで行う革新的なマッチングプラットフォーム
              </p>

              {/* CTA ボタン */}
              <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
                <Link href="/search">
                  <button className="btn btn-primary text-lg px-8 py-4 w-full sm:w-auto">
                    <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                    インフルエンサーを検索
                  </button>
                </Link>
                <button className="btn btn-secondary text-lg px-8 py-4 w-full sm:w-auto bg-white/10 border-white/30 text-white hover:bg-white/20">
                  <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h1m4 0h1m-6 4h8m-3-10v20" />
                  </svg>
                  デモを見る
                </button>
              </div>
            </div>
          </div>
        </section>

        {/* 特徴セクション */}
        <section className="container mx-auto px-6 py-20">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              AIエージェントの力
            </h2>
            <p className="text-xl text-white/70 max-w-2xl mx-auto">
              3つの専門AIエージェントが連携して、最適なマッチングと交渉を実現
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
            {/* 特徴1 */}
            <div className="card bg-white/10 border-white/20 backdrop-blur-md p-8 text-center group hover:scale-105 transition-all duration-300">
              <div className="w-16 h-16 bg-gradient-to-r from-purple-500 to-pink-500 rounded-2xl flex items-center justify-center mx-auto mb-6 group-hover:animate-glow">
                <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              </div>
              <h3 className="text-xl font-bold text-white mb-4">AIデータ分析</h3>
              <p className="text-white/70">
                YouTube APIとAIを活用し、登録者数、エンゲージメント率、コンテンツ品質を自動分析
              </p>
            </div>

            {/* 特徴2 */}
            <div className="card bg-white/10 border-white/20 backdrop-blur-md p-8 text-center group hover:scale-105 transition-all duration-300">
              <div className="w-16 h-16 bg-gradient-to-r from-cyan-500 to-blue-500 rounded-2xl flex items-center justify-center mx-auto mb-6 group-hover:animate-glow">
                <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                </svg>
              </div>
              <h3 className="text-xl font-bold text-white mb-4">スマートマッチング</h3>
              <p className="text-white/70">
                機械学習アルゴリズムが企業のニーズと最適なインフルエンサーを高精度でマッチング
              </p>
            </div>

            {/* 特徴3 */}
            <div className="card bg-white/10 border-white/20 backdrop-blur-md p-8 text-center group hover:scale-105 transition-all duration-300">
              <div className="w-16 h-16 bg-gradient-to-r from-green-500 to-emerald-500 rounded-2xl flex items-center justify-center mx-auto mb-6 group-hover:animate-glow">
                <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
              </div>
              <h3 className="text-xl font-bold text-white mb-4">自動交渉</h3>
              <p className="text-white/70">
                交渉エージェントが条件調整からコラボレーション提案まで全て自動で対応
              </p>
            </div>
          </div>
        </section>

        {/* 統計セクション */}
        <section className="container mx-auto px-6 py-20">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              実績と信頼
            </h2>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 max-w-4xl mx-auto">
            {[
              { number: '10,000+', label: 'インフルエンサー登録' },
              { number: '500+', label: 'マッチング成功' },
              { number: '95%', label: '満足度' },
              { number: '24/7', label: 'AI稼働時間' }
            ].map((stat, index) => (
              <div key={index} className="text-center">
                <div className="text-4xl md:text-5xl font-bold text-gradient mb-2">
                  {stat.number}
                </div>
                <div className="text-white/70 text-sm md:text-base">
                  {stat.label}
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* CTA セクション */}
        <section className="container mx-auto px-6 py-20">
          <div className="card bg-white/5 border-white/10 backdrop-blur-md p-12 text-center max-w-4xl mx-auto">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              今すぐ始めましょう
            </h2>
            <p className="text-xl text-white/70 mb-8 max-w-2xl mx-auto">
              無料でアカウントを作成し、AIエージェントの力を体験してください
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/search">
                <button className="btn btn-primary text-lg px-8 py-4">
                  無料で始める
                </button>
              </Link>
              <button className="btn btn-outline text-lg px-8 py-4 border-white/30 text-white hover:bg-white hover:text-purple-900">
                詳しく見る
              </button>
            </div>
          </div>
        </section>
      </main>

      {/* フッター */}
      <footer className="relative z-10 bg-black/20 backdrop-blur-md border-t border-white/10">
        <div className="container mx-auto px-6 py-8">
          <div className="text-center text-white/60">
            <p>&copy; 2025 InfuMatch. All rights reserved.</p>
            <p className="text-sm mt-2">Google Cloud Japan AI Hackathon Vol.2 参加作品</p>
          </div>
        </div>
      </footer>
    </div>
  );
}