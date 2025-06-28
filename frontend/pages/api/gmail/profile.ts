import { NextApiRequest, NextApiResponse } from 'next';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/lib/auth';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const session = await getServerSession(req, res, authOptions);
    
    if (!session?.accessToken) {
      console.error('❌ No access token found in session');
      return res.status(401).json({ error: 'No access token' });
    }

    console.log('📧 Gmail Profile API called');
    
    // Gmail APIでユーザープロファイルを取得
    const response = await fetch('https://gmail.googleapis.com/gmail/v1/users/me/profile', {
      headers: {
        'Authorization': `Bearer ${session.accessToken}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      console.error('❌ Gmail Profile API failed:', response.status, response.statusText);
      return res.status(response.status).json({ error: 'Gmail API error' });
    }

    const profileData = await response.json();
    console.log('✅ Gmail Profile取得成功:', profileData.emailAddress);

    return res.status(200).json({
      emailAddress: profileData.emailAddress,
      messagesTotal: profileData.messagesTotal,
      threadsTotal: profileData.threadsTotal,
      historyId: profileData.historyId
    });

  } catch (error) {
    console.error('❌ Gmail Profile API error:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
}