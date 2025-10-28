# rss_single_fetch.py
import requests
import feedparser
from bs4 import BeautifulSoup


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
        image_url = None

        # 1. RSSフィードから画像URLを取得する試み
        if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
            image_url = entry.media_thumbnail[0]["url"]
        elif hasattr(entry, "enclosures") and entry.enclosures:
            for enclosure in entry.enclosures:
                if "image" in enclosure.get("type", ""):
                    image_url = enclosure["href"]
                    break
        elif hasattr(entry, "image") and entry.image:
            image_url = entry.image.get("href") or entry.image.get("url")

        # 2. 記事のURLからOGP/Twitter Cardのメタタグを解析して画像URLを取得する試み
        if not image_url and link and link != "#":
            try:
                article_response = requests.get(
                    link, timeout=5, headers={"User-Agent": "RSSFetcher/1.0"}
                )
                article_response.raise_for_status()
                soup = BeautifulSoup(article_response.text, "lxml")

                # OGP画像
                og_image = soup.find("meta", property="og:image")
                if og_image and og_image.get("content"):
                    image_url = og_image["content"]

                # Twitter Card画像
                if not image_url:
                    twitter_image = soup.find("meta", property="twitter:image")
                    if twitter_image and twitter_image.get("content"):
                        image_url = twitter_image["content"]

            except Exception as e:
                print(f"記事ページからの画像取得エラー ({link}): {e}")

        article = {
            "title": title,
            "url": link,
            "summary": summary,
            "image_url": image_url,
        }
        all_articles.append(article)

        print(f"取得記事: {article['title']} ({article['url']})")
    return all_articles
