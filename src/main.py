import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()  # .envファイルを読み込む

# 他のスクリプトから関数をインポート
from rss_single_fetch import fetch_latest_entry
from write_to_notion import create_notion_article_page, ensure_notion_database_properties, DATABASE_ID
from notion_client import Client
from llm_processor import initialize_gemini, translate_and_summarize_with_gemini, is_foreign_language, categorize_article_with_gemini
from send_slack_message import send_slack_message

def main():
    # 現在のレポート日付を環境変数として設定
    os.environ["REPORT_DATE"] = datetime.now().strftime("%Y-%m-%d")

    # Gemini APIの初期化
    try:
        initialize_gemini()
    except ValueError as e:
        print(f"エラー: Gemini APIの初期化に失敗しました - {e}")
        return

    # 1. AIニュースの収集
    # 監視したいRSSフィードのURLに置き換えてください
    rss_feed_urls = [
        "https://research.google/blog/rss/",  # Google AI Blog
        "https://openai.com/news/rss.xml",  # OpenAI News
        "https://news.microsoft.com/feed/",  # Microsoft AI Blog (AI関連に絞ることを確認)
        "https://towardsdatascience.com/feed",  # Towards Data Science
    ]

    all_articles = []
    for url in rss_feed_urls:
        print(f"Fetching articles from: {url}")
        articles = fetch_latest_entry(url)
        all_articles.extend(articles)

    if not all_articles:
        print("No articles fetched. Exiting.")
        return

    # 2. ニュースの翻訳と要約、カテゴリ分類
    processed_articles = []
    for article in all_articles:
        print(f"Processing article: {article['title']}")

        # 言語検出と翻訳
        if is_foreign_language(article["summary"]):
            print(f"  - 記事を翻訳・要約中: {article['title']}")
            translated_summary = translate_and_summarize_with_gemini(article["summary"])
            article["summary"] = translated_summary
        else:
            print(f"  - 記事は日本語であるため翻訳はスキップ: {article['title']}")

        # カテゴリ分類
        predicted_category = categorize_article_with_gemini(
            article["title"], article["summary"]
        )
        article["category"] = predicted_category

        processed_articles.append(article)

    notion_api_key = os.environ.get("NOTION_API_KEY")
    if not notion_api_key:
        print("エラー: NOTION_API_KEY 環境変数が設定されていません。Notion APIキーを設定してください。")
        return

    print("Creating Notion pages...")
    notion = Client(auth=notion_api_key)
    if not ensure_notion_database_properties(notion, DATABASE_ID):
        print("エラー: Notionデータベースのプロパティの準備に失敗しました。Notionページ作成をスキップします。")
        return

    notion_article_urls = []
    for article in processed_articles:
        article_page_url = create_notion_article_page(article, notion)
        if article_page_url:
            notion_article_urls.append(article_page_url)

    # Slack通知用のNotionレポートURLは、データベースのURLとするか、作成された記事ページのURLリストとする
    # ここでは、データベースのURLをNotionレポートのメインリンクとして使用する
    notion_report_url = f"https://www.notion.so/{DATABASE_ID.replace('-', '')}" if DATABASE_ID else None

    # 4. Slack通知メッセージの作成と送信
    slack_webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    slack_channel = os.environ.get(
        "SLACK_CHANNEL", "#ai-news"
    )  # 設定されていない場合は#ai-newsをデフォルトとする

    if slack_webhook_url and notion_report_url:
        print("Sending Slack message...")
        send_slack_message(
            slack_webhook_url, slack_channel, notion_report_url, processed_articles, os.environ.get("REPORT_DATE")
        )
    else:
        print(
            "Skipping Slack notification. SLACK_WEBHOOK_URL or Notion report URL not available."
        )
        if not slack_webhook_url:
            print(
                "To enable Slack notifications, please set the SLACK_WEBHOOK_URL environment variable."
            )

if __name__ == "__main__":
    main()
