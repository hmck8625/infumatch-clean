import { NextRequest, NextResponse } from 'next/server';
import { GmailService } from '@/lib/gmail';
import { withAuth } from '@/lib/auth-middleware';

export const GET = withAuth(async (request: NextRequest, session: any) => {
  try {
    console.log('🏷️ Gmail labels API called');

    const gmailService = new GmailService(session.accessToken, session.user?.email || 'default');
    const labels = await gmailService.getLabels();

    return NextResponse.json({
      success: true,
      labels
    });
  } catch (error: any) {
    console.error('❌ Gmail labels API error:', {
      message: error?.message,
      stack: error?.stack,
      response: error?.response?.data,
      status: error?.response?.status
    });
    
    return NextResponse.json(
      { 
        error: 'Failed to fetch Gmail labels',
        details: error?.message || 'Unknown error'
      },
      { status: 500 }
    );
  }
});