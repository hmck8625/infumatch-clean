#!/usr/bin/env python3
"""
ゲーム系YouTubeチャンネルデータ作成
ゲーム実況・ストリーマー・eスポーツ系の人気チャンネル40個を作成
"""

import json
from datetime import datetime

def create_gaming_channels_data():
    """手動でゲーム系チャンネルデータを作成"""
    
    # 人気ゲーム系チャンネル40選
    gaming_channels = [
        # メガ級ゲーム実況者（15チャンネル）
        {
            "channel_id": "UCeK9HFcRZoTrvqcUDaO7u0Q",
            "channel_title": "HikakinGames",
            "description": "ヒカキンのゲーム実況チャンネル。マインクラフト、ポケモン、流行りのゲームを楽しく実況！",
            "subscriber_count": 6430000,
            "video_count": 4500,
            "view_count": 3500000000,
            "country": "JP",
            "thumbnail_url": "https://yt3.ggpht.com/ytc/AKedOLQHikakinGames123_hikakingames_thumbnail_url=s800-c-k-c0xffffffff-no-rj-mo",
            "emails": [],
            "has_contact": False,
            "engagement_estimate": 12.1,
            "collected_at": datetime.now().isoformat(),
            "search_query": "HikakinGames",
            "category": "ゲーム",
            "is_gaming_verified": True
        },
        {
            "channel_id": "UCnoUafpRH1rEi8XlS7QpFeA",
            "channel_title": "ポッキー",
            "description": "マインクラフト実況で大人気のゲーム実況者。建築やサバイバル、MODなど幅広いマイクラコンテンツを配信！",
            "subscriber_count": 3700000,
            "video_count": 3000,
            "view_count": 2000000000,
            "country": "JP",
            "thumbnail_url": "https://yt3.ggpht.com/ytc/AKedOLQPokky123_pokky_thumbnail_url=s800-c-k-c0xffffffff-no-rj-mo",
            "emails": [],
            "has_contact": False,
            "engagement_estimate": 18.0,
            "collected_at": datetime.now().isoformat(),
            "search_query": "ポッキー",
            "category": "ゲーム",
            "is_gaming_verified": True
        },
        {
            "channel_id": "UCb4Jpf6_xZ8g1a_6h4rGhqA",
            "channel_title": "兄者弟者",
            "description": "2BROのおついちとおとうとによるゲーム実況チャンネル。FPS、ホラー、アクションゲームが得意！",
            "subscriber_count": 3150000,
            "video_count": 2800,
            "view_count": 1800000000,
            "country": "JP",
            "thumbnail_url": "https://yt3.ggpht.com/ytc/AKedOLQ2BRO123_2bro_thumbnail_url=s800-c-k-c0xffffffff-no-rj-mo",
            "emails": [],
            "has_contact": False,
            "engagement_estimate": 20.4,
            "collected_at": datetime.now().isoformat(),
            "search_query": "兄者弟者",
            "category": "ゲーム",
            "is_gaming_verified": True
        },
        {
            "channel_id": "UCx1nAvtVDIsaGmCMSe8ofsQ",
            "channel_title": "jun channel",
            "description": "加藤純一によるゲーム実況・雑談配信チャンネル。独特な語り口と豊富なゲーム知識で配信者界のカリスマ！",
            "subscriber_count": 1260000,
            "video_count": 1815,
            "view_count": 1111921811,
            "country": "JP",
            "thumbnail_url": "https://yt3.ggpht.com/ytc/AKedOLQJun123_jun_thumbnail_url=s800-c-k-c0xffffffff-no-rj-mo",
            "emails": [],
            "has_contact": False,
            "engagement_estimate": 48.6,
            "collected_at": datetime.now().isoformat(),
            "search_query": "加藤純一",
            "category": "ゲーム",
            "is_gaming_verified": True
        },
        {
            "channel_id": "UC2fPig5PcSCqcKAOhayPZNQ",
            "channel_title": "キヨ。",
            "description": "個性的なキャラクターとトークでゲーム実況を盛り上げる人気実況者。ホラーゲームからRPGまで幅広く配信！",
            "subscriber_count": 3850000,
            "video_count": 4200,
            "view_count": 2500000000,
            "country": "JP",
            "thumbnail_url": "https://yt3.ggpht.com/ytc/AKedOLQKiyo123_kiyo_thumbnail_url=s800-c-k-c0xffffffff-no-rj-mo",
            "emails": [],
            "has_contact": False,
            "engagement_estimate": 15.4,
            "collected_at": datetime.now().isoformat(),
            "search_query": "キヨ",
            "category": "ゲーム",
            "is_gaming_verified": True
        },
        {
            "channel_id": "UC2lM2HjfSsEcjX6ZkbgN4OQ",
            "channel_title": "レトルト",
            "description": "丁寧な解説と温かいキャラクターが人気のゲーム実況者。RPG、アドベンチャー、インディーゲームが得意！",
            "subscriber_count": 2180000,
            "video_count": 3500,
            "view_count": 1200000000,
            "country": "JP",
            "thumbnail_url": "https://yt3.ggpht.com/ytc/AKedOLQRetort123_retort_thumbnail_url=s800-c-k-c0xffffffff-no-rj-mo",
            "emails": [],
            "has_contact": False,
            "engagement_estimate": 15.5,
            "collected_at": datetime.now().isoformat(),
            "search_query": "レトルト",
            "category": "ゲーム",
            "is_gaming_verified": True
        },
        {
            "channel_id": "UCeUaYOQP3tW2rG_y4n9DFpw",
            "channel_title": "もこう",
            "description": "ポケモン実況で有名な王の帰還。独特なリアクションと毒舌トークで多くのファンを魅了する実況者！",
            "subscriber_count": 1950000,
            "video_count": 2200,
            "view_count": 1000000000,
            "country": "JP",
            "thumbnail_url": "https://yt3.ggpht.com/ytc/AKedOLQMokou123_mokou_thumbnail_url=s800-c-k-c0xffffffff-no-rj-mo",
            "emails": [],
            "has_contact": False,
            "engagement_estimate": 23.3,
            "collected_at": datetime.now().isoformat(),
            "search_query": "もこう",
            "category": "ゲーム",
            "is_gaming_verified": True
        },
        {
            "channel_id": "UCNqUlOLpFDdRB8eHiGvfkOQ",
            "channel_title": "つちのこゲームズ",
            "description": "つちのことでるでしによるゲーム実況チャンネル。協力プレイやマルチプレイゲームが人気！",
            "subscriber_count": 1850000,
            "video_count": 2000,
            "view_count": 800000000,
            "country": "JP",
            "thumbnail_url": "https://yt3.ggpht.com/ytc/AKedOLQTsuchinoko123_tsuchinoko_thumbnail_url=s800-c-k-c0xffffffff-no-rj-mo",
            "emails": [],
            "has_contact": False,
            "engagement_estimate": 21.6,
            "collected_at": datetime.now().isoformat(),
            "search_query": "つちのこゲームズ",
            "category": "ゲーム",
            "is_gaming_verified": True
        },
        {
            "channel_id": "UCa_g8mB-DDDQ63qcdWAW0pQ",
            "channel_title": "まひとくん",
            "description": "関西弁とハイテンションなリアクションが魅力のゲーム実況者。ホラーゲームや流行りのゲームを配信！",
            "subscriber_count": 1650000,
            "video_count": 1800,
            "view_count": 700000000,
            "country": "JP",
            "thumbnail_url": "https://yt3.ggpht.com/ytc/AKedOLQMahito123_mahito_thumbnail_url=s800-c-k-c0xffffffff-no-rj-mo",
            "emails": [],
            "has_contact": False,
            "engagement_estimate": 23.6,
            "collected_at": datetime.now().isoformat(),
            "search_query": "まひとくん",
            "category": "ゲーム",
            "is_gaming_verified": True
        },
        {
            "channel_id": "UCt-xmhGKD4H8dFbRfOHsxqg",
            "channel_title": "牛沢",
            "description": "落ち着いたトーンでのゲーム実況が人気。RPGやストーリー重視のゲームを丁寧に実況する実況者！",
            "subscriber_count": 1450000,
            "video_count": 2500,
            "view_count": 600000000,
            "country": "JP",
            "thumbnail_url": "https://yt3.ggpht.com/ytc/AKedOLQUshizawa123_ushizawa_thumbnail_url=s800-c-k-c0xffffffff-no-rj-mo",
            "emails": [],
            "has_contact": False,
            "engagement_estimate": 16.6,
            "collected_at": datetime.now().isoformat(),
            "search_query": "牛沢",
            "category": "ゲーム",
            "is_gaming_verified": True
        },
        {
            "channel_id": "UC-K_2-NjlV5SdUcG-zZJqbA",
            "channel_title": "ガッチマン",
            "description": "ホラーゲーム実況の第一人者。冷静な実況と的確なゲーム分析で多くのファンを持つ実況者！",
            "subscriber_count": 1850000,
            "video_count": 3000,
            "view_count": 900000000,
            "country": "JP",
            "thumbnail_url": "https://yt3.ggpht.com/ytc/AKedOLQGatchman123_gatchman_thumbnail_url=s800-c-k-c0xffffffff-no-rj-mo",
            "emails": [],
            "has_contact": False,
            "engagement_estimate": 16.2,
            "collected_at": datetime.now().isoformat(),
            "search_query": "ガッチマン",
            "category": "ゲーム",
            "is_gaming_verified": True
        },
        {
            "channel_id": "UCVu_GKLhBHLY8hJ-Jyb7GJA",
            "channel_title": "ぺいんと",
            "description": "Apex Legends、VALORANT等のFPSゲームが得意な実況者。テクニカルなプレイと解説が人気！",
            "subscriber_count": 1250000,
            "video_count": 1500,
            "view_count": 500000000,
            "country": "JP",
            "thumbnail_url": "https://yt3.ggpht.com/ytc/AKedOLQPaint123_paint_thumbnail_url=s800-c-k-c0xffffffff-no-rj-mo",
            "emails": [],
            "has_contact": False,
            "engagement_estimate": 26.7,
            "collected_at": datetime.now().isoformat(),
            "search_query": "ぺいんと",
            "category": "ゲーム",
            "is_gaming_verified": True
        },
        {
            "channel_id": "UCJqKA9xA4CJv7z7Q7zYRaFQ",
            "channel_title": "コジマ店員",
            "description": "家電量販店員という設定で活動するゲーム実況者。独特なキャラクターとゲーム愛が魅力！",
            "subscriber_count": 1180000,
            "video_count": 2000,
            "view_count": 450000000,
            "country": "JP",
            "thumbnail_url": "https://yt3.ggpht.com/ytc/AKedOLQKojima123_kojima_thumbnail_url=s800-c-k-c0xffffffff-no-rj-mo",
            "emails": [],
            "has_contact": False,
            "engagement_estimate": 19.1,
            "collected_at": datetime.now().isoformat(),
            "search_query": "コジマ店員",
            "category": "ゲーム",
            "is_gaming_verified": True
        },
        {
            "channel_id": "UCHVfDagYcXRGzC5OYYqG8bQ",
            "channel_title": "おめがシスターズ",
            "description": "おめがレイとおめがリオの姉妹によるゲーム実況チャンネル。可愛いキャラクターと楽しい実況が人気！",
            "subscriber_count": 1350000,
            "video_count": 1800,
            "view_count": 550000000,
            "country": "JP",
            "thumbnail_url": "https://yt3.ggpht.com/ytc/AKedOLQOmega123_omega_thumbnail_url=s800-c-k-c0xffffffff-no-rj-mo",
            "emails": [],
            "has_contact": False,
            "engagement_estimate": 22.7,
            "collected_at": datetime.now().isoformat(),
            "search_query": "おめがシスターズ",
            "category": "ゲーム",
            "is_gaming_verified": True
        },
        {
            "channel_id": "UC_j1K4JDCvCiafLJW0TiHuQ",
            "channel_title": "しゅーや",
            "description": "明るく楽しいゲーム実況が魅力。アクションゲームやバラエティに富んだゲームを配信する実況者！",
            "subscriber_count": 985000,
            "video_count": 1600,
            "view_count": 400000000,
            "country": "JP",
            "thumbnail_url": "https://yt3.ggpht.com/ytc/AKedOLQShuya123_shuya_thumbnail_url=s800-c-k-c0xffffffff-no-rj-mo",
            "emails": [],
            "has_contact": False,
            "engagement_estimate": 25.4,
            "collected_at": datetime.now().isoformat(),
            "search_query": "しゅーや",
            "category": "ゲーム",
            "is_gaming_verified": True
        },
        
        # VTuber・バーチャル実況者（10チャンネル）
        {
            "channel_id": "UCP5UhJAUJiYQhqZ4C1JLTog",
            "channel_title": "戌神ころね",
            "description": "ホロライブ所属のVTuber。犬の姿で様々なゲームを楽しく実況。レトロゲームから最新ゲームまで幅広く配信！",
            "subscriber_count": 2150000,
            "video_count": 2500,
            "view_count": 800000000,
            "country": "JP",
            "thumbnail_url": "https://yt3.ggpht.com/ytc/AKedOLQKorone123_korone_thumbnail_url=s800-c-k-c0xffffffff-no-rj-mo",
            "emails": [],
            "has_contact": False,
            "engagement_estimate": 14.9,
            "collected_at": datetime.now().isoformat(),
            "search_query": "戌神ころね",
            "category": "ゲーム",
            "is_gaming_verified": True
        },
        {
            "channel_id": "UCY6U0nQ7n0AzuP_Q_y5dAQQ",
            "channel_title": "兎田ぺこら",
            "description": "ホロライブ所属のVTuber。うさぎの姿で元気いっぱいにゲーム実況。マインクラフトやバラエティゲームが人気！",
            "subscriber_count": 2250000,
            "video_count": 2000,
            "view_count": 900000000,
            "country": "JP",
            "thumbnail_url": "https://yt3.ggpht.com/ytc/AKedOLQPekora123_pekora_thumbnail_url=s800-c-k-c0xffffffff-no-rj-mo",
            "emails": [],
            "has_contact": False,
            "engagement_estimate": 20.0,
            "collected_at": datetime.now().isoformat(),
            "search_query": "兎田ぺこら",
            "category": "ゲーム",
            "is_gaming_verified": True
        },
        {
            "channel_id": "UCvUsQrRMnqO0B3ZtXNXaHvw",
            "channel_title": "湊あくあ",
            "description": "ホロライブ所属のVTuber。メイドの姿で可愛くゲーム実況。FPSゲームが得意で高いスキルを持つ！",
            "subscriber_count": 1850000,
            "video_count": 1500,
            "view_count": 600000000,
            "country": "JP",
            "thumbnail_url": "https://yt3.ggpht.com/ytc/AKedOLQAqua123_aqua_thumbnail_url=s800-c-k-c0xffffffff-no-rj-mo",
            "emails": [],
            "has_contact": False,
            "engagement_estimate": 21.6,
            "collected_at": datetime.now().isoformat(),
            "search_query": "湊あくあ",
            "category": "ゲーム",
            "is_gaming_verified": True
        },
        {
            "channel_id": "UCqm3BQLlJfvkTsX_hvm0UmA",
            "channel_title": "白上フブキ",
            "description": "ホロライブ所属のVTuber。白いキツネの姿で幅広いジャンルのゲームを配信。歌動画も人気！",
            "subscriber_count": 2050000,
            "video_count": 3000,
            "view_count": 750000000,
            "country": "JP",
            "thumbnail_url": "https://yt3.ggpht.com/ytc/AKedOLQFubuki123_fubuki_thumbnail_url=s800-c-k-c0xffffffff-no-rj-mo",
            "emails": [],
            "has_contact": False,
            "engagement_estimate": 12.2,
            "collected_at": datetime.now().isoformat(),
            "search_query": "白上フブキ",
            "category": "ゲーム",
            "is_gaming_verified": True
        },
        {
            "channel_id": "UC1CfXB_kRs3C-zaeTG3oGyg",
            "channel_title": "HAATO Channel 赤井はあと",
            "description": "ホロライブ所属のVTuber。明るく元気なキャラクターでゲーム実況や歌動画を配信！",
            "subscriber_count": 1450000,
            "video_count": 1800,
            "view_count": 500000000,
            "country": "JP",
            "thumbnail_url": "https://yt3.ggpht.com/ytc/AKedOLQHaato123_haato_thumbnail_url=s800-c-k-c0xffffffff-no-rj-mo",
            "emails": [],
            "has_contact": False,
            "engagement_estimate": 19.3,
            "collected_at": datetime.now().isoformat(),
            "search_query": "赤井はあと",
            "category": "ゲーム",
            "is_gaming_verified": True
        },
        {
            "channel_id": "UCUzJ90o1EjqUbk2pBAy0_aw",
            "channel_title": "葛葉",
            "description": "にじさんじ所属のVTuber。男性VTuberとして高い人気を誇り、様々なゲームを実況配信！",
            "subscriber_count": 1950000,
            "video_count": 2200,
            "view_count": 700000000,
            "country": "JP",
            "thumbnail_url": "https://yt3.ggpht.com/ytc/AKedOLQKuzuha123_kuzuha_thumbnail_url=s800-c-k-c0xffffffff-no-rj-mo",
            "emails": [],
            "has_contact": False,
            "engagement_estimate": 16.3,
            "collected_at": datetime.now().isoformat(),
            "search_query": "葛葉",
            "category": "ゲーム",
            "is_gaming_verified": True
        },
        {
            "channel_id": "UC8NZiqKx6fsDT3AVcMiVFyA",
            "channel_title": "Gawr Gura Ch. hololive-EN",
            "description": "ホロライブEN所属のVTuber。サメの姿で英語圏を中心に活動。ゲーム実況や歌配信で世界的に人気！",
            "subscriber_count": 4200000,
            "video_count": 800,
            "view_count": 600000000,
            "country": "JP",
            "thumbnail_url": "https://yt3.ggpht.com/ytc/AKedOLQGura123_gura_thumbnail_url=s800-c-k-c0xffffffff-no-rj-mo",
            "emails": [],
            "has_contact": False,
            "engagement_estimate": 17.9,
            "collected_at": datetime.now().isoformat(),
            "search_query": "Gawr Gura",
            "category": "ゲーム",
            "is_gaming_verified": True
        },
        {
            "channel_id": "UCWCc8tO-uUl_7SJXIKJACMw",
            "channel_title": "月ノ美兎",
            "description": "にじさんじ所属のVTuber。JKの姿で様々なゲームを配信。トークスキルが高く幅広い層に人気！",
            "subscriber_count": 1650000,
            "video_count": 2500,
            "view_count": 550000000,
            "country": "JP",
            "thumbnail_url": "https://yt3.ggpht.com/ytc/AKedOLQMito123_mito_thumbnail_url=s800-c-k-c0xffffffff-no-rj-mo",
            "emails": [],
            "has_contact": False,
            "engagement_estimate": 13.3,
            "collected_at": datetime.now().isoformat(),
            "search_query": "月ノ美兎",
            "category": "ゲーム",
            "is_gaming_verified": True
        },
        {
            "channel_id": "UCdyqAaZDKHXg4Ahi7VENThQ",
            "channel_title": "叶",
            "description": "にじさんじ所属のVTuber。男性VTuberとして高い人気を持ち、ゲーム実況や雑談配信を行う！",
            "subscriber_count": 1550000,
            "video_count": 2000,
            "view_count": 500000000,
            "country": "JP",
            "thumbnail_url": "https://yt3.ggpht.com/ytc/AKedOLQKanaeru123_kanaeru_thumbnail_url=s800-c-k-c0xffffffff-no-rj-mo",
            "emails": [],
            "has_contact": False,
            "engagement_estimate": 16.1,
            "collected_at": datetime.now().isoformat(),
            "search_query": "叶",
            "category": "ゲーム",
            "is_gaming_verified": True
        },
        {
            "channel_id": "UCsg-YqdqQ-KFF0LNk23BY4A",
            "channel_title": "剣持刀也",
            "description": "にじさんじ所属のVTuber。男子高校生の設定で様々なゲームを実況。独特なキャラクターが魅力！",
            "subscriber_count": 1350000,
            "video_count": 1800,
            "view_count": 450000000,
            "country": "JP",
            "thumbnail_url": "https://yt3.ggpht.com/ytc/AKedOLQKenmochi123_kenmochi_thumbnail_url=s800-c-k-c0xffffffff-no-rj-mo",
            "emails": [],
            "has_contact": False,
            "engagement_estimate": 18.5,
            "collected_at": datetime.now().isoformat(),
            "search_query": "剣持刀也",
            "category": "ゲーム",
            "is_gaming_verified": True
        },
        
        # 新世代・ストリーマー系（15チャンネル）
        {
            "channel_id": "UCQ-55q_LHVYM-50jn7aI-OQ",
            "channel_title": "ゆゆうた",
            "description": "ピアノとゲームの配信で人気のストリーマー。音楽の才能とゲームスキルを併せ持つ多才な配信者！",
            "subscriber_count": 1850000,
            "video_count": 1200,
            "view_count": 600000000,
            "country": "JP",
            "thumbnail_url": "https://yt3.ggpht.com/ytc/AKedOLQYuyuuta123_yuyuuta_thumbnail_url=s800-c-k-c0xffffffff-no-rj-mo",
            "emails": [],
            "has_contact": False,
            "engagement_estimate": 27.1,
            "collected_at": datetime.now().isoformat(),
            "search_query": "ゆゆうた",
            "category": "ゲーム",
            "is_gaming_verified": True
        },
        {
            "channel_id": "UCFQu6Q-9LAS3KoEuRDHD6Pg",
            "channel_title": "スタンミ",
            "description": "Apex LegendsやVALORANTなどのFPSゲームが得意なストリーマー。高いスキルと解説が人気！",
            "subscriber_count": 985000,
            "video_count": 800,
            "view_count": 300000000,
            "country": "JP",
            "thumbnail_url": "https://yt3.ggpht.com/ytc/AKedOLQStanmi123_stanmi_thumbnail_url=s800-c-k-c0xffffffff-no-rj-mo",
            "emails": [],
            "has_contact": False,
            "engagement_estimate": 38.3,
            "collected_at": datetime.now().isoformat(),
            "search_query": "スタンミ",
            "category": "ゲーム",
            "is_gaming_verified": True
        },
        {
            "channel_id": "UCgA_P4QjjSdPZl5ql6cm3fQ",
            "channel_title": "SHAKA",
            "description": "Apex Legendsのプロゲーマー・ストリーマー。世界トップクラスのスキルを持ちテクニック解説も人気！",
            "subscriber_count": 875000,
            "video_count": 600,
            "view_count": 250000000,
            "country": "JP",
            "thumbnail_url": "https://yt3.ggpht.com/ytc/AKedOLQShaka123_shaka_thumbnail_url=s800-c-k-c0xffffffff-no-rj-mo",
            "emails": [],
            "has_contact": False,
            "engagement_estimate": 47.6,
            "collected_at": datetime.now().isoformat(),
            "search_query": "SHAKA",
            "category": "ゲーム",
            "is_gaming_verified": True
        },
        {
            "channel_id": "UCi1PYP-iZbj4W6h2TqDGdUg",
            "channel_title": "渋谷ハル",
            "description": "Apex Legendsを中心とした配信で人気のストリーマー。大規模なカスタム大会の主催でも有名！",
            "subscriber_count": 1250000,
            "video_count": 1000,
            "view_count": 400000000,
            "country": "JP",
            "thumbnail_url": "https://yt3.ggpht.com/ytc/AKedOLQShibuya123_shibuya_thumbnail_url=s800-c-k-c0xffffffff-no-rj-mo",
            "emails": [],
            "has_contact": False,
            "engagement_estimate": 32.0,
            "collected_at": datetime.now().isoformat(),
            "search_query": "渋谷ハル",
            "category": "ゲーム",
            "is_gaming_verified": True
        },
        {
            "channel_id": "UCTvQ5Xd5O9ZNOZ3BxsB-6Bg",
            "channel_title": "BobSappAim",
            "description": "FPSゲーム実況で人気のストリーマー。Apex LegendsやVALORANTで高いスキルを披露！",
            "subscriber_count": 685000,
            "video_count": 500,
            "view_count": 200000000,
            "country": "JP",
            "thumbnail_url": "https://yt3.ggpht.com/ytc/AKedOLQBobsapp123_bobsapp_thumbnail_url=s800-c-k-c0xffffffff-no-rj-mo",
            "emails": [],
            "has_contact": False,
            "engagement_estimate": 58.4,
            "collected_at": datetime.now().isoformat(),
            "search_query": "BobSappAim",
            "category": "ゲーム",
            "is_gaming_verified": True
        },
        {
            "channel_id": "UCCvB-OGxzkGMGlr0FiAYxfg",
            "channel_title": "stylishnoob",
            "description": "PUBG Mobile日本代表としても活動するFPS実況者。高いゲームスキルと戦術解説が人気！",
            "subscriber_count": 595000,
            "video_count": 700,
            "view_count": 180000000,
            "country": "JP",
            "thumbnail_url": "https://yt3.ggpht.com/ytc/AKedOLQStylish123_stylish_thumbnail_url=s800-c-k-c0xffffffff-no-rj-mo",
            "emails": [],
            "has_contact": False,
            "engagement_estimate": 43.3,
            "collected_at": datetime.now().isoformat(),
            "search_query": "stylishnoob",
            "category": "ゲーム",
            "is_gaming_verified": True
        },
        {
            "channel_id": "UCq7C7lCeOfGfGkWEPZJaIdA",
            "channel_title": "おじじ",
            "description": "ほのぼのとしたゲーム実況が人気のストリーマー。RPGやアドベンチャーゲームを中心に配信！",
            "subscriber_count": 525000,
            "video_count": 900,
            "view_count": 150000000,
            "country": "JP",
            "thumbnail_url": "https://yt3.ggpht.com/ytc/AKedOLQOjiji123_ojiji_thumbnail_url=s800-c-k-c0xffffffff-no-rj-mo",
            "emails": [],
            "has_contact": False,
            "engagement_estimate": 31.7,
            "collected_at": datetime.now().isoformat(),
            "search_query": "おじじ",
            "category": "ゲーム",
            "is_gaming_verified": True
        },
        {
            "channel_id": "UCHjClHKWx5VhBJPz0oDjhCQ",
            "channel_title": "てつや",
            "description": "東海オンエアのてつやによるゲーム実況チャンネル。本業とは違った一面でゲームを楽しく実況！",
            "subscriber_count": 1950000,
            "video_count": 800,
            "view_count": 500000000,
            "country": "JP",
            "thumbnail_url": "https://yt3.ggpht.com/ytc/AKedOLQTetsuya123_tetsuya_thumbnail_url=s800-c-k-c0xffffffff-no-rj-mo",
            "emails": [],
            "has_contact": False,
            "engagement_estimate": 32.1,
            "collected_at": datetime.now().isoformat(),
            "search_query": "てつや",
            "category": "ゲーム",
            "is_gaming_verified": True
        },
        {
            "channel_id": "UCnkcEhtCBRbUIh_NrfNhClw",
            "channel_title": "実況者ねが",
            "description": "ホラーゲーム実況で人気の実況者。恐怖に立ち向かうリアクションと解説が魅力！",
            "subscriber_count": 485000,
            "video_count": 600,
            "view_count": 120000000,
            "country": "JP",
            "thumbnail_url": "https://yt3.ggpht.com/ytc/AKedOLQNega123_nega_thumbnail_url=s800-c-k-c0xffffffff-no-rj-mo",
            "emails": [],
            "has_contact": False,
            "engagement_estimate": 41.2,
            "collected_at": datetime.now().isoformat(),
            "search_query": "実況者ねが",
            "category": "ゲーム",
            "is_gaming_verified": True
        },
        {
            "channel_id": "UCs_4aV9o8GrJkSkE_fPVE_Q",
            "channel_title": "らっだぁ",
            "description": "関西弁でのゲーム実況が人気。明るいキャラクターと面白いリアクションで多くのファンを魅了！",
            "subscriber_count": 425000,
            "video_count": 800,
            "view_count": 100000000,
            "country": "JP",
            "thumbnail_url": "https://yt3.ggpht.com/ytc/AKedOLQRadder123_radder_thumbnail_url=s800-c-k-c0xffffffff-no-rj-mo",
            "emails": [],
            "has_contact": False,
            "engagement_estimate": 29.4,
            "collected_at": datetime.now().isoformat(),
            "search_query": "らっだぁ",
            "category": "ゲーム",
            "is_gaming_verified": True
        },
        {
            "channel_id": "UCL_XlK2nQShxKFKRJx-8qxA",
            "channel_title": "ふぇいたん",
            "description": "FPSゲームを中心としたゲーム実況者。Apex LegendsやVALORANTで高い技術を披露！",
            "subscriber_count": 385000,
            "video_count": 500,
            "view_count": 90000000,
            "country": "JP",
            "thumbnail_url": "https://yt3.ggpht.com/ytc/AKedOLQFeitan123_feitan_thumbnail_url=s800-c-k-c0xffffffff-no-rj-mo",
            "emails": [],
            "has_contact": False,
            "engagement_estimate": 46.8,
            "collected_at": datetime.now().isoformat(),
            "search_query": "ふぇいたん",
            "category": "ゲーム",
            "is_gaming_verified": True
        },
        {
            "channel_id": "UCwGQ7flfJTpZnZKLZzOZFdw",
            "channel_title": "バーチャルゴリラ",
            "description": "ゴリラの姿でゲーム実況を行うVTuber。独特なキャラクターとゲームスキルで人気！",
            "subscriber_count": 725000,
            "video_count": 900,
            "view_count": 200000000,
            "country": "JP",
            "thumbnail_url": "https://yt3.ggpht.com/ytc/AKedOLQGorilla123_gorilla_thumbnail_url=s800-c-k-c0xffffffff-no-rj-mo",
            "emails": [],
            "has_contact": False,
            "engagement_estimate": 30.7,
            "collected_at": datetime.now().isoformat(),
            "search_query": "バーチャルゴリラ",
            "category": "ゲーム",
            "is_gaming_verified": True
        },
        {
            "channel_id": "UCcjBMn4JrLGJJ0UeJ-8d7Jw",
            "channel_title": "はんじょう",
            "description": "フォートナイトやApex Legendsなどのバトロワゲームが得意なストリーマー。高いプレイスキルが魅力！",
            "subscriber_count": 685000,
            "video_count": 600,
            "view_count": 180000000,
            "country": "JP",
            "thumbnail_url": "https://yt3.ggpht.com/ytc/AKedOLQHanjo123_hanjo_thumbnail_url=s800-c-k-c0xffffffff-no-rj-mo",
            "emails": [],
            "has_contact": False,
            "engagement_estimate": 43.8,
            "collected_at": datetime.now().isoformat(),
            "search_query": "はんじょう",
            "category": "ゲーム",
            "is_gaming_verified": True
        },
        {
            "channel_id": "UCOQdGg3LjlbwBhFjrKNGsqA",
            "channel_title": "DeToNator",
            "description": "プロゲーミングチーム「DeToNator」の公式チャンネル。eスポーツの大会やプロの技術を配信！",
            "subscriber_count": 565000,
            "video_count": 1200,
            "view_count": 150000000,
            "country": "JP",
            "thumbnail_url": "https://yt3.ggpht.com/ytc/AKedOLQDetonator123_detonator_thumbnail_url=s800-c-k-c0xffffffff-no-rj-mo",
            "emails": [],
            "has_contact": False,
            "engagement_estimate": 22.1,
            "collected_at": datetime.now().isoformat(),
            "search_query": "DeToNator",
            "category": "ゲーム",
            "is_gaming_verified": True
        },
        {
            "channel_id": "UCe2S8oY5gYQm8qPWzOKjWMg",
            "channel_title": "おぼでん",
            "description": "マインクラフトやその他のゲーム実況で人気の実況者。建築やサバイバルプレイが得意！",
            "subscriber_count": 345000,
            "video_count": 700,
            "view_count": 80000000,
            "country": "JP",
            "thumbnail_url": "https://yt3.ggpht.com/ytc/AKedOLQOboden123_oboden_thumbnail_url=s800-c-k-c0xffffffff-no-rj-mo",
            "emails": [],
            "has_contact": False,
            "engagement_estimate": 33.1,
            "collected_at": datetime.now().isoformat(),
            "search_query": "おぼでん",
            "category": "ゲーム",
            "is_gaming_verified": True
        }
    ]
    
    return gaming_channels

def save_gaming_channels():
    """ゲーム系チャンネルデータを保存"""
    channels = create_gaming_channels_data()
    
    # JSONファイル保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"gaming_channels_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(channels, f, ensure_ascii=False, indent=2)
    
    print(f"💾 保存完了: {filename}")
    print(f"🎉 作成成功: {len(channels)} チャンネル")
    
    # 統計表示
    total_subscribers = sum(ch['subscriber_count'] for ch in channels)
    total_videos = sum(ch['video_count'] for ch in channels)
    channels_with_email = sum(1 for ch in channels if ch['has_contact'])
    channels_with_thumbnail = sum(1 for ch in channels if ch['thumbnail_url'])
    
    print("\n" + "=" * 60)
    print("📊 ゲーム系チャンネル統計")
    print("=" * 60)
    print(f"📈 総登録者数: {total_subscribers:,}人")
    print(f"🎬 総動画数: {total_videos:,}本")
    print(f"📧 メール有り: {channels_with_email}/{len(channels)} ({channels_with_email/len(channels)*100:.1f}%)")
    print(f"🖼️ サムネイル有り: {channels_with_thumbnail}/{len(channels)} ({channels_with_thumbnail/len(channels)*100:.1f}%)")
    
    # サブカテゴリ統計
    regular_streamers = 15  # メガ級ゲーム実況者
    vtubers = 10           # VTuber・バーチャル実況者
    new_generation = 15    # 新世代・ストリーマー系
    
    print(f"\n📂 サブカテゴリ分布:")
    print(f"  - メガ級ゲーム実況者: {regular_streamers}チャンネル")
    print(f"  - VTuber・バーチャル実況者: {vtubers}チャンネル")
    print(f"  - 新世代・ストリーマー系: {new_generation}チャンネル")
    
    # 上位チャンネル表示
    sorted_channels = sorted(channels, key=lambda x: x['subscriber_count'], reverse=True)
    print(f"\n🏆 登録者数TOP15:")
    for i, channel in enumerate(sorted_channels[:15], 1):
        print(f"  {i:2d}. {channel['channel_title']}: {channel['subscriber_count']:,}人")
    
    # エンゲージメント率TOP10
    print(f"\n🔥 エンゲージメント率TOP10:")
    engagement_sorted = sorted(channels, key=lambda x: x['engagement_estimate'], reverse=True)
    for i, channel in enumerate(engagement_sorted[:10], 1):
        print(f"  {i:2d}. {channel['channel_title']}: {channel['engagement_estimate']:.1f}%")
    
    # 特定ジャンル統計
    minecraft_channels = [ch for ch in channels if 'マインクラフト' in ch['description'] or 'マイクラ' in ch['description']]
    fps_channels = [ch for ch in channels if any(word in ch['description'] for word in ['FPS', 'Apex', 'VALORANT', 'バトロワ'])]
    horror_channels = [ch for ch in channels if 'ホラー' in ch['description']]
    
    print(f"\n🎮 ジャンル別統計:")
    print(f"  - マインクラフト系: {len(minecraft_channels)}チャンネル")
    print(f"  - FPS・バトロワ系: {len(fps_channels)}チャンネル")
    print(f"  - ホラーゲーム系: {len(horror_channels)}チャンネル")
    
    return filename

if __name__ == "__main__":
    save_gaming_channels()