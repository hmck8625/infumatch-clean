#!/bin/bash
# Firestore データ登録用スクリプト

echo "🔥 Firestore にゲーム系YouTuberデータを登録中..."

# 1. リカルガ【ゆっくり実況】
gcloud firestore documents create --project=hackathon-462905 \
  --collection=influencers \
  --document-id="UCgokOIWB73ZUg5NdYU9zIUQ" \
  --data='{"channel_id":"UCgokOIWB73ZUg5NdYU9zIUQ","channel_title":"リカルガ【ゆっくり実況】","description":"主にフォートナイトのゆっくり実況を投稿してます！\n色々なゲーム 実況していくのでよければチャンネル登録お願いします！\n#フォートナイト #ゆっくり実況\n","subscriber_count":38800,"video_count":132,"view_count":14610038,"category":"gaming","country":"JP","language":"ja","contact_info":{"emails":[],"primary_email":null},"engagement_metrics":{"engagement_rate":2.8526,"avg_views_per_video":110682.10606060606,"has_contact":false},"ai_analysis":{"content_quality_score":0.8,"brand_safety_score":0.9,"growth_potential":0.7},"status":"active","created_at":"2025-06-14T16:43:04.572665+00:00","updated_at":"2025-06-14T16:43:04.572804+00:00","last_analyzed":"2025-06-15T01:38:26.146758","fetched_at":"2025-06-15T01:38:26.146758","data_source":"youtube_api","collection_method":"manual_search"}'

echo "✅ 1/4 完了: リカルガ【ゆっくり実況】"

# 2. ほとんどホラーゲーム実況ですが何か?
gcloud firestore documents create --project=hackathon-462905 \
  --collection=influencers \
  --document-id="UCZ9baV335FyJiNa4IExtoQw" \
  --data='{"channel_id":"UCZ9baV335FyJiNa4IExtoQw","channel_title":"ほとんどホラーゲーム実況ですが何か?","description":"ホラーゲーム実況を主とするチャンネルです！\nたまにホラーじゃないものやります！\n\n#ホラーゲーム\n#ホラー\n#ゲーム実況","subscriber_count":20400,"video_count":698,"view_count":4697444,"category":"gaming","country":"JP","language":"ja","contact_info":{"emails":[],"primary_email":null},"engagement_metrics":{"engagement_rate":0.3299,"avg_views_per_video":6729.862464183381,"has_contact":false},"ai_analysis":{"content_quality_score":0.8,"brand_safety_score":0.9,"growth_potential":0.7},"status":"active","created_at":"2025-06-14T16:43:04.572828+00:00","updated_at":"2025-06-14T16:43:04.572829+00:00","last_analyzed":"2025-06-15T01:38:26.146809","fetched_at":"2025-06-15T01:38:26.146809","data_source":"youtube_api","collection_method":"manual_search"}'

echo "✅ 2/4 完了: ほとんどホラーゲーム実況ですが何か?"

# 3. ノノムラ猫の考えるゲーム配信
gcloud firestore documents create --project=hackathon-462905 \
  --collection=influencers \
  --document-id="UC4KXxp8JMm-NtfMXG-wbvdw" \
  --data='{"channel_id":"UC4KXxp8JMm-NtfMXG-wbvdw","channel_title":"ノノムラ猫の考えるゲーム配信","description":"アドベンチャー系のゲーム配信をメインに他にも色々やってます。","subscriber_count":18400,"video_count":2142,"view_count":22975579,"category":"gaming","country":"JP","language":"ja","contact_info":{"emails":[],"primary_email":null},"engagement_metrics":{"engagement_rate":0.5829,"avg_views_per_video":10726.22735760971,"has_contact":false},"ai_analysis":{"content_quality_score":0.8,"brand_safety_score":0.9,"growth_potential":0.7},"status":"active","created_at":"2025-06-14T16:43:04.572841+00:00","updated_at":"2025-06-14T16:43:04.572842+00:00","last_analyzed":"2025-06-15T01:38:26.146833","fetched_at":"2025-06-15T01:38:26.146833","data_source":"youtube_api","collection_method":"manual_search"}'

echo "✅ 3/4 完了: ノノムラ猫の考えるゲーム配信"

# 4. あふろ / ゲーム実況
gcloud firestore documents create --project=hackathon-462905 \
  --collection=influencers \
  --document-id="UCFyTRFEClzu_VQkdd5wP0Ew" \
  --data='{"channel_id":"UCFyTRFEClzu_VQkdd5wP0Ew","channel_title":"あふろ / ゲーム実況","description":"↓伝説のYouTuber誕生ボタン↓\nhttps://www.youtube.com/channel/UCFyTRFEClzu_VQkdd5wP0Ew?sub_confirmation=1\n\nこのチャンネルを見つけてくれてありがとう！\n\nこのチャンネルでは、フォートナイト、LEGOフォートナイトに関する動画を中心に更新しています！\n\n週最低5本以上の動画が更新され、建築学生の経験を活かした超イカした建造物、ゲーマーの性を最大限利用した最強攻略情報など、このチャンネルでしか見られない内容が数多くアップされていきます😃\n\nどんな年齢の方でも楽しめる内容ですので、ぜひチャンネル登録、通知オンを押して、最高な動画を見逃さないようにしておきましょう😊\n\nまた、Twitterでのフォローもおすすめです。あなたのアイディアやコメント、リクエストも大歓迎です。共に一人前のYouTuberになる様を見届けてくれよな！\n\nクリエイターサポート【AFR】も合わせてしてくれると嬉しくて鼻毛とひじきの区別もつかなくなるのでよろしく！\n\nてことでここまで読んでくれてありがとう！愛してるぜ！\n\nメンバーシップ加入はこちらから！\nhttps://www.youtube.com/channel/UCFyTRFEClzu_VQkdd5wP0Ew/join\n\nお仕事依頼、お問い合わせはこちらまで！\nhandsomeafro88@gmail.com\n","subscriber_count":41700,"video_count":1094,"view_count":16770024,"category":"gaming","country":"JP","language":"ja","contact_info":{"emails":["handsomeafro88@gmail.com"],"primary_email":"handsomeafro88@gmail.com"},"engagement_metrics":{"engagement_rate":0.3676,"avg_views_per_video":15329.08957952468,"has_contact":true},"ai_analysis":{"content_quality_score":0.8,"brand_safety_score":0.9,"growth_potential":0.7},"status":"active","created_at":"2025-06-14T16:43:04.572851+00:00","updated_at":"2025-06-14T16:43:04.572852+00:00","last_analyzed":"2025-06-15T01:38:26.146878","fetched_at":"2025-06-15T01:38:26.146878","data_source":"youtube_api","collection_method":"manual_search"}'

echo "✅ 4/4 完了: あふろ / ゲーム実況"

echo "🎉 全ての YouTuber データの Firestore 登録が完了しました！"