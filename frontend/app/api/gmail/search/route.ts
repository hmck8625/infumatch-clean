import { NextRequest, NextResponse } from 'next/server';
import { GmailService, SearchFilters, SearchOptions } from '@/lib/gmail';
import { withAuth } from '@/lib/auth-middleware';

export const GET = withAuth(async (request: NextRequest, session: any) => {
  try {
    console.log('🔍 Gmail search API called');
    
    const { searchParams } = new URL(request.url);
    
    // 検索フィルターを構築
    const filters: SearchFilters = {};
    const options: SearchOptions = {};
    
    // クエリパラメータから検索条件を取得
    if (searchParams.get('query')) filters.query = searchParams.get('query')!;
    if (searchParams.get('from')) filters.from = searchParams.get('from')!;
    if (searchParams.get('to')) filters.to = searchParams.get('to')!;
    if (searchParams.get('subject')) filters.subject = searchParams.get('subject')!;
    
    // ブール値パラメータ
    if (searchParams.get('hasAttachment') === 'true') filters.hasAttachment = true;
    if (searchParams.get('isUnread') === 'true') filters.isUnread = true;
    if (searchParams.get('isImportant') === 'true') filters.isImportant = true;
    
    // 日付パラメータ
    if (searchParams.get('dateAfter')) {
      filters.dateAfter = new Date(searchParams.get('dateAfter')!);
    }
    if (searchParams.get('dateBefore')) {
      filters.dateBefore = new Date(searchParams.get('dateBefore')!);
    }
    
    // ラベル
    if (searchParams.get('labels')) {
      filters.labels = searchParams.get('labels')!.split(',');
    }
    
    // 結果数制限
    if (searchParams.get('maxResults')) {
      filters.maxResults = parseInt(searchParams.get('maxResults')!);
    }
    
    // ページネーション
    if (searchParams.get('pageToken')) {
      options.pageToken = searchParams.get('pageToken')!;
    }
    
    console.log('Search filters:', filters);
    console.log('Search options:', options);

    const gmailService = new GmailService(session.accessToken, session.user?.email || 'default');
    const result = await gmailService.searchThreads(filters, options);

    return NextResponse.json({
      success: true,
      threads: result?.threads || [],
      nextPageToken: result?.nextPageToken,
      totalResults: result?.threads?.length || 0
    });
  } catch (error: any) {
    console.error('❌ Gmail search API error:', {
      message: error?.message,
      stack: error?.stack,
      response: error?.response?.data,
      status: error?.response?.status
    });
    
    return NextResponse.json(
      { 
        error: 'Failed to search Gmail threads',
        details: error?.message || 'Unknown error'
      },
      { status: 500 }
    );
  }
});