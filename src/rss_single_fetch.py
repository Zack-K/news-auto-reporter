# rss_single_fetch.py
import requests
import feedparser
from datetime import datetime


def fetch_latest_entry(url: str):
    """
    RSSフィードから最新記事1件を取得してリスト形式で返す
    """
    try:
        response = requests.get(
            url, timeout=10, headers={"User-Agent": "RSSFetcher/1.0"}
        )
        response.raise_for_status()
    except Exception as e:
        print(f"RSS取得エラー: {e}")
        return []

    feed = feedparser.parse(response.content)
    if not feed.entries:
        print("記事が見つかりませんでした。")
        return []

    entry = feed.entries[0]

    article = {
        "category": "最新ニュース",  # 必要に応じて変更可
        "title": entry.title,
        "url": entry.link,
        "summary": entry.get("summary", ""),
    }

    print(f"取得記事: {article['title']} ({article['url']})")
    return [article]  # リスト形式で返す
