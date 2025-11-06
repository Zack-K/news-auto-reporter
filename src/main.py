import os
from datetime import datetime
from dotenv import load_dotenv

# 他のスクリプトから関数をインポート
from .rss_single_fetch import fetch_all_entries
from .write_to_notion import (
    create_notion_report_page,
    ensure_notion_database_properties,
)
from notion_client import Client
from .llm_processor import (
    initialize_gemini,
    translate_and_summarize_with_gemini,
    is_foreign_language,
    categorize_article_with_gemini,
    select_and_summarize_articles_with_gemini,
    generate_closing_comment_with_gemini,
    generate_image_keywords_with_gemini,
    search_image_from_unsplash,
)
from .send_slack_message import send_slack_message
from .utils import remove_html_tags

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

    print(f"[{datetime.now()}] --- 1. AIニュースの収集 開始 ---")  # 追加
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
    print(f"[{datetime.now()}] --- 1. AIニュースの収集 終了 ---")

    print(
        f"[{datetime.now()}] --- 2. ニュースの翻訳と要約、カテゴリ分類、選定 開始 ---"
    )
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
        # 記事タイトルからHTMLタグを除去
        article["title"] = remove_html_tags(article["title"])

        print(f"Processing article: {article['title']}")

        llm_result = {"summary": article["summary"], "points": [], "comment": ""}

        # 言語検出と翻訳・要約・ポイント・コメント生成
        if is_foreign_language(article["summary"]):
            print(f"  - 記事を翻訳・要約・ポイント・コメント生成中: {article['title']}")
            llm_result = translate_and_summarize_with_gemini(article["summary"])
            article["summary"] = remove_html_tags(llm_result["summary"])
            article["points"] = llm_result["points"]
            # article["comment"] = llm_result["comment"]
        else:
            print(f"  - 記事は日本語であるため翻訳はスキップ: {article['title']}")
            # 日本語記事でもポイントとコメントを生成
            llm_result = translate_and_summarize_with_gemini(article["summary"])
            article["summary"] = remove_html_tags(llm_result["summary"])
            article["points"] = llm_result["points"]
            # article["comment"] = llm_result["comment"]

        # カテゴリ分類
        predicted_category = categorize_article_with_gemini(
            article["title"], article["summary"]
        )
        article["category"] = predicted_category

        processed_articles_with_llm_info.append(article)

    print(
        f"[{datetime.now()}] --- 2. ニュースの翻訳と要約、カテゴリ分類、選定 終了 ---"
    )

    print(f"[{datetime.now()}] --- 3. LLMによる記事選定と絞り込み 開始 ---")
    # 3. LLMによる記事選定と絞り込み
    final_articles_for_report = select_and_summarize_articles_with_gemini(
        processed_articles_with_llm_info, categories
    )

    if not final_articles_for_report:
        print("No articles selected for the report. Exiting.")
        return

    # 追加: 選定されたすべての記事に対してUnsplashから画像を検索・取得
    print(f"[{datetime.now()}] --- 3.5. Unsplashからの画像取得 開始 ---")
    for article in final_articles_for_report:
        if not article.get("image_url"):  # image_urlがまだ設定されていない場合のみ
            print(
                f"  - 画像URLが見つかりません。LLMでキーワード生成後、Unsplashで検索します: {article['title']}"
            )
            image_keywords = generate_image_keywords_with_gemini(
                article["title"], article["summary"], article["category"]
            )
            if image_keywords:
                image_url = search_image_from_unsplash(image_keywords)
                if image_url:
                    article["image_url"] = image_url
                    print(f"  - Unsplashから画像URLを取得しました: {image_url}")
                else:
                    print(
                        f"  - Unsplashでキーワード '{image_keywords}' に一致する画像が見つかりませんでした。"
                    )
            else:
                print("  - LLMで画像キーワードを生成できませんでした。")
    print(f"[{datetime.now()}] --- 3.5. Unsplashからの画像取得 終了 ---")

    print(f"[{datetime.now()}] --- Notionレポートの作成 開始 ---")

    notion_api_key = os.environ.get("NOTION_API_KEY")
    if not notion_api_key:
        print(
            "エラー: NOTION_API_KEY 環境変数が設定されていません。Notion APIキーを設定してください。"
        )
        return

    notion_database_id = os.environ.get("NOTION_DATABASE_ID")
    if not notion_database_id:
        print(
            "エラー: NOTION_DATABASE_ID 環境変数が設定されていません。NotionデータベースIDを設定してください。"
        )
        return

    notion = Client(auth=notion_api_key, notion_version="2022-06-28")
    if not ensure_notion_database_properties(notion, notion_database_id):
        print(
            "エラー: Notionデータベースのプロパティの準備に失敗しました。Notionページ作成をスキップします。"
        )
        return

    print("Creating Notion report page...")
    # create_notion_report_page 関数呼び出し時に、記事のimage_urlがカバー画像として利用されることを想定
    notion_report_url = create_notion_report_page(
        notion,
        final_articles_for_report,
        cover_image_url=final_articles_for_report[0].get("image_url"),
    )
    print(f"[{datetime.now()}] --- Notionレポートの作成 終了 ---")

    print(f"[{datetime.now()}] --- 4. Slack通知メッセージの作成と送信 開始 ---")
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
    print(f"[{datetime.now()}] --- 4. Slack通知メッセージの作成と送信 終了 ---")


if __name__ == "__main__":
    main()
