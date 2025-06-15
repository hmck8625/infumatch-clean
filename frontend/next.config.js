/**
 * Next.js 設定ファイル
 * 
 * @description YouTube Influencer Matching Agent のNext.js設定
 * @author InfuMatch Development Team
 * @version 1.0.0
 */

/** @type {import('next').NextConfig} */
const nextConfig = {
  // 実験的機能の有効化
  experimental: {
    // Server Components の最適化
    serverComponentsExternalPackages: ['@google-cloud/firestore'],
    // 部分的な事前レンダリング（PPR）を有効化
    ppr: false,
  },

  // TypeScript 設定
  typescript: {
    // 本番ビルド時にTypeScriptエラーがあっても続行するか
    // 開発時は false にして厳密にチェック
    ignoreBuildErrors: false,
  },

  // ESLint 設定
  eslint: {
    // ビルド時にESLintエラーがあっても続行するか
    ignoreDuringBuilds: false,
  },

  // 画像最適化設定
  images: {
    // 外部画像ホストの許可
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'yt3.ggpht.com', // YouTube アバター
        port: '',
        pathname: '/**',
      },
      {
        protocol: 'https',
        hostname: 'i.ytimg.com', // YouTube サムネイル
        port: '',
        pathname: '/**',
      },
      {
        protocol: 'https',
        hostname: 'storage.googleapis.com', // Cloud Storage
        port: '',
        pathname: '/**',
      },
    ],
    // 画像サイズの最適化
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
  },

  // 環境変数の設定
  env: {
    // ビルド時に注入される環境変数
    NEXT_PUBLIC_APP_NAME: 'YouTube Influencer Matching Agent',
    NEXT_PUBLIC_APP_VERSION: process.env.npm_package_version || '0.1.0',
  },

  // パフォーマンス最適化
  poweredByHeader: false, // X-Powered-By ヘッダーを削除
  
  // セキュリティヘッダー
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          },
          {
            key: 'Permissions-Policy',
            value: 'camera=(), microphone=(), geolocation=()',
          },
        ],
      },
    ];
  },

  // リダイレクト設定
  async redirects() {
    return [
      // 古いURL形式から新しい形式へのリダイレクト
      {
        source: '/dashboard/influencers',
        destination: '/dashboard/discover',
        permanent: true,
      },
    ];
  },

  // リライト設定（プロキシ）
  async rewrites() {
    const rewrites = [];
    
    // API URL が設定されている場合のみプロキシを追加
    if (process.env.NEXT_PUBLIC_API_URL) {
      rewrites.push({
        source: '/api/v1/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL}/api/v1/:path*`,
      });
    }
    
    return rewrites;
  },

  // Webpack 設定のカスタマイズ
  webpack: (config, { buildId, dev, isServer, defaultLoaders, webpack }) => {
    // Node.js モジュールのブラウザ対応
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        net: false,
        tls: false,
        fs: false,
        child_process: false,
        dns: false,
        http2: false,
        crypto: false,
        stream: false,
        buffer: false,
        util: false,
        url: false,
        querystring: false,
        os: false,
        path: false,
        zlib: false,
      };
    }

    // SVG を React コンポーネントとして読み込み
    config.module.rules.push({
      test: /\.svg$/,
      use: ['@svgr/webpack'],
    });

    // Bundle Analyzer の設定（開発時のみ）
    if (process.env.ANALYZE === 'true') {
      const { BundleAnalyzerPlugin } = require('webpack-bundle-analyzer');
      config.plugins.push(
        new BundleAnalyzerPlugin({
          analyzerMode: 'static',
          openAnalyzer: false,
        })
      );
    }

    return config;
  },

  // 出力設定
  output: 'standalone', // Docker コンテナでの実行に最適化

  // 圧縮設定
  compress: true,

  // トレイリングスラッシュの処理
  trailingSlash: false,

  // ページ拡張子
  pageExtensions: ['ts', 'tsx', 'js', 'jsx', 'md', 'mdx'],

  // 国際化設定（将来的な多言語対応）
  i18n: {
    locales: ['ja', 'en'],
    defaultLocale: 'ja',
    localeDetection: false, // 自動検出を無効化
  },
};

module.exports = nextConfig;