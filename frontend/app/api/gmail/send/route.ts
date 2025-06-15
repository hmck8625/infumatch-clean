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
    const { to, subject, body: messageBody, message: messageText, replyToMessageId, threadId } = body;
    
    // messageBodyまたはmessageTextのどちらかを使用
    const finalMessageBody = messageBody || messageText;

    if (!to || !subject || !finalMessageBody) {
      return NextResponse.json(
        { error: 'Missing required fields: to, subject, body' },
        { status: 400 }
      );
    }

    // 日本語対応：件名をRFC2047形式でエンコード
    const encodeSubject = (str: string): string => {
      // 日本語文字が含まれている場合のみエンコード
      if (/[^\x00-\x7F]/.test(str)) {
        const encoded = Buffer.from(str, 'utf8').toString('base64');
        return `=?UTF-8?B?${encoded}?=`;
      }
      return str;
    };

    // メールの作成（MIME形式）
    const messageParts = [
      `To: ${to}`,
      `Subject: ${encodeSubject(subject)}`,
      'MIME-Version: 1.0',
      'Content-Type: text/plain; charset=UTF-8',
      'Content-Transfer-Encoding: base64',
      ''
    ];

    // 返信の場合、追加ヘッダーを設定
    if (replyToMessageId) {
      messageParts.splice(-1, 0, `In-Reply-To: ${replyToMessageId}`);
      messageParts.splice(-1, 0, `References: ${replyToMessageId}`);
    }
    
    if (threadId) {
      messageParts.splice(-1, 0, `Thread-Topic: ${threadId}`);
    }

    // 本文をBase64エンコード
    const bodyBase64 = Buffer.from(finalMessageBody, 'utf8').toString('base64');
    
    // メッセージ全体を組み立て
    const messageContent = messageParts.join('\r\n') + bodyBase64;
    const encodedMessage = Buffer.from(messageContent, 'utf8').toString('base64')
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=+$/, '');

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