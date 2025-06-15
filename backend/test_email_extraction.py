#!/usr/bin/env python3
"""
メールアドレス抽出テストスクリプト

@description 実際の概要欄からメールアドレス抽出をテスト
@author InfuMatch Development Team
@version 1.0.0
"""

import re
import json

def extract_emails_from_description(description):
    """概要欄からメールアドレスを抽出"""
    if not description:
        return []
    
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, description)
    return list(set(emails))  # 重複除去

def test_email_extraction():
    """実際のYouTuberデータでメール抽出をテスト"""
    print("📧 メールアドレス抽出テスト")
    print("=" * 60)
    
    # 実際のデータを読み込み
    try:
        with open('gaming_youtubers.json', 'r', encoding='utf-8') as f:
            youtuber_data = json.load(f)
    except FileNotFoundError:
        print("❌ gaming_youtubers.json が見つかりません")
        return
    
    for i, channel in enumerate(youtuber_data, 1):
        channel_title = channel['channel_title']
        description = channel['description']
        
        print(f"\n{i}. {channel_title}")
        print("-" * 40)
        
        # メール抽出実行
        extracted_emails = extract_emails_from_description(description)
        stored_emails = channel.get('emails', [])
        
        print(f"📄 概要欄の長さ: {len(description)} 文字")
        print(f"🔍 抽出されたメール: {extracted_emails}")
        print(f"💾 保存されているメール: {stored_emails}")
        
        # 概要欄の一部を表示（メール周辺）
        if extracted_emails:
            for email in extracted_emails:
                email_index = description.find(email)
                if email_index != -1:
                    start = max(0, email_index - 50)
                    end = min(len(description), email_index + len(email) + 50)
                    context = description[start:end].replace('\n', ' ')
                    print(f"📍 メール周辺テキスト: ...{context}...")
        else:
            print("📍 概要欄にメールアドレスは含まれていません")
            # 概要欄の最初の200文字を表示
            preview = description[:200].replace('\n', ' ')
            print(f"📖 概要欄プレビュー: {preview}...")

def test_various_email_patterns():
    """様々なメールパターンのテスト"""
    print("\n🧪 メールパターン認識テスト")
    print("=" * 60)
    
    test_cases = [
        "お問い合わせ: contact@example.com までどうぞ",
        "business@gmail.com",
        "info@company.co.jp",
        "user.name+tag@domain-name.com",
        "メール: test123@test.org です",
        "連絡先：hello@world.net",
        "invalid-email-format",
        "test@",
        "@domain.com",
        "正常なメール: valid@test.com と無効: invalid@",
    ]
    
    for i, test_text in enumerate(test_cases, 1):
        emails = extract_emails_from_description(test_text)
        status = "✅" if emails else "❌"
        print(f"{i:2d}. {status} '{test_text}' → {emails}")

def main():
    """メイン実行関数"""
    # 実際のデータでテスト
    test_email_extraction()
    
    # 様々なパターンでテスト
    test_various_email_patterns()
    
    print("\n📊 メール抽出の仕組み:")
    print("1. YouTube Data API で channel.snippet.description を取得")
    print("2. 正規表現でメールアドレスパターンを検索")
    print("3. 抽出されたメールを配列として保存")
    print("4. BigQuery の contact_email には最初のメールを設定")

if __name__ == "__main__":
    main()