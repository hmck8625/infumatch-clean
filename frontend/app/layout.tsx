import type { Metadata, Viewport } from 'next';
import { Inter, Noto_Sans_JP } from 'next/font/google';
import './globals.css';
import { AuthProvider } from '@/components/auth-provider';

const inter = Inter({ 
  subsets: ['latin'],
  variable: '--font-sans',
  display: 'swap',
});

const notoSansJP = Noto_Sans_JP({ 
  subsets: ['latin'],
  variable: '--font-heading',
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'InfuMatch - AI YouTube Influencer Matching Platform',
  description: 'AIエージェントが最適なYouTubeインフルエンサーを見つけて、自動で交渉まで行う革新的なマッチングプラットフォーム。Google Cloud Japan AI Hackathon Vol.2 参加作品。',
  keywords: ['YouTube', 'インフルエンサー', 'マッチング', 'AI', 'エージェント', 'Google Cloud'],
  authors: [{ name: 'InfuMatch Team' }],
  openGraph: {
    title: 'InfuMatch - AI YouTube Influencer Matching Platform',
    description: 'AIエージェントが最適なYouTubeインフルエンサーを見つけて、自動で交渉まで行う革新的なマッチングプラットフォーム',
    type: 'website',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ja" className={`${inter.variable} ${notoSansJP.variable}`}>
      <body className={`${inter.className} antialiased bg-gray-50`}>
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}