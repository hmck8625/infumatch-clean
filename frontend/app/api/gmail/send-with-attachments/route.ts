import { NextRequest, NextResponse } from 'next/server';
import { GmailService } from '@/lib/gmail';
import { withAuth } from '@/lib/auth-middleware';

export const POST = withAuth(async (request: NextRequest, session: any) => {
  try {
    const formData = await request.formData();
    
    const to = formData.get('to') as string;
    const subject = formData.get('subject') as string;
    const message = formData.get('message') as string;
    const threadId = formData.get('threadId') as string | null;

    if (!to || !subject || !message) {
      return NextResponse.json(
        { error: 'Missing required fields: to, subject, message' },
        { status: 400 }
      );
    }

    // 添付ファイルを取得
    const attachments: File[] = [];
    const fileEntries = Array.from(formData.entries()).filter(([key]) => key.startsWith('attachment_'));
    
    for (const [, file] of fileEntries) {
      if (file instanceof File) {
        attachments.push(file);
      }
    }

    const gmailService = new GmailService(session.accessToken, session.user?.email || 'default');
    
    if (attachments.length > 0) {
      // 添付ファイル付きで送信
      await gmailService.sendWithAttachments(to, subject, message, attachments, threadId || undefined);
    } else {
      // 通常の送信
      if (threadId) {
        await gmailService.sendReply(threadId, to, subject, message);
      } else {
        await gmailService.sendNewMessage(to, subject, message);
      }
    }

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Gmail送信API エラー:', error);
    return NextResponse.json(
      { error: 'Failed to send email with attachments' },
      { status: 500 }
    );
  }
});