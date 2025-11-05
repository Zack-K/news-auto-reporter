# rss_single_fetch.py
import time
import requests
import feedparser


def fetch_all_entries(url: str):
    """
    RSSフィードから全ての記事を取得してリスト形式で返す
    """
    all_articles = []
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

    for entry in feed.entries:
        title = entry.get("title", "タイトルなし")
        link = entry.get("link", "#")
        summary = entry.get("summary", "")
        image_url = None # image_urlはUnsplashから取得するため、ここではNoneのまま

        article = {
            "title": title,
            "url": link,
            "summary": summary,
            "image_url": image_url,
        }
        all_articles.append(article)

        print(f"取得記事: {article['title']} ({article['url']})")
    return all_articles
