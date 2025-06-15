'use client';

import { useState, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { X, Paperclip, File } from 'lucide-react';

interface AttachmentUploadProps {
  onFilesChange: (files: File[]) => void;
  maxFiles?: number;
  maxFileSize?: number; // MB
  acceptedTypes?: string[];
}

export function AttachmentUpload({ 
  onFilesChange, 
  maxFiles = 5, 
  maxFileSize = 25,
  acceptedTypes = ['*/*']
}: AttachmentUploadProps) {
  const [files, setFiles] = useState<File[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (selectedFiles: FileList | null) => {
    if (!selectedFiles) return;

    const newFiles = Array.from(selectedFiles);
    const validFiles: File[] = [];
    const errors: string[] = [];

    for (const file of newFiles) {
      // ファイルサイズチェック
      if (file.size > maxFileSize * 1024 * 1024) {
        errors.push(`${file.name}: ファイルサイズが${maxFileSize}MBを超えています`);
        continue;
      }

      // ファイル数制限チェック
      if (files.length + validFiles.length >= maxFiles) {
        errors.push(`ファイル数は最大${maxFiles}件までです`);
        break;
      }

      validFiles.push(file);
    }

    if (errors.length > 0) {
      alert(errors.join('\n'));
    }

    const updatedFiles = [...files, ...validFiles];
    setFiles(updatedFiles);
    onFilesChange(updatedFiles);
  };

  const removeFile = (index: number) => {
    const updatedFiles = files.filter((_, i) => i !== index);
    setFiles(updatedFiles);
    onFilesChange(updatedFiles);
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="space-y-3">
      {/* ファイル選択ボタン */}
      <div>
        <Button
          type="button"
          variant="outline"
          onClick={() => fileInputRef.current?.click()}
          disabled={files.length >= maxFiles}
          className="w-full"
        >
          <Paperclip className="w-4 h-4 mr-2" />
          ファイルを添付 ({files.length}/{maxFiles})
        </Button>
        
        <input
          ref={fileInputRef}
          type="file"
          multiple
          className="hidden"
          accept={acceptedTypes.join(',')}
          onChange={(e) => handleFileSelect(e.target.files)}
        />
        
        <p className="text-xs text-gray-500 mt-1">
          最大{maxFiles}件、1ファイル{maxFileSize}MBまで
        </p>
      </div>

      {/* 選択されたファイル一覧 */}
      {files.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-700">
            添付ファイル
          </h4>
          
          {files.map((file, index) => (
            <Card key={`${file.name}-${index}`} className="p-2">
              <CardContent className="p-0">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2 min-w-0 flex-1">
                    <File className="w-4 h-4 text-gray-500 flex-shrink-0" />
                    
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {file.name}
                      </p>
                      <p className="text-xs text-gray-500">
                        {formatFileSize(file.size)}
                      </p>
                    </div>
                  </div>

                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => removeFile(index)}
                    className="flex-shrink-0 ml-2 h-6 w-6 p-0"
                  >
                    <X className="w-3 h-3" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}