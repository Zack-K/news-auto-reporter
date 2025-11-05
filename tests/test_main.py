import pytest
from unittest.mock import MagicMock
import os
from datetime import datetime

# テスト対象のmain関数をインポート
from src.main import main


# main関数が依存する外部関数をモックするための準備
@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """環境変数をモックするフィクスチャ"""
    monkeypatch.setitem(os.environ, "GOOGLE_ALERTS_RSS_URLS", "http://example.com/rss")
    monkeypatch.setitem(os.environ, "NOTION_API_KEY", "mock_notion_key")
    monkeypatch.setitem(os.environ, "NOTION_DATABASE_ID", "mock_database_id")
    monkeypatch.setitem(os.environ, "SLACK_WEBHOOK_URL", "http://example.com/slack")
    monkeypatch.setitem(os.environ, "SLACK_CHANNEL", "#test-channel")
    monkeypatch.setitem(os.environ, "UNSPLASH_ACCESS_KEY", "mock_unsplash_key")
    monkeypatch.setitem(os.environ, "REPORT_DATE", datetime.now().strftime("%Y-%m-%d"))


@pytest.fixture
def mock_initialize_gemini(mocker):
    return mocker.patch("src.main.initialize_gemini")


@pytest.fixture
def mock_fetch_all_entries(mocker):
    mock = mocker.patch("src.main.fetch_all_entries")
    mock.return_value = [
        {"title": "Test Article 1", "url": "http://example.com/1", "summary": "Summary 1"},
        {"title": "Test Article 2", "url": "http://example.com/2", "summary": "Summary 2"},
    ]
    return mock


@pytest.fixture
def mock_is_foreign_language(mocker):
    mock = mocker.patch("src.main.is_foreign_language")
    mock.side_effect = [True, False]  # 1つ目は外国語、2つ目は日本語
    return mock


@pytest.fixture
def mock_translate_and_summarize_with_gemini(mocker):
    mock = mocker.patch("src.main.translate_and_summarize_with_gemini")
    mock.side_effect = [
        {"summary": "Translated Summary 1", "points": ["P1", "P2", "P3"]},
        {"summary": "Summary 2", "points": ["P4", "P5", "P6"]},
    ]
    return mock


@pytest.fixture
def mock_categorize_article_with_gemini(mocker):
    mock = mocker.patch("src.main.categorize_article_with_gemini")
    mock.side_effect = ["データサイエンス", "人工知能"]
    return mock


@pytest.fixture
def mock_select_and_summarize_articles_with_gemini(mocker):
    mock = mocker.patch("src.main.select_and_summarize_articles_with_gemini")
    mock.return_value = [
        {"title": "Selected Article 1", "url": "http://example.com/1", "summary": "Translated Summary 1", "category": "データサイエンス", "points": ["P1", "P2", "P3"], "image_url": None},
        {"title": "Selected Article 2", "url": "http://example.com/2", "summary": "Summary 2", "category": "人工知能", "points": ["P4", "P5", "P6"], "image_url": None},
    ]
    return mock


@pytest.fixture
def mock_generate_image_keywords_with_gemini(mocker):
    mock = mocker.patch("src.main.generate_image_keywords_with_gemini")
    mock.return_value = "AI, technology"
    return mock


@pytest.fixture
def mock_search_image_from_unsplash(mocker):
    mock = mocker.patch("src.main.search_image_from_unsplash")
    mock.return_value = "http://unsplash.com/image.jpg"
    return mock


@pytest.fixture
def mock_generate_closing_comment_with_gemini(mocker):
    mock = mocker.patch("src.main.generate_closing_comment_with_gemini")
    mock.return_value = "Closing comment."
    return mock


@pytest.fixture
def mock_ensure_notion_database_properties(mocker):
    mock = mocker.patch("src.main.ensure_notion_database_properties")
    mock.return_value = True
    return mock


@pytest.fixture
def mock_create_notion_report_page(mocker):
    mock = mocker.patch("src.main.create_notion_report_page")
    mock.return_value = "http://notion.so/report"
    return mock


@pytest.fixture
def mock_send_slack_message(mocker):
    mock = mocker.patch("src.main.send_slack_message")
    mock.return_value = True
    return mock


@pytest.fixture
def mock_remove_html_tags(mocker):
    mock = mocker.patch("src.main.remove_html_tags")
    mock.side_effect = lambda x: x  # remove_html_tagsはそのまま返すようにモック
    return mock


@pytest.fixture
def mock_notion_client(mocker):
    return mocker.patch("src.main.Client")  # Notion Clientのモック


def test_main_successful_pipeline(
    mock_initialize_gemini,
    mock_fetch_all_entries,
    mock_is_foreign_language,
    mock_translate_and_summarize_with_gemini,
    mock_categorize_article_with_gemini,
    mock_select_and_summarize_articles_with_gemini,
    mock_generate_image_keywords_with_gemini,
    mock_search_image_from_unsplash,
    mock_generate_closing_comment_with_gemini,
    mock_ensure_notion_database_properties,
    mock_create_notion_report_page,
    mock_send_slack_message,
    mock_remove_html_tags,
    mock_notion_client,
):
    """
    main関数が正常に全パイプラインを実行するケースをテスト
    """
    # main関数を実行
    main()

    # 各関数が期待通りに呼び出されたか検証
    mock_initialize_gemini.assert_called_once()
    mock_fetch_all_entries.assert_called_with("http://example.com/rss")
    assert mock_is_foreign_language.call_count == 2
    assert mock_translate_and_summarize_with_gemini.call_count == 2
    assert mock_categorize_article_with_gemini.call_count == 2
    mock_select_and_summarize_articles_with_gemini.assert_called_once()
    assert mock_generate_image_keywords_with_gemini.call_count == 2  # 2つの記事に対して呼ばれる
    assert mock_search_image_from_unsplash.call_count == 2  # 2つの記事に対して呼ばれる
    mock_generate_closing_comment_with_gemini.assert_called_once()
    mock_ensure_notion_database_properties.assert_called_once()
    mock_create_notion_report_page.assert_called_once_with(
        mock_notion_client.return_value,
        mock_select_and_summarize_articles_with_gemini.return_value,
        cover_image_url="http://unsplash.com/image.jpg"  # 最初の記事のimage_urlが渡される
    )
    mock_send_slack_message.assert_called_once()
    assert mock_remove_html_tags.call_count == 4  # 2つの記事のsummaryと2つの記事のtitleに対して呼ばれる

    # REPORT_DATEが設定されていることを確認
    assert "REPORT_DATE" in os.environ
    assert os.environ["REPORT_DATE"] == datetime.now().strftime("%Y-%m-%d")


# 異常系テストの追加
def test_main_no_rss_urls_env_var(mock_initialize_gemini, mock_fetch_all_entries, monkeypatch, capsys):
    """GOOGLE_ALERTS_RSS_URLS 環境変数が設定されていない場合に早期終了することをテスト"""
    monkeypatch.delitem(os.environ, "GOOGLE_ALERTS_RSS_URLS")
    main()
    captured = capsys.readouterr()
    assert "エラー: GOOGLE_ALERTS_RSS_URLS 環境変数が設定されていません。GoogleアラートのRSSフィードURLを設定してください。" in captured.out
    mock_initialize_gemini.assert_called_once()
    mock_fetch_all_entries.assert_not_called()


def test_main_no_articles_fetched(mock_initialize_gemini, mock_fetch_all_entries, capsys):
    """fetch_all_entriesが空のリストを返した場合に早期終了することをテスト"""
    mock_fetch_all_entries.return_value = []
    main()
    captured = capsys.readouterr()
    assert "No articles fetched. Exiting." in captured.out
    mock_initialize_gemini.assert_called_once()
    mock_fetch_all_entries.assert_called_once()


def test_main_no_articles_selected(
    mock_initialize_gemini, mock_fetch_all_entries, mock_select_and_summarize_articles_with_gemini, capsys
):
    """select_and_summarize_articles_with_geminiが空のリストを返した場合に早期終了することをテスト"""
    mock_fetch_all_entries.return_value = [
        {"title": "Test Article 1", "url": "http://example.com/1", "summary": "Summary 1"}
    ]
    mock_select_and_summarize_articles_with_gemini.return_value = []
    main()
    captured = capsys.readouterr()
    assert "No articles selected for the report. Exiting." in captured.out
    mock_initialize_gemini.assert_called_once()
    mock_fetch_all_entries.assert_called_once()
    mock_select_and_summarize_articles_with_gemini.assert_called_once()


def test_main_notion_db_properties_failure(
    mock_initialize_gemini,
    mock_fetch_all_entries,
    mock_select_and_summarize_articles_with_gemini,
    mock_ensure_notion_database_properties,
    mock_create_notion_report_page,
    capsys,
):
    """Notionデータベースのプロパティ準備に失敗した場合にNotionページ作成がスキップされることをテスト"""
    mock_fetch_all_entries.return_value = [
        {"title": "Test Article 1", "url": "http://example.com/1", "summary": "Summary 1"}
    ]
    mock_select_and_summarize_articles_with_gemini.return_value = [
        {"title": "Selected Article 1", "url": "http://example.com/1", "summary": "Summary 1", "category": "データサイエンス", "points": ["P1", "P2", "P3"], "image_url": None}
    ]
    mock_ensure_notion_database_properties.return_value = False
    main()
    captured = capsys.readouterr()
    assert "エラー: Notionデータベースのプロパティの準備に失敗しました。Notionページ作成をスキップします。" in captured.out
    mock_create_notion_report_page.assert_not_called()


def test_main_no_slack_webhook_url(
    mock_initialize_gemini,
    mock_fetch_all_entries,
    mock_select_and_summarize_articles_with_gemini,
    mock_ensure_notion_database_properties,
    mock_create_notion_report_page,
    mock_send_slack_message,
    monkeypatch,
    capsys,
):
    """SLACK_WEBHOOK_URL が設定されていない場合にSlack通知がスキップされることをテスト"""
    monkeypatch.delitem(os.environ, "SLACK_WEBHOOK_URL")
    mock_fetch_all_entries.return_value = [
        {"title": "Test Article 1", "url": "http://example.com/1", "summary": "Summary 1"}
    ]
    mock_select_and_summarize_articles_with_gemini.return_value = [
        {"title": "Selected Article 1", "url": "http://example.com/1", "summary": "Summary 1", "category": "データサイエンス", "points": ["P1", "P2", "P3"], "image_url": None}
    ]
    mock_ensure_notion_database_properties.return_value = True
    mock_create_notion_report_page.return_value = "http://notion.so/report"
    main()
    captured = capsys.readouterr()
    assert "Skipping Slack notification. SLACK_WEBHOOK_URL or Notion report URL not available." in captured.out
    assert "To enable Slack notifications, please set the SLACK_WEBHOOK_URL environment variable." in captured.out
    mock_send_slack_message.assert_not_called()
