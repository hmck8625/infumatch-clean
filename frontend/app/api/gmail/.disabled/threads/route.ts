import { NextRequest, NextResponse } from 'next/server';
import { GmailService } from '@/lib/gmail';
import { withAuth } from '@/lib/auth-middleware';

export const GET = withAuth(async (request: NextRequest, session: any) => {
  try {
    console.log('📧 Gmail threads API called');
    console.log('Session available:', !!session);
    console.log('Access token available:', !!session?.accessToken);
    
    const { searchParams } = new URL(request.url);
    const influencerEmail = searchParams.get('email');
    
    console.log('Influencer email filter:', influencerEmail);

    const gmailService = new GmailService(session.accessToken, session.user?.email || 'default');
    console.log('Gmail service created');
    
    const threads = await gmailService.getInfluencerThreads(influencerEmail || undefined);
    console.log('Threads fetched successfully:', threads?.length || 0);

    return NextResponse.json({ threads });
  } catch (error: any) {
    console.error('❌ Gmail threads API error:', {
      message: error?.message,
      stack: error?.stack,
      name: error?.name,
      response: error?.response?.data,
      status: error?.response?.status
    });
    
    return NextResponse.json(
      { 
        error: 'Failed to fetch Gmail threads',
        details: error?.message || 'Unknown error'
      },
      { status: 500 }
    );
  }
});