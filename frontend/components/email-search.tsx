'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { SearchFilters } from '@/lib/gmail';
import { useAuthError } from '@/hooks/use-auth-error';
import { Search, Filter, X, Calendar, Paperclip, Mail, Star, Sparkles, ChevronDown, ChevronUp, SlidersHorizontal } from 'lucide-react';

interface EmailSearchProps {
  onSearch: (filters: SearchFilters) => void;
  onClear: () => void;
  isLoading?: boolean;
}

export function EmailSearch({ onSearch, onClear, isLoading = false }: EmailSearchProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [filters, setFilters] = useState<SearchFilters>({});
  const [labels, setLabels] = useState<any[]>([]);
  const { handleApiResponse } = useAuthError();

  useEffect(() => {
    loadLabels();
  }, []);

  const loadLabels = async () => {
    try {
      const response = await fetch('/api/gmail/labels');
      const authErrorHandled = await handleApiResponse(response);
      if (authErrorHandled) return;

      if (response.ok) {
        const data = await response.json();
        setLabels(data.labels || []);
      }
    } catch (error) {
      console.error('ラベル取得エラー:', error);
    }
  };

  const handleSearch = () => {
    onSearch(filters);
  };

  const handleClear = () => {
    setFilters({});
    onClear();
  };

  const updateFilter = (key: keyof SearchFilters, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const removeFilter = (key: keyof SearchFilters) => {
    const newFilters = { ...filters };
    delete newFilters[key];
    setFilters(newFilters);
  };

  const hasActiveFilters = Object.keys(filters).length > 0;

  return (
    <div className="w-full space-y-4">
      {/* メインヘッダー */}
      <div className="bg-gradient-to-r from-blue-50 via-indigo-50 to-purple-50 rounded-2xl p-6 border border-blue-100/50">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg">
              <Search className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                📧 メール検索
                <Sparkles className="w-5 h-5 text-indigo-500" />
              </h2>
              <p className="text-sm text-gray-600">高度な検索機能でメールを素早く見つけましょう</p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            {hasActiveFilters && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleClear}
                className="bg-red-50 border-red-200 text-red-700 hover:bg-red-100 hover:border-red-300 transition-all duration-200"
              >
                <X className="w-4 h-4 mr-1" />
                クリア
              </Button>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsExpanded(!isExpanded)}
              className="bg-white/80 border-indigo-200 text-indigo-700 hover:bg-indigo-50 hover:border-indigo-300 transition-all duration-200"
            >
              <SlidersHorizontal className="w-4 h-4 mr-1" />
              {isExpanded ? (
                <>
                  <ChevronUp className="w-4 h-4 ml-1" />
                  詳細を閉じる
                </>
              ) : (
                <>
                  <ChevronDown className="w-4 h-4 ml-1" />
                  詳細フィルタ
                </>
              )}
            </Button>
          </div>
        </div>

        {/* 基本検索 */}
        <div className="flex gap-3">
          <div className="flex-1">
            <Input
              type="text"
              placeholder="🔍 キーワード、送信者、件名で検索..."
              value={filters.query || ''}
              onChange={(e) => updateFilter('query', e.target.value)}
              className="h-12 text-base bg-white/80 border-indigo-200 focus:border-indigo-400 focus:ring-indigo-200 rounded-xl shadow-sm"
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            />
          </div>
          <Button
            onClick={handleSearch}
            disabled={isLoading}
            className="h-12 px-8 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white font-medium rounded-xl shadow-lg hover:shadow-xl transition-all duration-200"
          >
            {isLoading ? (
              <div className="animate-spin w-5 h-5 border-2 border-white border-t-transparent rounded-full" />
            ) : (
              <>
                <Search className="w-5 h-5 mr-2" />
                検索実行
              </>
            )}
          </Button>
        </div>

        {/* アクティブフィルター表示 */}
        {hasActiveFilters && (
          <div className="bg-white/60 rounded-xl p-4 border border-indigo-100">
            <div className="flex items-center gap-2 mb-2">
              <Filter className="w-4 h-4 text-indigo-600" />
              <span className="text-sm font-medium text-indigo-900">適用中のフィルター</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {filters.from && (
                <Badge 
                  variant="secondary" 
                  className="bg-gradient-to-r from-blue-100 to-blue-200 text-blue-800 border-blue-300 hover:from-blue-200 hover:to-blue-300 transition-all duration-200"
                >
                  📩 From: {filters.from}
                  <button onClick={() => removeFilter('from')} className="ml-1 hover:text-blue-900">
                    <X className="w-3 h-3" />
                  </button>
                </Badge>
              )}
              {filters.to && (
                <Badge 
                  variant="secondary" 
                  className="bg-gradient-to-r from-green-100 to-green-200 text-green-800 border-green-300 hover:from-green-200 hover:to-green-300 transition-all duration-200"
                >
                  📤 To: {filters.to}
                  <button onClick={() => removeFilter('to')} className="ml-1 hover:text-green-900">
                    <X className="w-3 h-3" />
                  </button>
                </Badge>
              )}
              {filters.subject && (
                <Badge 
                  variant="secondary" 
                  className="bg-gradient-to-r from-purple-100 to-purple-200 text-purple-800 border-purple-300 hover:from-purple-200 hover:to-purple-300 transition-all duration-200"
                >
                  📝 Subject: {filters.subject}
                  <button onClick={() => removeFilter('subject')} className="ml-1 hover:text-purple-900">
                    <X className="w-3 h-3" />
                  </button>
                </Badge>
              )}
              {filters.hasAttachment && (
                <Badge 
                  variant="secondary" 
                  className="bg-gradient-to-r from-orange-100 to-orange-200 text-orange-800 border-orange-300 hover:from-orange-200 hover:to-orange-300 transition-all duration-200"
                >
                  <Paperclip className="w-3 h-3 mr-1" />
                  添付ファイルあり
                  <button onClick={() => removeFilter('hasAttachment')} className="ml-1 hover:text-orange-900">
                    <X className="w-3 h-3" />
                  </button>
                </Badge>
              )}
              {filters.isUnread && (
                <Badge 
                  variant="secondary" 
                  className="bg-gradient-to-r from-yellow-100 to-yellow-200 text-yellow-800 border-yellow-300 hover:from-yellow-200 hover:to-yellow-300 transition-all duration-200"
                >
                  <Mail className="w-3 h-3 mr-1" />
                  未読のみ
                  <button onClick={() => removeFilter('isUnread')} className="ml-1 hover:text-yellow-900">
                    <X className="w-3 h-3" />
                  </button>
                </Badge>
              )}
              {filters.isImportant && (
                <Badge 
                  variant="secondary" 
                  className="bg-gradient-to-r from-red-100 to-red-200 text-red-800 border-red-300 hover:from-red-200 hover:to-red-300 transition-all duration-200"
                >
                  <Star className="w-3 h-3 mr-1" />
                  重要メール
                  <button onClick={() => removeFilter('isImportant')} className="ml-1 hover:text-red-900">
                    <X className="w-3 h-3" />
                  </button>
                </Badge>
              )}
            </div>
          </div>
        )}

      </div>
      
      {/* 詳細フィルター */}
      {isExpanded && (
        <div className="bg-white rounded-2xl p-6 border border-gray-200 shadow-sm">
          <div className="mb-4">
            <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              <SlidersHorizontal className="w-5 h-5 text-indigo-500" />
              詳細フィルター設定
            </h3>
            <p className="text-sm text-gray-600 mt-1">より細かい条件でメールを絞り込みます</p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* 送信者フィルター */}
            <div className="space-y-2">
              <label className="block text-sm font-semibold text-gray-700 flex items-center gap-2">
                📩 送信者
              </label>
              <Input
                type="email"
                placeholder="sender@example.com"
                value={filters.from || ''}
                onChange={(e) => updateFilter('from', e.target.value)}
                className="bg-gray-50 border-gray-200 focus:border-indigo-400 focus:ring-indigo-200 rounded-lg"
              />
            </div>

            {/* 宛先フィルター */}
            <div className="space-y-2">
              <label className="block text-sm font-semibold text-gray-700 flex items-center gap-2">
                📤 宛先
              </label>
              <Input
                type="email"
                placeholder="recipient@example.com"
                value={filters.to || ''}
                onChange={(e) => updateFilter('to', e.target.value)}
                className="bg-gray-50 border-gray-200 focus:border-indigo-400 focus:ring-indigo-200 rounded-lg"
              />
            </div>

            {/* 件名フィルター */}
            <div className="space-y-2">
              <label className="block text-sm font-semibold text-gray-700 flex items-center gap-2">
                📝 件名
              </label>
              <Input
                type="text"
                placeholder="件名のキーワード"
                value={filters.subject || ''}
                onChange={(e) => updateFilter('subject', e.target.value)}
                className="bg-gray-50 border-gray-200 focus:border-indigo-400 focus:ring-indigo-200 rounded-lg"
              />
            </div>

            {/* 日付フィルター */}
            <div className="space-y-2">
              <label className="block text-sm font-semibold text-gray-700 flex items-center gap-2">
                📅 開始日
              </label>
              <Input
                type="date"
                value={filters.dateAfter ? filters.dateAfter.toISOString().split('T')[0] : ''}
                onChange={(e) => updateFilter('dateAfter', e.target.value ? new Date(e.target.value) : undefined)}
                className="bg-gray-50 border-gray-200 focus:border-indigo-400 focus:ring-indigo-200 rounded-lg"
              />
            </div>

            <div className="space-y-2">
              <label className="block text-sm font-semibold text-gray-700 flex items-center gap-2">
                📅 終了日
              </label>
              <Input
                type="date"
                value={filters.dateBefore ? filters.dateBefore.toISOString().split('T')[0] : ''}
                onChange={(e) => updateFilter('dateBefore', e.target.value ? new Date(e.target.value) : undefined)}
                className="bg-gray-50 border-gray-200 focus:border-indigo-400 focus:ring-indigo-200 rounded-lg"
              />
            </div>

            {/* 表示件数 */}
            <div className="space-y-2">
              <label className="block text-sm font-semibold text-gray-700 flex items-center gap-2">
                🔢 表示件数
              </label>
              <select
                value={filters.maxResults || 20}
                onChange={(e) => updateFilter('maxResults', parseInt(e.target.value))}
                className="w-full px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400 text-sm"
              >
                <option value={10}>10件表示</option>
                <option value={20}>20件表示</option>
                <option value={50}>50件表示</option>
                <option value={100}>100件表示</option>
              </select>
            </div>
          </div>

          {/* 条件チェックボックス */}
          <div className="mt-6 pt-4 border-t border-gray-200">
            <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
              ✨ 特別条件
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <label className="flex items-center space-x-3 p-3 bg-gradient-to-r from-orange-50 to-orange-100 rounded-xl border border-orange-200 cursor-pointer hover:from-orange-100 hover:to-orange-150 transition-all duration-200">
                <input
                  type="checkbox"
                  checked={filters.hasAttachment || false}
                  onChange={(e) => updateFilter('hasAttachment', e.target.checked || undefined)}
                  className="rounded border-orange-300 text-orange-600 focus:ring-orange-500"
                />
                <div className="flex items-center space-x-2">
                  <Paperclip className="w-4 h-4 text-orange-600" />
                  <span className="text-sm font-medium text-orange-800">添付ファイルあり</span>
                </div>
              </label>
              
              <label className="flex items-center space-x-3 p-3 bg-gradient-to-r from-yellow-50 to-yellow-100 rounded-xl border border-yellow-200 cursor-pointer hover:from-yellow-100 hover:to-yellow-150 transition-all duration-200">
                <input
                  type="checkbox"
                  checked={filters.isUnread || false}
                  onChange={(e) => updateFilter('isUnread', e.target.checked || undefined)}
                  className="rounded border-yellow-300 text-yellow-600 focus:ring-yellow-500"
                />
                <div className="flex items-center space-x-2">
                  <Mail className="w-4 h-4 text-yellow-600" />
                  <span className="text-sm font-medium text-yellow-800">未読のみ</span>
                </div>
              </label>
              
              <label className="flex items-center space-x-3 p-3 bg-gradient-to-r from-red-50 to-red-100 rounded-xl border border-red-200 cursor-pointer hover:from-red-100 hover:to-red-150 transition-all duration-200">
                <input
                  type="checkbox"
                  checked={filters.isImportant || false}
                  onChange={(e) => updateFilter('isImportant', e.target.checked || undefined)}
                  className="rounded border-red-300 text-red-600 focus:ring-red-500"
                />
                <div className="flex items-center space-x-2">
                  <Star className="w-4 h-4 text-red-600" />
                  <span className="text-sm font-medium text-red-800">重要メール</span>
                </div>
              </label>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}