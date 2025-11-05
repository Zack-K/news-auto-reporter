import pytest
import os
from unittest.mock import MagicMock
from notion_client.errors import APIResponseError
from src.write_to_notion import (
    ensure_notion_database_properties,
    create_notion_report_page,
    PROP_NAME,
    PROP_DATE,
    PROP_STATUS,
    PROP_ABSTRACT,
    PROP_URL,
)


@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """環境変数をモックするフィクスチャ"""
    monkeypatch.setenv("NOTION_DATABASE_ID", "test_database_id")
    monkeypatch.setenv("REPORT_DATE", "2023-11-01")
    monkeypatch.setenv("NOTION_PROPERTY_NAME", "Name")
    monkeypatch.setenv("NOTION_PROPERTY_DATE", "Date")
    monkeypatch.setenv("NOTION_PROPERTY_STATUS", "Status")
    monkeypatch.setenv("NOTION_PROPERTY_ABSTRACT", "Abstract")
    monkeypatch.setenv("NOTION_PROPERTY_URL", "URL")


@pytest.fixture
def mock_notion_client(mocker):
    """Notionクライアントをモックするフィクスチャ"""
    mock_notion = mocker.MagicMock()

    return mock_notion


@pytest.fixture
def sample_processed_articles():
    """テスト用の記事データ"""
    return [
        {
            "title": "量子コンピューティングの進展",
            "url": "https://example.com/quantum",
            "summary": "量子コンピューティングの最新動向と将来性についての要約。",
            "points": ["ポイント1", "ポイント2", "ポイント3"],
            "category": "テクノロジー",
            "image_url": "https://example.com/image_quantum.jpg",
        },
        {
            "title": "AIと倫理的問題",
            "url": "https://example.com/ai_ethics",
            "summary": "人工知能の発展に伴う倫理的課題に関する考察。",
            "points": ["ポイントA", "ポイントB", "ポイントC"],
            "category": "AI",
            "image_url": "https://example.com/image_ai.jpg",
        },
        {
            "title": "データプライバシーの重要性",
            "url": "https://example.com/data_privacy",
            "summary": "データプライバシー保護の技術と法規制。",
            "points": ["ポイントX", "ポイントy", "ポイントZ"],
            "category": "データサイエンス",
            "image_url": None,
        },
    ]


@pytest.fixture
def sample_processed_articles_no_image_key():
    """image_urlキーがないテスト用の記事データ"""
    return [
        {
            "title": "量子コンピューティングの進展",
            "url": "https://example.com/quantum",
            "summary": "量子コンピューティングの最新動向と将来性についての要約。",
            "points": ["ポイント1", "ポイント2", "ポイント3"],
            "category": "テクノロジー",
        },
    ]


@pytest.fixture
def sample_processed_articles_empty_image_url():
    """image_urlが空文字列のテスト用の記事データ"""
    return [
        {
            "title": "量子コンピューティングの進展",
            "url": "https://example.com/quantum",
            "summary": "量子コンピューティングの最新動向と将来性についての要約。",
            "points": ["ポイント1", "ポイント2", "ポイント3"],
            "category": "テクノロジー",
            "image_url": "",
        },
    ]


@pytest.fixture
def sample_processed_articles_invalid_image_url():
    """image_urlが不正なURLのテスト用の記事データ"""
    return [
        {
            "title": "量子コンピューティングの進展",
            "url": "https://example.com/quantum",
            "summary": "量子コンピューティングの最新動向と将来性についての要約。",
            "points": ["ポイント1", "ポイント2", "ポイント3"],
            "category": "テクノロジー",
            "image_url": "invalid-url",
        },
    ]


# ensure_notion_database_properties関数のテスト
class TestEnsureNotionDatabaseProperties:
    def test_all_properties_exist_and_match(self, mock_notion_client):
        """すべてのプロパティが存在し、タイプも一致する場合のテスト"""
        mock_notion_client.databases.retrieve.return_value = {
            "properties": {
                PROP_NAME: {"type": "title"},
                PROP_DATE: {"type": "date"},
                PROP_STATUS: {
                    "type": "status",
                    "status": {"options": [{"name": "Published", "color": "green"}]},
                },
                PROP_ABSTRACT: {"type": "rich_text"},
                PROP_URL: {"type": "url"},
            }
        }
        result = ensure_notion_database_properties(
            mock_notion_client, os.environ.get("NOTION_DATABASE_ID")
        )
        assert result is True
        mock_notion_client.databases.update.assert_not_called()

    def test_missing_property_is_added(self, mock_notion_client):
        """不足しているプロパティが追加される場合のテスト"""
        mock_notion_client.databases.retrieve.return_value = {
            "properties": {
                PROP_NAME: {"type": "title"},
                PROP_DATE: {"type": "date"},
                PROP_STATUS: {
                    "type": "status",
                    "status": {"options": [{"name": "Published", "color": "green"}]},
                },
                PROP_URL: {"type": "url"},
            }
        }
        result = ensure_notion_database_properties(
            mock_notion_client, os.environ.get("NOTION_DATABASE_ID")
        )
        assert result is True
        mock_notion_client.databases.update.assert_called_once()
        args, kwargs = mock_notion_client.databases.update.call_args
        assert "properties" in kwargs
        assert PROP_ABSTRACT in kwargs["properties"]
        assert kwargs["properties"][PROP_ABSTRACT]["rich_text"] == {}

    def test_missing_published_option_is_added(self, mock_notion_client):
        """StatusプロパティにPublishedオプションがない場合、追加されるテスト"""
        mock_notion_client.databases.retrieve.return_value = {
            "properties": {
                PROP_NAME: {"type": "title"},
                PROP_DATE: {"type": "date"},
                PROP_STATUS: {
                    "type": "status",
                    "status": {"options": [{"name": "Draft", "color": "red"}]},
                },
                PROP_ABSTRACT: {"type": "rich_text"},
                PROP_URL: {"type": "url"},
            }
        }
        result = ensure_notion_database_properties(
            mock_notion_client, os.environ.get("NOTION_DATABASE_ID")
        )
        assert result is True
        mock_notion_client.databases.update.assert_called_once()
        args, kwargs = mock_notion_client.databases.update.call_args
        status_options = kwargs["properties"][PROP_STATUS]["status"]["options"]
        assert len(status_options) == 2  # 既存のDraftと追加されたPublished
        assert {"name": "Published", "color": "green"} in status_options
        assert {"name": "Draft", "color": "red"} in status_options

    def test_api_error_on_retrieve_object_not_found(self, mock_notion_client):
        """データベース情報取得中にObjectNotFoundエラーが発生した場合のテスト"""
        mock_notion_client.databases.retrieve.side_effect = APIResponseError(
            response=MagicMock(status_code=404),
            code="object_not_found",
            message="Object not found",
        )
        result = ensure_notion_database_properties(
            mock_notion_client, os.environ.get("NOTION_DATABASE_ID")
        )
        assert result is False

    def test_api_error_on_retrieve_unauthorized(self, mock_notion_client):
        """データベース情報取得中にUnauthorizedエラーが発生した場合のテスト"""
        mock_notion_client.databases.retrieve.side_effect = APIResponseError(
            response=MagicMock(status_code=401),
            code="unauthorized",
            message="Unauthorized",
        )
        result = ensure_notion_database_properties(
            mock_notion_client, os.environ.get("NOTION_DATABASE_ID")
        )
        assert result is False

    def test_api_error_on_retrieve_generic_exception(self, mock_notion_client):
        """データベース情報取得中に予期せぬエラーが発生した場合のテスト"""
        mock_notion_client.databases.retrieve.side_effect = Exception(
            "Some unexpected error"
        )
        result = ensure_notion_database_properties(
            mock_notion_client, os.environ.get("NOTION_DATABASE_ID")
        )
        assert result is False

    def test_property_type_mismatch(self, mock_notion_client):
        """プロパティのタイプが既存のものと一致しない場合のテスト"""
        mock_notion_client.databases.retrieve.return_value = {
            "properties": {
                PROP_NAME: {"type": "title"},
                PROP_DATE: {"type": "text"},  # 意図的にタイプを不一致にする
                PROP_STATUS: {
                    "type": "status",
                    "status": {"options": [{"name": "Published", "color": "green"}]},
                },
                PROP_ABSTRACT: {"type": "rich_text"},
                PROP_URL: {"type": "url"},
            }
        }
        result = ensure_notion_database_properties(
            mock_notion_client, os.environ.get("NOTION_DATABASE_ID")
        )
        assert result is False
        mock_notion_client.databases.update.assert_not_called()


# create_notion_report_page関数のテスト
class TestCreateNotionReportPage:
    def test_create_page_success_with_articles(
        self, mock_notion_client, sample_processed_articles
    ):
        """記事データを含むNotionページが正常に作成される場合のテスト"""
        expected_url = "https://notion.so/test_page_url"
        mock_notion_client.pages.create.return_value = {"url": expected_url}

        # cover_image_urlを明示的に渡すように修正
        result = create_notion_report_page(
            mock_notion_client,
            sample_processed_articles,
            cover_image_url="https://example.com/mock_cover.jpg",
        )
        assert result == expected_url
        mock_notion_client.pages.create.assert_called_once()
        args, kwargs = mock_notion_client.pages.create.call_args

        # プロパティの確認
        assert kwargs["parent"]["database_id"] == os.environ.get("NOTION_DATABASE_ID")
        assert (
            kwargs["properties"][PROP_NAME]["title"][0]["text"]["content"]
            == "AIニュースレポート - 2023-11-01"
        )
        assert kwargs["properties"][PROP_DATE]["date"]["start"] == "2023-11-01"
        assert kwargs["properties"][PROP_STATUS]["status"]["name"] == "Published"

        # カバー画像の確認
        assert kwargs["cover"]["type"] == "external"
        assert (
            kwargs["cover"]["external"]["url"] == "https://example.com/mock_cover.jpg"
        )

        # 子要素の構成を確認 (一部抜粋)
        children = kwargs["children"]
        assert len(children) > 0
        assert (
            children[0]["paragraph"]["rich_text"][0]["text"]["content"]
            == "データサイエンス、データエンジニアリング、データ分析の学習者向けに、AIの最新ニュースを毎日お届けします。"
        )
        assert any(
            c.get("heading_2", {})
            .get("rich_text", [{}])[0]
            .get("text", {})
            .get("content")
            == "【テクノロジー】"
            for c in children
        )
        assert any(
            c.get("heading_3", {})
            .get("rich_text", [{}])[0]
            .get("text", {})
            .get("content")
            == "量子コンピューティングの進展"
            for c in children
        )

    def test_create_page_success_empty_articles(self, mock_notion_client):
        """記事データが空の場合でもNotionページが正常に作成される場合のテスト"""
        expected_url = "https://notion.so/test_empty_page_url"
        mock_notion_client.pages.create.return_value = {"url": expected_url}

        # cover_image_url=Noneを明示的に渡す
        result = create_notion_report_page(mock_notion_client, [], cover_image_url=None)
        assert result == expected_url
        mock_notion_client.pages.create.assert_called_once()
        args, kwargs = mock_notion_client.pages.create.call_args

        assert (
            kwargs["cover"] is None
        )  # cover_image_urlがNoneのためカバー画像は設定されない

        # 子要素の構成を確認 (導入文と区切り線のみ)
        children = kwargs["children"]
        assert len(children) == 2  # 導入文とdividerのみ
        assert (
            children[0]["paragraph"]["rich_text"][0]["text"]["content"]
            == "データサイエンス、データエンジニアリング、データ分析の学習者向けに、AIの最新ニュースを毎日お届けします。"
        )

    def test_create_page_success_no_image_url(
        self, mock_notion_client, sample_processed_articles
    ):
        """記事データにimage_urlがない場合のテスト (cover_image_url=Noneで呼び出す)"""
        expected_url = "https://notion.so/test_no_image_page_url"
        mock_notion_client.pages.create.return_value = {"url": expected_url}

        # 最初の記事のimage_urlをNoneに設定し直す (このテストでは不要になるが、fixtureの整合性のため残す)
        articles_no_image = sample_processed_articles.copy()
        articles_no_image[0]["image_url"] = None

        # cover_image_url=Noneを明示的に渡す
        result = create_notion_report_page(
            mock_notion_client, articles_no_image, cover_image_url=None
        )
        assert result == expected_url
        mock_notion_client.pages.create.assert_called_once()
        args, kwargs = mock_notion_client.pages.create.call_args

        assert (
            kwargs["cover"] is None
        )  # cover_image_urlがNoneのためカバー画像は設定されない

    def test_create_page_success_no_image_key(
        self, mock_notion_client, sample_processed_articles_no_image_key
    ):
        """記事データにimage_urlキー自体がない場合のテスト (cover_image_url=Noneで呼び出す)"""
        expected_url = "https://notion.so/test_no_image_key_page_url"
        mock_notion_client.pages.create.return_value = {"url": expected_url}

        # cover_image_url=Noneを明示的に渡す
        result = create_notion_report_page(
            mock_notion_client,
            sample_processed_articles_no_image_key,
            cover_image_url=None,
        )
        assert result == expected_url
        mock_notion_client.pages.create.assert_called_once()
        args, kwargs = mock_notion_client.pages.create.call_args

        assert (
            kwargs["cover"] is None
        )  # cover_image_urlがNoneのためカバー画像は設定されない

    def test_create_page_success_empty_image_url(
        self, mock_notion_client, sample_processed_articles_empty_image_url
    ):
        """記事データにimage_urlが空文字列の場合のテスト (cover_image_url=Noneで呼び出す)"""
        expected_url = "https://notion.so/test_empty_image_url_page_url"
        mock_notion_client.pages.create.return_value = {"url": expected_url}

        # cover_image_url=Noneを明示的に渡す
        result = create_notion_report_page(
            mock_notion_client,
            sample_processed_articles_empty_image_url,
            cover_image_url=None,
        )
        assert result == expected_url
        mock_notion_client.pages.create.assert_called_once()
        args, kwargs = mock_notion_client.pages.create.call_args

        assert (
            kwargs["cover"] is None
        )  # cover_image_urlがNoneのためカバー画像は設定されない

    def test_create_page_success_invalid_image_url(
        self, mock_notion_client, sample_processed_articles_invalid_image_url
    ):
        """記事データにimage_urlが不正なURLの場合のテスト (cover_image_url=Noneで呼び出す)"""
        expected_url = "https://notion.so/test_invalid_image_url_page_url"
        mock_notion_client.pages.create.return_value = {"url": expected_url}

        # cover_image_url=Noneを明示的に渡す
        result = create_notion_report_page(
            mock_notion_client,
            sample_processed_articles_invalid_image_url,
            cover_image_url=None,
        )
        assert result == expected_url
        mock_notion_client.pages.create.assert_called_once()
        args, kwargs = mock_notion_client.pages.create.call_args

        assert (
            kwargs["cover"] is None
        )  # cover_image_urlがNoneのためカバー画像は設定されない

    def test_create_page_success_with_mocked_cover_image_url(self, mock_notion_client):
        """モックされた有効なcover_image_urlでNotionページが正常に作成される場合のテスト"""
        expected_url = "https://notion.so/test_mocked_cover_page_url"
        mock_notion_client.pages.create.return_value = {"url": expected_url}
        mock_cover_url = "https://unsplash.com/photos/mock_image.jpg"

        result = create_notion_report_page(
            mock_notion_client, [], cover_image_url=mock_cover_url
        )
        assert result == expected_url
        mock_notion_client.pages.create.assert_called_once()
        args, kwargs = mock_notion_client.pages.create.call_args

        assert kwargs["cover"]["type"] == "external"
        assert kwargs["cover"]["external"]["url"] == mock_cover_url

    def test_create_page_failure_with_invalid_mocked_cover_image_url(
        self, mock_notion_client
    ):
        """モックされた不正なcover_image_urlでNotionページ作成が失敗する場合のテスト"""
        mock_notion_client.pages.create.side_effect = APIResponseError(
            response=MagicMock(status_code=400),
            code="validation_error",
            message="Invalid URL for cover image",
        )
        invalid_mock_cover_url = "invalid-unsplash-url"

        result = create_notion_report_page(
            mock_notion_client, [], cover_image_url=invalid_mock_cover_url
        )
        assert result is None
        mock_notion_client.pages.create.assert_called_once()

    def test_api_error_on_create_page_internal_error(
        self, mock_notion_client, sample_processed_articles
    ):
        """ページ作成中にAPIInternalServerErrorが発生した場合のテスト"""
        mock_notion_client.pages.create.side_effect = APIResponseError(
            response=MagicMock(status_code=500),
            code="internal_server_error",
            message="Internal Server Error",
        )
        result = create_notion_report_page(
            mock_notion_client, sample_processed_articles, cover_image_url=None
        )
        assert result is None

    def test_generic_exception_on_create_page(
        self, mock_notion_client, sample_processed_articles
    ):
        """ページ作成中に予期せぬエラーが発生した場合のテスト"""
        mock_notion_client.pages.create.side_effect = Exception(
            "Some unexpected error during page creation"
        )
        result = create_notion_report_page(
            mock_notion_client, sample_processed_articles, cover_image_url=None
        )
        assert result is None
