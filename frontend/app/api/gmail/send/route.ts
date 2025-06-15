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
    
    // 🔍 DEBUG: リクエストボディの詳細をログ出力
    console.log('=== EMAIL SEND DEBUG START ===');
    console.log('📧 Request body received:', JSON.stringify(body, null, 2));
    console.log('📧 To:', to);
    console.log('📧 Subject:', subject);
    console.log('📧 messageBody:', messageBody);
    console.log('📧 messageText:', messageText);
    console.log('📧 replyToMessageId:', replyToMessageId);
    console.log('📧 threadId:', threadId);
    
    // messageBodyまたはmessageTextのどちらかを使用
    const finalMessageBody = messageBody || messageText;
    console.log('📧 Final message body to send:', finalMessageBody);

    if (!to || !subject || !finalMessageBody) {
      console.error('❌ Missing required fields:', { to: !!to, subject: !!subject, finalMessageBody: !!finalMessageBody });
      return NextResponse.json(
        { error: 'Missing required fields: to, subject, body' },
        { status: 400 }
      );
    }

    // From ヘッダー用の送信者情報を取得
    console.log('🔍 Getting user info for From header...');
    const session_info = await fetch('https://www.googleapis.com/oauth2/v2/userinfo', {
      headers: {
        'Authorization': `Bearer ${session.accessToken}`,
      },
    });
    
    let fromName = 'InfuMatch';
    if (session_info.ok) {
      const userInfo = await session_info.json();
      fromName = userInfo.name || 'InfuMatch';
      console.log('📧 User info retrieved:', userInfo);
      console.log('📧 From name:', fromName);
      console.log('📧 User email:', session.user?.email);
    } else {
      console.warn('⚠️ Failed to get user info, using default fromName');
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
    console.log('🔍 Building email message...');
    
    // 各ヘッダーをエンコード処理
    const encodedFromName = encodeMimeWord(fromName);
    const encodedSubject = encodeMimeWord(subject);
    
    // Toヘッダーの名前部分もエンコード（名前 <email> 形式の場合）
    let encodedTo = to;
    const toEmailMatch = to.match(/^(.+?)\s*<(.+)>$/);
    if (toEmailMatch) {
      const toName = toEmailMatch[1].trim();
      const toEmail = toEmailMatch[2].trim();
      const encodedToName = encodeMimeWord(toName);
      encodedTo = `${encodedToName} <${toEmail}>`;
    }
    
    console.log('📧 Original fromName:', fromName);
    console.log('📧 Encoded fromName:', encodedFromName);
    console.log('📧 Original subject:', subject);
    console.log('📧 Encoded subject:', encodedSubject);
    console.log('📧 Original to:', to);
    console.log('📧 Encoded to:', encodedTo);
    
    const emailLines = [
      `From: ${encodedFromName} <${session.user?.email || 'noreply@infumatch.com'}>`,
      `To: ${encodedTo}`,
      `Subject: ${encodedSubject}`,
      'MIME-Version: 1.0',
      'Content-Type: text/plain; charset=UTF-8',
      'Content-Transfer-Encoding: base64',
    ];

    // 返信の場合、スレッド用ヘッダーを追加
    if (replyToMessageId) {
      console.log('📧 Adding reply headers for threadId:', threadId, 'replyToMessageId:', replyToMessageId);
      // Gmail のMessage-IDは実際のIDをそのまま使用
      emailLines.push(`In-Reply-To: <${replyToMessageId}>`);
      emailLines.push(`References: <${replyToMessageId}>`);
    }
    
    if (threadId) {
      // ThreadIdをGmail形式で設定
      emailLines.push(`Thread-Topic: ${threadId}`);
    }

    console.log('📧 Email headers constructed:', emailLines);

    // 本文をBase64エンコード
    const bodyBase64 = Buffer.from(finalMessageBody, 'utf8').toString('base64');
    console.log('📧 Original body:', finalMessageBody);
    console.log('📧 Base64 encoded body (first 100 chars):', bodyBase64.substring(0, 100) + '...');

    // 完全なメッセージを構築
    const fullMessage = emailLines.join('\r\n') + '\r\n\r\n' + bodyBase64;
    console.log('📧 Full message structure (first 500 chars):', fullMessage.substring(0, 500) + '...');
    
    // Gmail APIのraw形式にエンコード
    const encodedMessage = Buffer.from(fullMessage, 'utf8')
      .toString('base64')
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=+$/, '');

    console.log('📧 Final encoded message length:', encodedMessage.length);
    console.log('📧 Encoded message preview (first 200 chars):', encodedMessage.substring(0, 200) + '...');

    console.log('🚀 Sending email via Gmail API...');
    console.log('📧 Final summary - To:', to, 'Subject:', subject, 'Body length:', finalMessageBody.length);

    // Gmail Send APIエンドポイント
    const gmailUrl = 'https://gmail.googleapis.com/gmail/v1/users/me/messages/send';
    
    const requestPayload = {
      raw: encodedMessage
    };
    
    console.log('📧 Gmail API request payload keys:', Object.keys(requestPayload));
    
    const response = await fetch(gmailUrl, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${session.accessToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestPayload)
    });

    if (!response.ok) {
      console.error('❌ Gmail send API error:', response.status, response.statusText);
      const errorText = await response.text();
      console.error('❌ Error details:', errorText);
      console.log('=== EMAIL SEND DEBUG END (ERROR) ===');
      
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
    console.log('✅ Email sent successfully! Message ID:', data.id);
    console.log('📧 Response data:', JSON.stringify(data, null, 2));
    console.log('=== EMAIL SEND DEBUG END (SUCCESS) ===');

    return NextResponse.json({ 
      success: true, 
      messageId: data.id,
      message: 'Email sent successfully',
      debugInfo: {
        to,
        subject,
        bodyLength: finalMessageBody.length,
        fromName,
        hasReplyHeaders: !!replyToMessageId
      }
    });
  } catch (error) {
    console.error('Gmail send API error:', error);
    return NextResponse.json(
      { error: 'Internal server error', details: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    );
  }
}