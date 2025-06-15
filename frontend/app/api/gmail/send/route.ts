import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/lib/auth';

export async function POST(request: NextRequest) {
  try {
    const session = await getServerSession(authOptions);
    
    if (!session?.accessToken) {
      return NextResponse.json(
        { error: 'Authentication required' },
        { status: 401 }
      );
    }

    const body = await request.json();
    const { to, subject, body: messageBody, message, replyToMessageId, threadId } = body;
    
    // messageBodyまたはmessageのどちらかを使用
    const finalMessageBody = messageBody || message;

    if (!to || !subject || !finalMessageBody) {
      return NextResponse.json(
        { error: 'Missing required fields: to, subject, body' },
        { status: 400 }
      );
    }

    // メールの作成
    const messageParts = [
      `To: ${to}`,
      `Subject: ${subject}`,
      'Content-Type: text/html; charset=utf-8',
      '',
      finalMessageBody
    ];

    // 返信の場合、追加ヘッダーを設定
    if (replyToMessageId) {
      messageParts.splice(3, 0, `In-Reply-To: ${replyToMessageId}`);
      messageParts.splice(4, 0, `References: ${replyToMessageId}`);
    }

    const message = messageParts.join('\r\n');
    const encodedMessage = Buffer.from(message).toString('base64').replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');

    console.log('Sending email to:', to, 'Subject:', subject);

    // Gmail Send APIエンドポイント
    const gmailUrl = 'https://gmail.googleapis.com/gmail/v1/users/me/messages/send';
    
    const response = await fetch(gmailUrl, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${session.accessToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        raw: encodedMessage
      })
    });

    if (!response.ok) {
      console.error('Gmail send API error:', response.status, response.statusText);
      const errorText = await response.text();
      console.error('Error details:', errorText);
      
      return NextResponse.json(
        { 
          error: 'Failed to send email',
          details: errorText,
          status: response.status 
        },
        { status: response.status }
      );
    }

    const data = await response.json();
    console.log('Email sent successfully:', data.id);

    return NextResponse.json({ 
      success: true, 
      messageId: data.id,
      message: 'Email sent successfully' 
    });
  } catch (error) {
    console.error('Gmail send API error:', error);
    return NextResponse.json(
      { error: 'Internal server error', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}