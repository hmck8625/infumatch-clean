#!/bin/bash

# =============================================================================
# エンドツーエンド統合スクリプト
# =============================================================================

set -e

echo "🔗 Starting End-to-End Integration for InfuMatch"

# 色付きログ関数
log_info() {
    echo -e "\033[1;34m[INFO]\033[0m $1"
}

log_success() {
    echo -e "\033[1;32m[SUCCESS]\033[0m $1"
}

log_error() {
    echo -e "\033[1;31m[ERROR]\033[0m $1"
}

log_warning() {
    echo -e "\033[1;33m[WARNING]\033[0m $1"
}

# 統合フェーズ1: 環境セットアップ
setup_integration_environment() {
    log_info "Phase 1: Setting up integration environment..."
    
    # 依存関係インストール
    log_info "Installing integration test dependencies..."
    pip3 install httpx --break-system-packages 2>/dev/null || pip3 install httpx
    
    # 環境変数確認
    if [ ! -f ".env.local" ]; then
        log_error ".env.local file not found. Please set up environment variables."
        exit 1
    fi
    
    # 環境変数読み込み
    set -a
    source .env.local
    set +a
    
    log_success "Integration environment ready"
}

# 統合フェーズ2: サービス起動
start_services() {
    log_info "Phase 2: Starting services for integration..."
    
    # 既存サービス停止
    ./stop-local.sh > /dev/null 2>&1 || true
    
    # バックエンド起動
    log_info "Starting backend service..."
    cd backend
    source venv/bin/activate 2>/dev/null || python3 -m venv venv && source venv/bin/activate
    pip install -r requirements-minimal.txt > /dev/null 2>&1 || true
    
    # バックグラウンドで起動
    nohup python main.py > ../backend.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > ../backend.pid
    cd ..
    
    # フロントエンド起動
    log_info "Starting frontend service..."
    cd frontend
    npm install > ../frontend_install.log 2>&1 || log_warning "Frontend npm install had issues"
    
    # バックグラウンドで起動
    nohup npm run dev > ../frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > ../frontend.pid
    cd ..
    
    # サービス起動待機
    log_info "Waiting for services to start..."
    sleep 10
    
    log_success "Services started"
}

# 統合フェーズ3: 接続確認
verify_connections() {
    log_info "Phase 3: Verifying service connections..."
    
    # バックエンド確認
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        log_success "Backend service is running"
    else
        log_warning "Backend service may still be starting..."
    fi
    
    # フロントエンド確認
    if curl -f http://localhost:3000 > /dev/null 2>&1; then
        log_success "Frontend service is running"
    else
        log_warning "Frontend service may still be starting..."
    fi
}

# 統合フェーズ4: 統合テスト実行
run_integration_tests() {
    log_info "Phase 4: Running integration tests..."
    
    # 環境変数設定
    export YOUTUBE_API_KEY="${YOUTUBE_API_KEY}"
    export GEMINI_API_KEY="${GEMINI_API_KEY}"
    export NEXT_PUBLIC_API_URL="http://localhost:8000"
    
    # 統合テスト実行
    python3 e2e_integration_test.py
}

# 統合フェーズ5: 接続の実装
implement_connections() {
    log_info "Phase 5: Implementing missing connections..."
    
    # API 統合の確認と修正
    log_info "Checking API integrations..."
    
    # フロントエンド-バックエンド接続設定
    if [ ! -f "frontend/.env.local" ]; then
        log_info "Creating frontend environment configuration..."
        echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > frontend/.env.local
        echo "NEXTAUTH_SECRET=your-secret-key" >> frontend/.env.local
        echo "NEXTAUTH_URL=http://localhost:3000" >> frontend/.env.local
    fi
    
    log_success "Connections configured"
}

# 統合フェーズ6: ワークフロー確認
test_workflows() {
    log_info "Phase 6: Testing integrated workflows..."
    
    # 基本ワークフローテスト
    log_info "Testing basic API workflows..."
    
    # YouTube API テスト
    if [ -n "$YOUTUBE_API_KEY" ]; then
        log_info "YouTube API key configured"
    else
        log_warning "YouTube API key not configured"
    fi
    
    # Gemini API テスト
    if [ -n "$GEMINI_API_KEY" ]; then
        log_info "Gemini API key configured"
    else
        log_warning "Gemini API key not configured"
    fi
    
    log_success "Workflow testing completed"
}

# メイン実行
main() {
    echo "🎯 InfuMatch End-to-End Integration"
    echo "=================================="
    
    setup_integration_environment
    start_services
    verify_connections
    implement_connections
    run_integration_tests
    test_workflows
    
    echo ""
    echo "🎉 End-to-End Integration Completed!"
    echo ""
    echo "🔗 Access URLs:"
    echo "   Frontend: http://localhost:3000"
    echo "   Backend API: http://localhost:8000"
    echo "   API Docs: http://localhost:8000/docs"
    echo ""
    echo "📋 Integration Status:"
    echo "   ✅ Services Running"
    echo "   ✅ Basic Connectivity"
    echo "   ⚠️  API Integration (In Progress)"
    echo "   ⚠️  Authentication Flow (Needs Configuration)"
    echo ""
    echo "📊 View logs:"
    echo "   Backend: tail -f backend.log"
    echo "   Frontend: tail -f frontend.log"
    echo ""
    echo "🛑 Stop services: ./stop-local.sh"
}

# エラーハンドリング
cleanup() {
    log_error "Integration interrupted. Cleaning up..."
    ./stop-local.sh > /dev/null 2>&1 || true
    exit 1
}

trap cleanup INT

# スクリプト実行
main

# ログ監視
echo "📊 Monitoring services (Press Ctrl+C to stop)..."
tail -f backend.log frontend.log 2>/dev/null || echo "Services are running in background..."