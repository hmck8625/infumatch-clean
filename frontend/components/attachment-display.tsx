'use client';

import { useState } from 'react';
// import { Attachment, GmailService } from '@/lib/gmail'; // Server-side only
// Temporary interface
interface Attachment { 
  id: string; 
  attachmentId: string;
  filename: string; 
  mimeType: string; 
  size: number; 
  data?: string; 
}
import { useAuthError } from '@/hooks/use-auth-error';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Download, FileText, Image, Video, Music, Archive, File } from 'lucide-react';

interface AttachmentDisplayProps {
  attachments: Attachment[];
  messageId: string;
}

export function AttachmentDisplay({ attachments, messageId }: AttachmentDisplayProps) {
  const [downloadingIds, setDownloadingIds] = useState<Set<string>>(new Set());
  const { handleApiResponse } = useAuthError();

  const downloadAttachment = async (attachment: Attachment) => {
    if (downloadingIds.has(attachment.attachmentId)) return;

    setDownloadingIds(prev => new Set(Array.from(prev).concat(attachment.attachmentId)));

    try {
      const response = await fetch(
        `/api/gmail/attachments/${messageId}/${attachment.attachmentId}`
      );

      const authErrorHandled = await handleApiResponse(response);
      if (authErrorHandled) {
        return;
      }

      if (response.ok) {
        const data = await response.json();
        
        // Base64データをBlobに変換してダウンロード
        const binaryData = atob(data.data.replace(/-/g, '+').replace(/_/g, '/'));
        const bytes = new Uint8Array(binaryData.length);
        for (let i = 0; i < binaryData.length; i++) {
          bytes[i] = binaryData.charCodeAt(i);
        }
        
        const blob = new Blob([bytes], { type: attachment.mimeType });
        const url = URL.createObjectURL(blob);
        
        // ダウンロード実行
        const a = document.createElement('a');
        a.href = url;
        a.download = attachment.filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      } else {
        console.error('添付ファイルダウンロードエラー:', response.statusText);
      }
    } catch (error) {
      console.error('添付ファイルダウンロードエラー:', error);
    } finally {
      setDownloadingIds(prev => {
        const newSet = new Set(prev);
        newSet.delete(attachment.attachmentId);
        return newSet;
      });
    }
  };

  const getFileIcon = (mimeType: string) => {
    if (mimeType.startsWith('image/')) return <Image className="w-4 h-4" />;
    if (mimeType.includes('pdf')) return <FileText className="w-4 h-4" />;
    if (mimeType.includes('word') || mimeType.includes('document')) return <FileText className="w-4 h-4" />;
    if (mimeType.includes('excel') || mimeType.includes('spreadsheet')) return <FileText className="w-4 h-4" />;
    if (mimeType.includes('powerpoint') || mimeType.includes('presentation')) return <FileText className="w-4 h-4" />;
    if (mimeType.includes('zip') || mimeType.includes('rar') || mimeType.includes('archive')) return <Archive className="w-4 h-4" />;
    if (mimeType.startsWith('audio/')) return <Music className="w-4 h-4" />;
    if (mimeType.startsWith('video/')) return <Video className="w-4 h-4" />;
    return <File className="w-4 h-4" />;
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (!attachments || attachments.length === 0) {
    return null;
  }

  return (
    <div className="mt-4 space-y-2">
      <h4 className="text-sm font-medium text-gray-700 mb-2">
        添付ファイル ({attachments.length}件)
      </h4>
      
      {attachments.map((attachment) => (
        <Card key={attachment.attachmentId} className="p-3">
          <CardContent className="p-0">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3 min-w-0 flex-1">
                <div className="flex-shrink-0 text-gray-500">
                  {getFileIcon(attachment.mimeType)}
                </div>
                
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {attachment.filename}
                  </p>
                  <p className="text-xs text-gray-500">
                    {formatFileSize(attachment.size)} • {attachment.mimeType}
                  </p>
                </div>
              </div>

              <Button
                variant="outline"
                size="sm"
                onClick={() => downloadAttachment(attachment)}
                disabled={downloadingIds.has(attachment.attachmentId)}
                className="flex-shrink-0 ml-2"
              >
                <Download className="w-3 h-3 mr-1" />
                {downloadingIds.has(attachment.attachmentId) ? 'ダウンロード中...' : 'ダウンロード'}
              </Button>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}