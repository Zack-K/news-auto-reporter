from unittest.mock import patch
from src.rss_single_fetch import fetch_all_entries
import requests


# Mock Response class for requests.get
class MockResponse:
    def __init__(self, content, status_code=200, url="http://example.com/article"):
        self._content = content
        self.status_code = status_code
        self.text = content.decode("utf-8") if isinstance(content, bytes) else content
        self.url = url
        self.ok = status_code == 200

    @property
    def content(self):
        return self._content

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(f"HTTP Error: {self.status_code}")


# Mock feedparser entry
class MockFeedEntry:
    def __init__(
        self, title, link, summary, media_thumbnail=None, enclosures=None, image=None
    ):
        self.title = title
        self.link = link
        self.summary = summary
        if media_thumbnail is not None:
            self.media_thumbnail = media_thumbnail
        if enclosures is not None:
            self.enclosures = enclosures
        if image is not None:
            self.image = image

    def get(self, key, default=None):
        # feedparserのentryオブジェクトのgetメソッドの挙動を模倣
        return getattr(self, key, default)


# Mock feedparser object
class MockFeedParser:
    def __init__(self, entries):
        self.entries = entries


@patch("time.sleep")
@patch("requests.get")
@patch("feedparser.parse")
def test_fetch_all_entries_success_basic(
    mock_feedparser_parse, mock_requests_get, mock_sleep
):
    """
    有効なRSSフィードから記事が正しく取得される基本的なケースをテスト
    """
    # Mock RSS feed content
    mock_rss_content = b"""<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
    <channel>
        <title>Test RSS Feed</title>
        <link>http://example.com/rss</link>
        <item>
            <title>Test Article 1</title>
            <link>http://example.com/article1</link>
            <description>Summary of test article 1.</description>
        </item>
    </channel>
    </rss>"""

    # Mock requests.get for RSS feed
    mock_requests_get.return_value = MockResponse(mock_rss_content)

    # Mock feedparser.parse result
    mock_entry = MockFeedEntry(
        title="Test Article 1",
        link="http://example.com/article1",
        summary="Summary of test article 1.",
    )
    mock_feedparser_parse.return_value = MockFeedParser(entries=[mock_entry])

    # Call the function
    articles = fetch_all_entries("http://example.com/rss")

    # Assertions
    assert len(articles) == 1
    assert articles[0]["title"] == "Test Article 1"
    assert articles[0]["url"] == "http://example.com/article1"
    assert articles[0]["summary"] == "Summary of test article 1."
    assert articles[0]["image_url"] is None

    # Verify requests.get was called for the RSS feed
    mock_requests_get.assert_called_once_with(
        "http://example.com/rss", timeout=10, headers={"User-Agent": "RSSFetcher/1.0"}
    )
    # time.sleepは記事本文のフェッチ時のみに呼び出されるため、ここでは呼び出されない
    mock_sleep.assert_not_called()


@patch("src.rss_single_fetch.requests.get")
@patch("src.rss_single_fetch.feedparser.parse")
def test_fetch_all_entries_invalid_rss_url(mock_feedparser_parse, mock_requests_get):
    """無効なRSSフィードURLが与えられた場合に空のリストが返されることをテスト"""
    mock_requests_get.side_effect = requests.exceptions.RequestException("Invalid URL")
    articles = fetch_all_entries("invalid_url")
    assert articles == []
    mock_requests_get.assert_called_once()
    mock_feedparser_parse.assert_not_called()


@patch("src.rss_single_fetch.requests.get")
@patch("src.rss_single_fetch.feedparser.parse")
def test_fetch_all_entries_empty_feed(mock_feedparser_parse, mock_requests_get):
    """RSSフィードが空の場合に空のリストが返されることをテスト"""
    mock_requests_get.return_value = MockResponse(b"<rss><channel></channel></rss>")
    mock_feedparser_parse.return_value = MockFeedParser(entries=[])
    articles = fetch_all_entries("http://example.com/empty_rss")
    assert articles == []
    mock_requests_get.assert_called_once()
    mock_feedparser_parse.assert_called_once()


@patch("src.rss_single_fetch.requests.get")
@patch("src.rss_single_fetch.feedparser.parse")
def test_fetch_all_entries_network_error(mock_feedparser_parse, mock_requests_get):
    """ネットワークエラー発生時に空のリストが返されることをテスト"""
    mock_requests_get.side_effect = requests.exceptions.ConnectionError(
        "Network is down"
    )
    articles = fetch_all_entries("http://example.com/error_rss")
    assert articles == []
    mock_requests_get.assert_called_once()
    mock_feedparser_parse.assert_not_called()


@patch("src.rss_single_fetch.requests.get")
@patch("src.rss_single_fetch.feedparser.parse")
def test_fetch_all_entries_missing_fields(mock_feedparser_parse, mock_requests_get):
    """記事内にtitle, link, summaryのいずれかが欠けている場合にデフォルト値が設定されることをテスト"""
    mock_rss_content = b"""<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
    <channel>
        <title>Test RSS Feed</title>
        <link>http://example.com/rss</link>
        <item>
            <link>http://example.com/article_no_title</link>
            <summary>Summary of article with no title.</summary>
        </item>
        <item>
            <title>Article with no link</title>
            <summary>Summary of article with no link.</summary>
        </item>
        <item>
            <title>Article with no summary</title>
            <link>http://example.com/article_no_summary</link>
        </item>
    </channel>
    </rss>"""

    mock_requests_get.return_value = MockResponse(mock_rss_content)

    mock_feedparser_parse.return_value = MockFeedParser(
        entries=[
            MockFeedEntry(
                title=None,
                link="http://example.com/article_no_title",
                summary="Summary of article with no title.",
            ),
            MockFeedEntry(
                title="Article with no link",
                link=None,
                summary="Summary of article with no link.",
            ),
            MockFeedEntry(
                title="Article with no summary",
                link="http://example.com/article_no_summary",
                summary=None,
            ),
        ]
    )

    articles = fetch_all_entries("http://example.com/rss")

    assert len(articles) == 3
    assert articles[0]["title"] is None
    assert articles[0]["url"] == "http://example.com/article_no_title"
    assert articles[0]["summary"] == "Summary of article with no title."

    assert articles[1]["title"] == "Article with no link"
    assert articles[1]["url"] is None
    assert articles[1]["summary"] == "Summary of article with no link."

    assert articles[2]["title"] == "Article with no summary"
    assert articles[2]["url"] == "http://example.com/article_no_summary"
    assert articles[2]["summary"] is None


@patch("src.rss_single_fetch.time.sleep")
@patch("src.rss_single_fetch.requests.get")
@patch("src.rss_single_fetch.feedparser.parse")
def test_fetch_all_entries_no_image_url_found(
    mock_feedparser_parse, mock_requests_get, mock_sleep
):
    """画像URLがRSSフィード、OGP/Twitter Card、記事本文のいずれからも取得できない場合のテスト"""
    # Arrange
    article_url = "http://example.com/article_no_image"
    mock_rss_content = f"""<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
    <channel>
        <title>Test RSS Feed</title>
        <link>http://example.com/rss</link>
        <item>
            <title>Article No Image</title>
            <link>{article_url}</link>
            <description>Summary of article with no image.</description>
        </item>
    </channel>
    </rss>"""

    mock_feedparser_parse.return_value = MockFeedParser(
        entries=[
            MockFeedEntry(
                title="Article No Image",
                link=article_url,
                summary="Summary of article with no image.",
                media_thumbnail=[],
                enclosures=[],
                image=None,
            )
        ]
    )

    # requests.get のモック設定
    # 1. RSSフィードの取得
    # 2. 記事コンテンツの取得 (OGP/Twitter Cardも画像なし)
    mock_requests_get.side_effect = [
        MockResponse(mock_rss_content, url="http://example.com/rss"),  # RSSフィード
        MockResponse(
            b"<html><body><p>No image here.</p></body></html>", url=article_url
        ),  # 記事コンテンツ
    ]

    # Act
    articles = fetch_all_entries("http://example.com/rss")

    # Assert
    assert len(articles) == 1
    assert articles[0]["title"] == "Article No Image"
    assert articles[0]["url"] == article_url
    assert articles[0]["image_url"] is None

    # time.sleepは記事本文のフェッチ時のみに呼び出されるため、ここでは呼び出されない
    mock_sleep.assert_not_called()


@patch("src.rss_single_fetch.requests.get")
@patch("src.rss_single_fetch.feedparser.parse")
def test_fetch_all_entries_http_error_on_rss_fetch(
    mock_feedparser_parse, mock_requests_get
):
    """RSSフィード取得時のHTTPエラーハンドリングのテスト"""
    mock_requests_get.side_effect = requests.exceptions.HTTPError("404 Not Found")
    articles = fetch_all_entries("http://example.com/404_rss")
    assert articles == []
    mock_requests_get.assert_called_once()
    mock_feedparser_parse.assert_not_called()


@patch("src.rss_single_fetch.requests.get")
@patch("src.rss_single_fetch.feedparser.parse")
def test_fetch_all_entries_timeout_on_rss_fetch(
    mock_feedparser_parse, mock_requests_get
):
    """RSSフィード取得時のタイムアウトエラーハンドリングのテスト"""
    mock_requests_get.side_effect = requests.exceptions.Timeout("Request timed out")
    articles = fetch_all_entries("http://example.com/timeout_rss")
    assert articles == []
    mock_requests_get.assert_called_once()
    mock_feedparser_parse.assert_not_called()


@patch("src.rss_single_fetch.time.sleep")
@patch("src.rss_single_fetch.requests.get")
@patch("src.rss_single_fetch.feedparser.parse")
def test_fetch_all_entries_http_error_on_article_fetch(
    mock_feedparser_parse, mock_requests_get, mock_sleep
):
    """記事コンテンツ取得時のHTTPエラーハンドリングのテスト"""
    article_url = "http://example.com/article_404"
    mock_rss_content = f"<rss><channel><item><title>Test</title><link>{article_url}</link></item></channel></rss>".encode()

    mock_feedparser_parse.return_value = MockFeedParser(
        entries=[
            MockFeedEntry(
                title="Article 404",
                link=article_url,
                summary="Summary",
                media_thumbnail=[],
                enclosures=[],
                image=None,
            )
        ]
    )

    mock_requests_get.side_effect = [
        MockResponse(mock_rss_content, url="http://example.com/rss"),  # RSSフィード
        requests.exceptions.HTTPError("404 Not Found"),  # 記事コンテンツ取得時にエラー
    ]

    articles = fetch_all_entries("http://example.com/rss")

    assert len(articles) == 1
    assert articles[0]["title"] == "Article 404"
    assert articles[0]["url"] == article_url
    assert articles[0]["image_url"] is None  # エラーのため画像は取得されない
    mock_sleep.assert_not_called() # 記事コンテンツ取得でエラーになるが、sleepは呼ばれない


@patch("src.rss_single_fetch.time.sleep")
@patch("src.rss_single_fetch.requests.get")
@patch("src.rss_single_fetch.feedparser.parse")
def test_fetch_all_entries_timeout_on_article_fetch(
    mock_feedparser_parse, mock_requests_get, mock_sleep
):
    """記事コンテンツ取得時のタイムアウトエラーハンドリングのテスト"""
    article_url = "http://example.com/article_timeout"
    mock_rss_content = f"<rss><channel><item><title>Test</title><link>{article_url}</link></item></channel></rss>".encode()

    mock_feedparser_parse.return_value = MockFeedParser(
        entries=[
            MockFeedEntry(
                title="Article Timeout",
                link=article_url,
                summary="Summary",
                media_thumbnail=[],
                enclosures=[],
                image=None,
            )
        ]
    )

    mock_requests_get.side_effect = [
        MockResponse(mock_rss_content, url="http://example.com/rss"),  # RSSフィード
        requests.exceptions.Timeout(
            "Request timed out"
        ),  # 記事コンテンツ取得時にエラー
    ]

    articles = fetch_all_entries("http://example.com/rss")

    assert len(articles) == 1
    assert articles[0]["title"] == "Article Timeout"
    assert articles[0]["url"] == article_url
    assert articles[0]["image_url"] is None  # エラーのため画像は取得されない
    mock_sleep.assert_not_called() # 記事コンテンツ取得でエラーになるが、sleepは呼ばれない

