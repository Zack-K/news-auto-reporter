# rss_single_fetch.py
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
        # .get() を使用して KeyError を回避
        title = entry.get("title", "タイトルなし")
        link = entry.get("link", "#")
        summary = entry.get("summary", "")

        article = {
            "title": title,
            "url": link,
            "summary": summary,
        }
        all_articles.append(article)

        print(f"取得記事: {article['title']} ({article['url']})")
    return all_articles
