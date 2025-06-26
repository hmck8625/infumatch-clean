import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/lib/auth';
import { GmailService } from '@/lib/gmail';

export async function POST(request: NextRequest) {
  try {
    const session = await getServerSession(authOptions);
    
    if (!session?.accessToken) {
      return NextResponse.json(
        { error: 'Authentication required' },
        { status: 401 }
      );
    }

    const formData = await request.formData();
    
    // フォームデータから各フィールドを取得
    const to = formData.get('to') as string;
    const subject = formData.get('subject') as string;
    const message = formData.get('message') as string;
    const threadId = formData.get('threadId') as string;
    const replyToMessageId = formData.get('replyToMessageId') as string;
    const replyHeadersString = formData.get('replyHeaders') as string;
    
    let replyHeaders = null;
    if (replyHeadersString) {
      try {
        replyHeaders = JSON.parse(replyHeadersString);
      } catch (error) {
        console.warn('Failed to parse replyHeaders:', error);
      }
    }

    console.log('📧 Send with attachments - received data:', {
      to,
      subject,
      messageLength: message?.length,
      threadId,
      replyToMessageId,
      hasReplyHeaders: !!replyHeaders
    });

    if (!to || !subject || !message) {
      return NextResponse.json(
        { error: 'Missing required fields: to, subject, message' },
        { status: 400 }
      );
    }

    // 添付ファイルを取得
    const attachmentFiles: File[] = [];
    let attachmentIndex = 0;
    
    while (true) {
      const file = formData.get(`attachment_${attachmentIndex}`) as File;
      if (!file) break;
      attachmentFiles.push(file);
      attachmentIndex++;
    }

    console.log(`📧 Found ${attachmentFiles.length} attachment files`);

    // Gmail Serviceを使用して添付ファイル付きメールを送信
    const gmailService = new GmailService(session.accessToken, session.user?.email || 'default');
    
    await gmailService.sendWithAttachments(
      to,
      subject,
      message,
      attachmentFiles,
      threadId,
      replyToMessageId
    );

    console.log('✅ Email with attachments sent successfully');

    return NextResponse.json({ 
      success: true,
      message: 'Email with attachments sent successfully',
      attachmentCount: attachmentFiles.length,
      threadId
    });

  } catch (error: any) {
    console.error('Send with attachments API error:', error);
    
    // トークンエラーをクライアントに伝える
    if (error.message === 'TOKEN_EXPIRED') {
      return NextResponse.json(
        { error: 'TOKEN_EXPIRED', message: 'Authentication token has expired' },
        { status: 401 }
      );
    }
    
    return NextResponse.json(
      { 
        error: 'Failed to send email with attachments', 
        details: error.message || 'Unknown error'
      },
      { status: 500 }
    );
  }
}