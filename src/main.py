import os
from datetime import datetime
from dotenv import load_dotenv
import time # 追加

# 他のスクリプトから関数をインポート
from rss_single_fetch import fetch_all_entries
from write_to_notion import (
    create_notion_report_page,
    ensure_notion_database_properties,
    DATABASE_ID,
)
from notion_client import Client
from llm_processor import (
    initialize_gemini,
    translate_and_summarize_with_gemini,
    is_foreign_language,
    categorize_article_with_gemini,
    select_and_summarize_articles_with_gemini,
    generate_image_keywords_with_gemini,
    search_image_from_unsplash,
    generate_closing_comment_with_gemini,
)
from send_slack_message import send_slack_message

load_dotenv()  # .envファイルを読み込む


def main():
    # 現在のレポート日付を環境変数として設定
    os.environ["REPORT_DATE"] = datetime.now().strftime("%Y-%m-%d")

    # Gemini APIの初期化
    try:
        initialize_gemini()
    except ValueError as e:
        print(f"エラー: Gemini APIの初期化に失敗しました - {e}")
        return

    print(f"[{datetime.now()}] --- 1. AIニュースの収集 開始 ---") # 追加
    # 1. AIニュースの収集
    # GoogleアラートのRSSフィードのURLを環境変数から取得
    google_alerts_rss_urls_str = os.environ.get("GOOGLE_ALERTS_RSS_URLS")
    if not google_alerts_rss_urls_str:
        print(
            "エラー: GOOGLE_ALERTS_RSS_URLS 環境変数が設定されていません。GoogleアラートのRSSフィードURLを設定してください。"
        )
        return
    rss_feed_urls = [
        url.strip() for url in google_alerts_rss_urls_str.split(",") if url.strip()
    ]

    all_articles = []
    for url in rss_feed_urls:
        print(f"Fetching articles from: {url}")
        articles = fetch_all_entries(url)
        all_articles.extend(articles)

    if not all_articles:
        print("No articles fetched. Exiting.")
        return
    print(f"[{datetime.now()}] --- 1. AIニュースの収集 終了 ---") # 追加

    print(f"[{datetime.now()}] --- 2. ニュースの翻訳と要約、カテゴリ分類、選定 開始 ---") # 追加
    # 2. ニュースの翻訳と要約、カテゴリ分類、選定
    categories = [
        "データサイエンス",
        "データエンジニアリング",
        "データ分析",
        "人工知能",
        "プログラミング",
        "パフォーマンス最適化",
    ]

    processed_articles_with_llm_info = []
    for article in all_articles:
        print(f"Processing article: {article['title']}")



        llm_result = {"summary": article["summary"], "points": [], "comment": ""}

        # 言語検出と翻訳・要約・ポイント・コメント生成
        if is_foreign_language(article["summary"]):
            print(f"  - 記事を翻訳・要約・ポイント・コメント生成中: {article['title']}")
            llm_result = translate_and_summarize_with_gemini(article["summary"])
            article["summary"] = llm_result["summary"]
            article["points"] = llm_result["points"]
            # article["comment"] = llm_result["comment"]
        else:
            print(f"  - 記事は日本語であるため翻訳はスキップ: {article['title']}")
            # 日本語記事でもポイントとコメントを生成
            llm_result = translate_and_summarize_with_gemini(article["summary"])
            article["points"] = llm_result["points"]
            # article["comment"] = llm_result["comment"]

        # カテゴリ分類
        predicted_category = categorize_article_with_gemini(
            article["title"], article["summary"]
        )
        article["category"] = predicted_category

        processed_articles_with_llm_info.append(article)

    print(f"[{datetime.now()}] --- 2. ニュースの翻訳と要約、カテゴリ分類、選定 終了 ---") # 追加

    print(f"[{datetime.now()}] --- 3. LLMによる記事選定と絞り込み 開始 ---") # 追加
    # 3. LLMによる記事選定と絞り込み
    final_articles_for_report = select_and_summarize_articles_with_gemini(
        processed_articles_with_llm_info, categories
    )

    if not final_articles_for_report:
        print("No articles selected for the report. Exiting.")
        return
    print(f"[{datetime.now()}] --- 3. LLMによる記事選定と絞り込み 終了 ---") # 追加

    print(f"[{datetime.now()}] --- Notionレポートの作成 開始 ---") # 追加
    # Notionのカバー画像用として、選定された最初の記事に対してUnsplash検索を1回だけ実行
    if final_articles_for_report and not final_articles_for_report[0].get("image_url"):
        first_article = final_articles_for_report[0]
        print(f"  - Notionカバー画像用: 画像URLが見つかりません。LLMでキーワード生成後、Unsplashで検索します: {first_article['title']}")
        image_keywords = generate_image_keywords_with_gemini(first_article["title"], first_article["summary"], first_article["category"]) # category引数を追加
        if image_keywords:
            image_url = search_image_from_unsplash(image_keywords)
            if image_url:
                first_article["image_url"] = image_url
                print(f"  - Notionカバー画像用: Unsplashから画像URLを取得しました: {image_url}")
            else:
                print(f"  - Notionカバー画像用: Unsplashで画像が見つかりませんでした。")
        else:
            print(f"  - Notionカバー画像用: LLMで画像キーワードを生成できませんでした。")

    notion_api_key = os.environ.get("NOTION_API_KEY")
    if not notion_api_key:
        print(
            "エラー: NOTION_API_KEY 環境変数が設定されていません。Notion APIキーを設定してください。"
        )
        return

    notion = Client(auth=notion_api_key)
    if not ensure_notion_database_properties(notion, DATABASE_ID):
        print(
            "エラー: Notionデータベースのプロパティの準備に失敗しました。Notionページ作成をスキップします。"
        )
        return

    print("Creating Notion report page...")
    notion_report_url = create_notion_report_page(notion, final_articles_for_report)
    print(f"[{datetime.now()}] --- Notionレポートの作成 終了 ---") # 追加

    print(f"[{datetime.now()}] --- 4. Slack通知メッセージの作成と送信 開始 ---") # 追加
    # 4. Slack通知メッセージの作成と送信
    slack_webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    slack_channel = os.environ.get(
        "SLACK_CHANNEL", "#ai-news"
    )  # 設定されていない場合は#ai-newsをデフォルトとする

    # クロージングコメントを生成
    closing_comment = generate_closing_comment_with_gemini(final_articles_for_report)

    if slack_webhook_url and notion_report_url:
        print("Sending Slack message...")
        send_slack_message(
            slack_webhook_url,
            slack_channel,
            notion_report_url,
            final_articles_for_report,
            os.environ.get("REPORT_DATE"),
            closing_comment,
        )
    else:
        print(
            "Skipping Slack notification. SLACK_WEBHOOK_URL or Notion report URL not available."
        )
        if not slack_webhook_url:
            print(
                "To enable Slack notifications, please set the SLACK_WEBHOOK_URL environment variable."
            )
    print(f"[{datetime.now()}] --- 4. Slack通知メッセージの作成と送信 終了 ---") # 追加


if __name__ == "__main__":
    main()
