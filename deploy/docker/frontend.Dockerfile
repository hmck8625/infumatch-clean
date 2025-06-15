# =============================================================================
# Next.js フロントエンド用 Dockerfile
# =============================================================================
# Vercel またはCloud Run デプロイ用

# ベースイメージ
FROM node:18-alpine AS base

# メタデータ
LABEL maintainer="InfuMatch Development Team"
LABEL description="InfuMatch Frontend"
LABEL version="1.0.0"

# 依存関係のインストール
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

# package.json と package-lock.json をコピー
COPY frontend/package*.json ./
RUN npm ci --only=production

# ビルダーステージ
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY frontend/ .

# Next.js の環境変数設定
ENV NEXT_TELEMETRY_DISABLED 1

# アプリケーションのビルド
RUN npm run build

# プロダクションイメージ
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

# 非root ユーザーの作成
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# 必要なファイルをコピー
COPY --from=builder /app/public ./public

# Set the correct permission for prerender cache
RUN mkdir .next
RUN chown nextjs:nodejs .next

# Automatically leverage output traces to reduce image size
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

# サーバー起動
CMD ["node", "server.js"]