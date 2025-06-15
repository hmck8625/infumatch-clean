import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/lib/auth';

export async function GET(request: NextRequest) {
  try {
    const session = await getServerSession(authOptions);
    
    if (!session?.accessToken) {
      return NextResponse.json(
        { error: 'Authentication required' },
        { status: 401 }
      );
    }

    // Gmail Threads APIエンドポイント
    const gmailUrl = 'https://gmail.googleapis.com/gmail/v1/users/me/threads';
    const params = new URLSearchParams({
      maxResults: '50',
      q: 'in:inbox'
    });

    console.log('Fetching Gmail threads with access token:', session.accessToken ? 'Present' : 'Missing');

    const response = await fetch(`${gmailUrl}?${params}`, {
      headers: {
        'Authorization': `Bearer ${session.accessToken}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      console.error('Gmail API error:', response.status, response.statusText);
      const errorText = await response.text();
      console.error('Error details:', errorText);
      
      return NextResponse.json(
        { 
          error: 'Failed to fetch threads',
          details: errorText,
          status: response.status 
        },
        { status: response.status }
      );
    }

    const data = await response.json();
    console.log('Gmail threads fetched successfully:', data.threads?.length || 0, 'threads');

    return NextResponse.json(data);
  } catch (error) {
    console.error('Gmail threads API error:', error);
    return NextResponse.json(
      { error: 'Internal server error', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}