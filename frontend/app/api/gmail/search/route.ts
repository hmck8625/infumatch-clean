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

    const { searchParams } = new URL(request.url);
    const query = searchParams.get('q') || 'in:inbox';
    const maxResults = searchParams.get('maxResults') || '50';

    // Gmail Messages APIエンドポイント
    const gmailUrl = 'https://gmail.googleapis.com/gmail/v1/users/me/messages';
    const params = new URLSearchParams({
      maxResults,
      q: query
    });

    console.log('Searching Gmail messages with query:', query);

    const response = await fetch(`${gmailUrl}?${params}`, {
      headers: {
        'Authorization': `Bearer ${session.accessToken}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      console.error('Gmail search API error:', response.status, response.statusText);
      const errorText = await response.text();
      console.error('Error details:', errorText);
      
      return NextResponse.json(
        { 
          error: 'Failed to search messages',
          details: errorText,
          status: response.status 
        },
        { status: response.status }
      );
    }

    const data = await response.json();
    console.log('Gmail search completed:', data.messages?.length || 0, 'messages found');

    return NextResponse.json(data);
  } catch (error) {
    console.error('Gmail search API error:', error);
    return NextResponse.json(
      { error: 'Internal server error', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}