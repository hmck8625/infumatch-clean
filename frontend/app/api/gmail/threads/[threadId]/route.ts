import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/lib/auth';

export async function GET(
  request: NextRequest,
  { params }: { params: { threadId: string } }
) {
  try {
    const session = await getServerSession(authOptions);
    
    if (!session?.accessToken) {
      return NextResponse.json(
        { error: 'Authentication required' },
        { status: 401 }
      );
    }

    const { threadId } = params;

    // Gmail Thread Detail APIエンドポイント
    const gmailUrl = `https://gmail.googleapis.com/gmail/v1/users/me/threads/${threadId}`;
    const searchParams = new URLSearchParams({
      format: 'full'
    });

    console.log('Fetching Gmail thread details for:', threadId);

    const response = await fetch(`${gmailUrl}?${searchParams}`, {
      headers: {
        'Authorization': `Bearer ${session.accessToken}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      console.error('Gmail thread detail API error:', response.status, response.statusText);
      const errorText = await response.text();
      console.error('Error details:', errorText);
      
      return NextResponse.json(
        { 
          error: 'Failed to fetch thread details',
          details: errorText,
          status: response.status 
        },
        { status: response.status }
      );
    }

    const data = await response.json();
    console.log('Gmail thread details fetched successfully:', data.messages?.length || 0, 'messages');

    return NextResponse.json({ thread: data });
  } catch (error) {
    console.error('Gmail thread detail API error:', error);
    return NextResponse.json(
      { error: 'Internal server error', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}