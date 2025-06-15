import { NextRequest, NextResponse } from 'next/server';
// import { GmailService } from '@/lib/gmail'; // Server-side only
// import { withAuth } from '@/lib/auth-middleware'; // Commented out for now

export async function GET(
  request: NextRequest,
  { params }: { params: { messageId: string; attachmentId: string } }
) {
    const { messageId, attachmentId } = params;

    if (!messageId || !attachmentId) {
      return NextResponse.json(
        { error: 'Message ID and Attachment ID are required' },
        { status: 400 }
      );
    }

    // TODO: Implement Gmail service integration
    // const gmailService = new GmailService(session.accessToken, session.user?.email || 'default');
    // const attachmentData = await gmailService.getAttachment(messageId, attachmentId);

    // Temporary mock response
    return NextResponse.json({
      error: 'Gmail service temporarily unavailable',
      messageId,
      attachmentId,
      success: false
    }, { status: 503 });
}