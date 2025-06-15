'use client';

import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    // Chrome拡張機能のエラーは無視
    if (error.stack?.includes('chrome-extension://')) {
      console.warn('Chrome extension error caught by ErrorBoundary and ignored:', error);
      return { hasError: false };
    }
    
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Chrome拡張機能のエラーは無視
    if (error.stack?.includes('chrome-extension://')) {
      return;
    }
    
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center">
          <div className="card p-8 text-center max-w-md mx-auto">
            <div className="text-red-500 mb-4">
              <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.728-.833-2.498 0L4.316 15.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-gray-900 mb-4">
              エラーが発生しました
            </h1>
            <p className="text-gray-600 mb-6">
              アプリケーションでエラーが発生しました。ページを再読み込みしてみてください。
            </p>
            <button 
              onClick={() => window.location.reload()}
              className="btn btn-primary"
            >
              ページを再読み込み
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// Hook版のエラーハンドリング
export function useErrorHandler() {
  return (error: unknown) => {
    // Chrome拡張機能のエラーは無視
    if (error instanceof Error && error.stack?.includes('chrome-extension://')) {
      console.warn('Chrome extension error ignored:', error);
      return;
    }
    
    console.error('Application error:', error);
    // 必要に応じて他のエラーレポーティングサービスに送信
  };
}