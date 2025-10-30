# rss_single_fetch.py
import requests
import feedparser
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs
import time


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
                # GoogleのリダイレクトURLから最終的な記事のURLを取得
                # allow_redirects=True はデフォルトだが、明示的に指定
                # 最終的なURLは response.url で取得できる
                initial_response = requests.get(
                    link, timeout=5, headers={"User-Agent": "RSSFetcher/1.0"}, allow_redirects=True
                )
                initial_response.raise_for_status()
                
                # GoogleのリダイレクトURLから最終的な記事のURLを抽出
                parsed_google_url = urlparse(initial_response.url)
                query_params = parse_qs(parsed_google_url.query)
                
                if 'url' in query_params and query_params['url']:
                    final_article_url = query_params['url'][0]
                    print(f"  - Extracted final URL from Google redirect: {final_article_url}") # Debug print
                else:
                    final_article_url = initial_response.url # 'url'パラメータがない場合はそのまま
                    print(f"  - No 'url' param in Google redirect, using: {final_article_url}") # Debug print

                # 最終的な記事のURLからHTMLコンテンツを再取得
                article_content_response = requests.get(
                    final_article_url, timeout=5, headers={"User-Agent": "RSSFetcher/1.0"}
                )
                article_content_response.raise_for_status()
                soup = BeautifulSoup(article_content_response.text, "lxml")
                print(f"  - Final article URL: {final_article_url}") # Debug print

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

        # 3. 記事本文から最初の画像URLを取得する試み (最小限度実装)
        if not image_url and link and link != "#":
            try:
                time.sleep(0.5) # サイトへの負荷軽減のため短い遅延

                # OGP/Twitter Cardの解析で取得した article_content_response と soup を再利用
                # もし article_content_response がエラーで取得できていない場合は、ここで再度取得を試みる
                if 'article_content_response' not in locals() or not article_content_response.ok:
                    # final_article_url が定義されていない場合は、link を使用
                    current_target_url = locals().get('final_article_url', link)
                    article_content_response = requests.get(
                        current_target_url, timeout=5, headers={"User-Agent": "RSSFetcher/1.0"}, allow_redirects=True
                    )
                    article_content_response.raise_for_status()
                    final_article_url = article_content_response.url # 最終的なURLを更新
                    soup = BeautifulSoup(article_content_response.text, "lxml")
                
                # final_article_url が定義されていない場合、ここで定義する
                elif 'final_article_url' not in locals():
                    final_article_url = article_content_response.url

                first_img = soup.find("img")
                if first_img and first_img.get("src"):
                    # 相対パスを絶対パスに変換
                    image_url = urljoin(final_article_url, first_img["src"])
            except Exception as e:
                print(f"記事本文からの画像取得エラー ({link}): {e}")

        article = {
            "title": title,
            "url": link,
            "summary": summary,
            "image_url": image_url,
        }
        all_articles.append(article)

        print(f"取得記事: {article['title']} ({article['url']})")
    return all_articles
