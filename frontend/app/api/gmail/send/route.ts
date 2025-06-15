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

    // From ヘッダー用の送信者情報を取得
    const session_info = await fetch('https://www.googleapis.com/oauth2/v2/userinfo', {
      headers: {
        'Authorization': `Bearer ${session.accessToken}`,
      },
    });
    
    let fromName = 'InfuMatch';
    if (session_info.ok) {
      const userInfo = await session_info.json();
      fromName = userInfo.name || 'InfuMatch';
    }

    // 日本語文字列をMIME encoded-wordでエンコード（RFC2047）
    const encodeMimeWord = (str: string): string => {
      if (!/[^\x00-\x7F]/.test(str)) {
        return str; // ASCII文字のみの場合はそのまま
      }
      const encoded = Buffer.from(str, 'utf8').toString('base64');
      return `=?UTF-8?B?${encoded}?=`;
    };

    // メールメッセージの構築（標準的なemail形式）
    const emailLines = [
      `From: ${encodeMimeWord(fromName)} <${session.user?.email || 'noreply@infumatch.com'}>`,
      `To: ${to}`,
      `Subject: ${encodeMimeWord(subject)}`,
      'MIME-Version: 1.0',
      'Content-Type: text/plain; charset=UTF-8',
      'Content-Transfer-Encoding: base64',
    ];

    // 返信の場合、スレッド用ヘッダーを追加
    if (replyToMessageId) {
      // Gmail のMessage-IDは実際のIDをそのまま使用
      emailLines.push(`In-Reply-To: <${replyToMessageId}>`);
      emailLines.push(`References: <${replyToMessageId}>`);
    }
    
    if (threadId) {
      // ThreadIdをGmail形式で設定
      emailLines.push(`Thread-Topic: ${threadId}`);
    }

    // 本文をBase64エンコード
    const bodyBase64 = Buffer.from(finalMessageBody, 'utf8').toString('base64');

    // 完全なメッセージを構築
    const fullMessage = emailLines.join('\r\n') + '\r\n\r\n' + bodyBase64;
    
    // Gmail APIのraw形式にエンコード
    const encodedMessage = Buffer.from(fullMessage, 'utf8')
      .toString('base64')
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