import { NextRequest, NextResponse } from 'next/server';
import { GmailService } from '@/lib/gmail';
import { withAuth } from '@/lib/auth-middleware';

export const GET = withAuth(async (
  request: NextRequest,
  session: any,
  { params }: { params: { messageId: string; attachmentId: string } }
) => {
    const { messageId, attachmentId } = params;

    if (!messageId || !attachmentId) {
      return NextResponse.json(
        { error: 'Message ID and Attachment ID are required' },
        { status: 400 }
      );
    }

    const gmailService = new GmailService(session.accessToken, session.user?.email || 'default');
    const attachmentData = await gmailService.getAttachment(messageId, attachmentId);

    if (!attachmentData) {
      return NextResponse.json(
        { error: 'Attachment not found' },
        { status: 404 }
      );
    }

    return NextResponse.json({ 
      data: attachmentData,
      success: true 
    });
});