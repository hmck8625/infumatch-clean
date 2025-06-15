import { NextRequest, NextResponse } from 'next/server';
import { GmailService } from '@/lib/gmail';
import { withAuth } from '@/lib/auth-middleware';

export const POST = withAuth(async (request: NextRequest, session: any) => {
  const body = await request.json();
  const { to, subject, message, threadId } = body;

  if (!to || !subject || !message) {
    return NextResponse.json(
      { error: 'Missing required fields: to, subject, message' },
      { status: 400 }
    );
  }

  const gmailService = new GmailService(session.accessToken, session.user?.email || 'default');
  
  if (threadId) {
    // 返信として送信
    await gmailService.sendReply(threadId, to, subject, message);
  } else {
    // 新規メールとして送信
    await gmailService.sendNewMessage(to, subject, message);
  }

  return NextResponse.json({ success: true });
});