// Gmail認証テスト用スクリプト
const fs = require('fs');
const path = require('path');

// .env.localファイルを手動で読み込み
const envPath = path.join(__dirname, 'frontend', '.env.local');
if (fs.existsSync(envPath)) {
  const envContent = fs.readFileSync(envPath, 'utf8');
  const envLines = envContent.split('\n');
  
  envLines.forEach(line => {
    if (line.trim() && !line.startsWith('#') && line.includes('=')) {
      const [key, ...valueParts] = line.trim().split('=');
      const value = valueParts.join('=');
      process.env[key] = value;
    }
  });
  console.log('✓ .env.local ファイル読み込み完了');
} else {
  console.log('❌ .env.local ファイルが見つかりません');
}

const { google } = require('googleapis');

console.log('=== Gmail認証テスト ===');
console.log('環境変数チェック:');
console.log('GOOGLE_CLIENT_ID:', process.env.GOOGLE_CLIENT_ID ? '✓ 設定済み' : '❌ 未設定');
console.log('GOOGLE_CLIENT_SECRET:', process.env.GOOGLE_CLIENT_SECRET ? '✓ 設定済み' : '❌ 未設定');
console.log('NEXTAUTH_URL:', process.env.NEXTAUTH_URL || '❌ 未設定');
console.log('NEXTAUTH_SECRET:', process.env.NEXTAUTH_SECRET ? '✓ 設定済み' : '❌ 未設定');

// OAuth2クライアントの作成テスト
try {
  const oauth2Client = new google.auth.OAuth2(
    process.env.GOOGLE_CLIENT_ID,
    process.env.GOOGLE_CLIENT_SECRET,
    `${process.env.NEXTAUTH_URL}/api/auth/callback/google`
  );
  
  console.log('\n✓ OAuth2クライアント作成成功');
  
  // Gmail APIクライアント作成テスト
  const gmail = google.gmail({ version: 'v1', auth: oauth2Client });
  console.log('✓ Gmail APIクライアント作成成功');
  
  // 認証URLの生成テスト
  const scopes = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.compose'
  ];
  
  const authUrl = oauth2Client.generateAuthUrl({
    access_type: 'offline',
    scope: scopes,
    prompt: 'consent'
  });
  
  console.log('✓ 認証URL生成成功');
  console.log('認証URL (最初の100文字):', authUrl.substring(0, 100) + '...');
  
  console.log('\n🎉 すべての認証設定が正常です');
  
} catch (error) {
  console.error('❌ 認証設定エラー:', error.message);
}