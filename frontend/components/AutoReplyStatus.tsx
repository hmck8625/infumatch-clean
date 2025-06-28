'use client';

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  Bot, 
  Clock, 
  Mail, 
  CheckCircle, 
  AlertCircle,
  ChevronDown,
  ChevronUp,
  Eye,
  EyeOff
} from 'lucide-react';

interface AutoReplyRecord {
  timestamp: string;
  replyContent: string;
  recipientEmail: string;
  subject: string;
  messageId: string;
  success: boolean;
}

interface AutoReplyStatusProps {
  autoReplyHistory: {[threadId: string]: AutoReplyRecord[]};
  currentThreadId?: string;
}

export default function AutoReplyStatus({ autoReplyHistory, currentThreadId }: AutoReplyStatusProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [showContent, setShowContent] = useState<{[key: string]: boolean}>({});

  // 現在のスレッドの自動返信履歴を取得
  const currentThreadHistory = currentThreadId ? autoReplyHistory[currentThreadId] || [] : [];
  
  // 全スレッドの自動返信履歴をまとめる（最新5件）
  const allHistory = Object.entries(autoReplyHistory)
    .flatMap(([threadId, records]) => 
      records.map(record => ({ ...record, threadId }))
    )
    .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
    .slice(0, 5);

  const toggleContent = (recordId: string) => {
    setShowContent(prev => ({
      ...prev,
      [recordId]: !prev[recordId]
    }));
  };

  const formatContent = (content: string) => {
    return content.length > 100 ? content.substring(0, 100) + '...' : content;
  };

  return (
    <Card className="w-full">
      <CardHeader 
        className="cursor-pointer hover:bg-gray-50 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Bot className="h-5 w-5 text-green-600" />
              自動返信ステータス
              {isExpanded ? (
                <ChevronUp className="h-4 w-4 ml-2" />
              ) : (
                <ChevronDown className="h-4 w-4 ml-2" />
              )}
            </CardTitle>
            <CardDescription>
              AI自動返信の実行履歴と内容を確認
            </CardDescription>
          </div>
          
          {allHistory.length > 0 && (
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-green-600 border-green-300">
                <CheckCircle className="h-3 w-3 mr-1" />
                {allHistory.length}件実行済み
              </Badge>
            </div>
          )}
        </div>
      </CardHeader>

      {isExpanded && (
        <CardContent className="space-y-4">
          {/* 現在のスレッドの履歴 */}
          {currentThreadId && currentThreadHistory.length > 0 && (
            <div className="space-y-3">
              <h4 className="text-sm font-medium flex items-center gap-2">
                <Mail className="h-4 w-4" />
                このスレッドの自動返信履歴
              </h4>
              
              {currentThreadHistory.map((record, index) => (
                <div key={`${currentThreadId}-${index}`} className="p-3 bg-green-50 rounded-lg border border-green-200">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <CheckCircle className="h-4 w-4 text-green-600" />
                      <span className="text-sm font-medium text-green-800">自動返信済み</span>
                      <Badge variant="outline" className="text-xs">
                        <Clock className="h-3 w-3 mr-1" />
                        {record.timestamp}
                      </Badge>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => toggleContent(`${currentThreadId}-${index}`)}
                      className="h-6 px-2 text-xs"
                    >
                      {showContent[`${currentThreadId}-${index}`] ? (
                        <>
                          <EyeOff className="h-3 w-3 mr-1" />
                          隠す
                        </>
                      ) : (
                        <>
                          <Eye className="h-3 w-3 mr-1" />
                          内容を表示
                        </>
                      )}
                    </Button>
                  </div>
                  
                  <div className="text-sm space-y-1">
                    <div>
                      <span className="text-gray-600">宛先:</span>
                      <span className="ml-2 text-gray-800">{record.recipientEmail}</span>
                    </div>
                    <div>
                      <span className="text-gray-600">件名:</span>
                      <span className="ml-2 text-gray-800">{record.subject}</span>
                    </div>
                    
                    {showContent[`${currentThreadId}-${index}`] ? (
                      <div className="mt-2 p-2 bg-white rounded border">
                        <div className="text-gray-600 text-xs mb-1">送信内容:</div>
                        <div className="text-sm whitespace-pre-wrap">{record.replyContent}</div>
                      </div>
                    ) : (
                      <div>
                        <span className="text-gray-600">内容:</span>
                        <span className="ml-2 text-gray-800">{formatContent(record.replyContent)}</span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* 全体の履歴 */}
          {allHistory.length > 0 && (
            <div className="space-y-3">
              <h4 className="text-sm font-medium flex items-center gap-2">
                <Clock className="h-4 w-4" />
                最近の自動返信履歴（最新5件）
              </h4>
              
              {allHistory.map((record, index) => (
                <div key={`all-${index}`} className="p-3 bg-blue-50 rounded-lg border border-blue-200">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <CheckCircle className="h-4 w-4 text-blue-600" />
                      <span className="text-sm font-medium text-blue-800">
                        スレッド {record.threadId.substring(0, 8)}...
                      </span>
                      <Badge variant="outline" className="text-xs">
                        <Clock className="h-3 w-3 mr-1" />
                        {record.timestamp}
                      </Badge>
                    </div>
                  </div>
                  
                  <div className="text-sm space-y-1">
                    <div>
                      <span className="text-gray-600">宛先:</span>
                      <span className="ml-2 text-gray-800">{record.recipientEmail}</span>
                    </div>
                    <div>
                      <span className="text-gray-600">件名:</span>
                      <span className="ml-2 text-gray-800">{record.subject}</span>
                    </div>
                    <div>
                      <span className="text-gray-600">内容:</span>
                      <span className="ml-2 text-gray-800">{formatContent(record.replyContent)}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* 履歴がない場合 */}
          {allHistory.length === 0 && (
            <div className="text-center py-6 text-gray-500">
              <Bot className="h-12 w-12 mx-auto mb-2 text-gray-300" />
              <p className="text-sm">まだ自動返信は実行されていません</p>
              <p className="text-xs mt-1">半自動モードで新着メールを受信すると自動返信が実行されます</p>
            </div>
          )}
        </CardContent>
      )}
    </Card>
  );
}