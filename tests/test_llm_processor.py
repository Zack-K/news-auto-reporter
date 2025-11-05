import pytest
from unittest.mock import MagicMock, patch
import os
from src.llm_processor import (
    initialize_gemini,
    is_foreign_language,
    translate_and_summarize_with_gemini,
    categorize_article_with_gemini,
    select_and_summarize_articles_with_gemini,
    generate_closing_comment_with_gemini,
)


# pytest fixture for mocking os.environ
@pytest.fixture
def clear_google_api_key(monkeypatch):
    """GOOGLE_API_KEY環境変数をクリアするフィクスチャ"""
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)


@pytest.fixture
def set_google_api_key(monkeypatch):
    """GOOGLE_API_KEY環境変数を設定するフィクスチャ"""
    monkeypatch.setenv("GOOGLE_API_KEY", "test_key")


# pytest fixture for mocking langdetect.detect
@pytest.fixture
def mock_lang_detect(mocker):
    """src.llm_processor.detectをモックするフィクスチャ"""
    return mocker.patch("src.llm_processor.detect")


# pytest fixture for mocking google.generativeai.GenerativeModel
@pytest.fixture
def mock_generative_model(mocker):
    """google.generativeai.GenerativeModelをモックするフィクスチャ"""
    mock_model_class = mocker.patch("google.generativeai.GenerativeModel")
    mock_model_instance = MagicMock()
    mock_model_class.return_value = mock_model_instance
    return mock_model_instance


# test_initialize_gemini
def test_initialize_gemini_no_api_key(clear_google_api_key):
    """GOOGLE_API_KEYが設定されていない場合にValueErrorが送出されることをテスト"""
    with pytest.raises(
        ValueError, match="GOOGLE_API_KEY 環境変数が設定されていません。"
    ):
        initialize_gemini()


@patch("google.generativeai.configure")
def test_initialize_gemini_with_api_key(mock_genai_configure, set_google_api_key):
    """GOOGLE_API_KEYが設定されている場合にgenai.configureが呼び出されることをテスト"""
    initialize_gemini()
    mock_genai_configure.assert_called_once_with(api_key="test_key")


# test_is_foreign_language
def test_is_foreign_language_japanese(mock_lang_detect):
    """日本語テキストが与えられた場合にFalseを返すことをテスト"""
    mock_lang_detect.return_value = "ja"
    text = "これは日本語のテキストです。"
    assert is_foreign_language(text) is False
    mock_lang_detect.assert_called_once_with(text)


def test_is_foreign_language_english(mock_lang_detect):
    """英語テキストが与えられた場合にTrueを返すことをテスト"""
    mock_lang_detect.return_value = "en"
    text = "This is an English text."
    assert is_foreign_language(text) is True
    mock_lang_detect.assert_called_once_with(text)


def test_is_foreign_language_unknown(mock_lang_detect):
    """言語検出が困難なテキストが与えられた場合にTrueを返すことをテスト"""
    mock_lang_detect.side_effect = Exception("Language detection failed")
    text = "abc"
    assert is_foreign_language(text) is True
    mock_lang_detect.assert_called_once_with(text)


# test_translate_and_summarize_with_gemini
def test_translate_and_summarize_with_gemini_success(mock_generative_model):
    """
    translate_and_summarize_with_geminiの正常系テスト
    """
    # LLMからの正常な応答をモック
    llm_response_text = """
    ```json
    {
      "summary": "これはテストの要約です。約200文字を目標とします。データサイエンスの初学者にも分かりやすいように、具体例を交えて説明します。",
      "points": ["ポイント1", "ポイント2", "ポイント3"]
    }
    ```
    """
    mock_generative_model.generate_content.return_value.text = llm_response_text

    text_to_process = "This is a test article in English."
    result = translate_and_summarize_with_gemini(text_to_process)

    assert "summary" in result
    assert "points" in result
    assert (
        result["summary"]
        == "これはテストの要約です。約200文字を目標とします。データサイエンスの初学者にも分かりやすいように、具体例を交えて説明します。"
    )
    assert result["points"] == ["ポイント1", "ポイント2", "ポイント3"]
    assert len(result["summary"]) <= 200  # 要約が200文字以下であることを確認
    mock_generative_model.generate_content.assert_called_once()


def test_translate_and_summarize_with_gemini_invalid_json(mock_generative_model):
    """
    LLMからの応答が不正なJSON文字列の場合の異常系テスト
    """
    # LLMからの不正なJSON応答をモック
    llm_response_text = "これは不正なJSON文字列です。ただのテキストです。"
    mock_generative_model.generate_content.return_value.text = llm_response_text

    text_to_process = "This is a test article."
    result = translate_and_summarize_with_gemini(text_to_process)

    assert "summary" in result
    assert "points" in result
    assert result["summary"] == llm_response_text.strip()
    assert result["points"] == []
    mock_generative_model.generate_content.assert_called_once()


def test_translate_and_summarize_with_gemini_missing_keys(mock_generative_model):
    """
    LLMからの応答がJSON形式だが、期待されるキーが含まれていない場合の異常系テスト
    """
    # LLMからのキーが欠落したJSON応答をモック
    llm_response_text = """
    ```json
    {
      "summary_only": "要約のみの応答です。"
    }
    ```
    """
    mock_generative_model.generate_content.return_value.text = llm_response_text

    text_to_process = "This is a test article."
    result = translate_and_summarize_with_gemini(text_to_process)

    assert "summary" in result
    assert "points" in result
    assert result["summary"] == ""  # 期待されるキーがないため空文字列
    assert result["points"] == []
    mock_generative_model.generate_content.assert_called_once()


def test_translate_and_summarize_with_gemini_api_error(mock_generative_model):
    """
    Gemini API呼び出し中にエラーが発生した場合の異常系テスト
    """
    # API呼び出しで例外を発生させるようにモック
    mock_generative_model.generate_content.side_effect = Exception("Gemini API Error")

    text_to_process = "This is a test article."
    result = translate_and_summarize_with_gemini(text_to_process)

    assert "summary" in result
    assert "points" in result
    assert "翻訳と要約に失敗しました" in result["summary"]
    assert result["points"] == []
    mock_generative_model.generate_content.assert_called_once()


# test_categorize_article_with_gemini
def test_categorize_article_with_gemini_success(mock_generative_model):
    """
    categorize_article_with_geminiの正常系テスト
    """
    # LLMからの正常な応答をモック
    mock_generative_model.generate_content.return_value.text = "データサイエンス"

    title = "データサイエンスの最新トレンド"
    summary = "データ分析に関する記事の要約"
    result = categorize_article_with_gemini(title, summary)

    assert result == "データサイエンス"
    mock_generative_model.generate_content.assert_called_once()


def test_categorize_article_with_gemini_unknown_category(mock_generative_model):
    """
    LLMが定義外のカテゴリ名を返した場合の異常系テスト
    """
    # LLMからの定義外カテゴリ応答をモック
    mock_generative_model.generate_content.return_value.text = "未知のカテゴリ"

    title = "未知のトピック"
    summary = "カテゴリ不明な記事の要約"
    result = categorize_article_with_gemini(title, summary)

    assert result == "その他"
    mock_generative_model.generate_content.assert_called_once()


def test_categorize_article_with_gemini_api_error(mock_generative_model):
    """
    Gemini API呼び出し中にエラーが発生した場合の異常系テスト
    """
    # API呼び出しで例外を発生させるようにモック
    mock_generative_model.generate_content.side_effect = Exception("Gemini API Error")

    title = "エラー発生記事"
    summary = "エラー発生時の記事要約"
    result = categorize_article_with_gemini(title, summary)

    assert result == "その他"
    mock_generative_model.generate_content.assert_called_once()


# test_select_and_summarize_articles_with_gemini
def test_select_and_summarize_articles_with_gemini_success(mock_generative_model):
    """
    select_and_summarize_articles_with_geminiの正常系テスト
    """
    # LLMからの正常な応答をモック
    llm_response_text = """
    ```json
    [
      {
        "title": "Test Article 1",
        "summary": "記事Aの要約",
        "category": "データサイエンス",
        "points": ["A1", "A2", "A3"]
      },
      {
        "title": "Test Article 2",
        "summary": "記事Bの要約",
        "category": "データサイエンス",
        "points": ["B1", "B2", "B3"]
      }
    ]
    ```
    """
    mock_generative_model.generate_content.return_value.text = llm_response_text

    articles = [
        {
            "title": "Test Article 1",
            "url": "http://example.com/a",
            "summary": "記事Aの要約",
            "category": "データサイエンス",
        },
        {
            "title": "Test Article 2",
            "url": "http://example.com/b",
            "summary": "記事Bの要約",
            "category": "データサイエンス",
        },
        {
            "title": "記事C",
            "url": "http://example.com/c",
            "summary": "記事Cの要約",
            "category": "人工知能",
        },
    ]
    categories = ["データサイエンス", "人工知能"]
    result = select_and_summarize_articles_with_gemini(articles, categories)

    assert len(result) == 2
    assert result[0]["title"] == "Test Article 1"
    assert result[0]["url"] == "http://example.com/a"
    assert result[0]["points"] == ["A1", "A2", "A3"]
    assert result[1]["title"] == "Test Article 2"
    assert result[1]["url"] == "http://example.com/b"
    assert result[1]["points"] == ["B1", "B2", "B3"]
    assert mock_generative_model.generate_content.call_count == len(categories)


def test_select_and_summarize_articles_with_gemini_invalid_json(mock_generative_model):
    """
    LLMからの応答が不正なJSONの場合の異常系テスト
    """
    # LLMからの不正なJSON応答をモック
    llm_response_text = "これは不正なJSON文字列です。"
    mock_generative_model.generate_content.return_value.text = llm_response_text

    articles = [
        {
            "title": "記事A",
            "url": "http://example.com/a",
            "summary": "記事Aの要約",
            "category": "データサイエンス",
        },
    ]
    categories = ["データサイエンス"]
    result = select_and_summarize_articles_with_gemini(articles, categories)

    assert len(result) == 0  # 不正なJSONの場合は空リストが返される
    mock_generative_model.generate_content.assert_called_once()


def test_select_and_summarize_articles_with_gemini_api_error(mock_generative_model):
    """
    Gemini API呼び出し中にエラーが発生した場合の異常系テスト
    """
    # API呼び出しで例外を発生させるようにモック
    mock_generative_model.generate_content.side_effect = Exception("Gemini API Error")

    articles = [
        {
            "title": "記事A",
            "url": "http://example.com/a",
            "summary": "記事Aの要約",
            "category": "データサイエンス",
        },
    ]
    categories = ["データサイエンス"]
    result = select_and_summarize_articles_with_gemini(articles, categories)

    assert len(result) == 0  # エラー時は空リストが返される
    mock_generative_model.generate_content.assert_called_once()


@patch("builtins.print")  # print関数をモック
def test_select_and_summarize_articles_with_gemini_missing_original_article(
    mock_print, mock_generative_model
):
    """
    選定された記事のタイトルが元記事に存在しない場合、警告が出力されること
    """
    # LLMからの応答で、元記事に存在しないタイトルを含むものをモック
    llm_response_text = """
    ```json
    [
      {
        "title": "存在しない記事",
        "summary": "存在しない記事の要約",
        "category": "データサイエンス",
        "points": ["X1", "X2", "X3"]
      }
    ]
    ```
    """
    mock_generative_model.generate_content.return_value.text = llm_response_text

    articles = [
        {
            "title": "記事A",
            "url": "http://example.com/a",
            "summary": "記事Aの要約",
            "category": "データサイエンス",
        },
    ]
    categories = ["データサイエンス"]
    result = select_and_summarize_articles_with_gemini(articles, categories)

    assert len(result) == 0  # 存在しない記事は選定されない
    assert mock_generative_model.generate_content.call_count == len(categories)


# test_generate_closing_comment_with_gemini
def test_generate_closing_comment_with_gemini_success(mock_generative_model):
    """
    generate_closing_comment_with_geminiの正常系テスト
    """
    # LLMからの正常な応答をモック
    llm_response_text = "今日のAIニュースレポートはいかがでしたか？ぜひコミュニティで感想や意見を共有し、議論を深めましょう！"
    mock_generative_model.generate_content.return_value.text = llm_response_text

    articles = [
        {"title": "記事A", "category": "データサイエンス"},
        {"title": "記事B", "category": "人工知能"},
    ]
    result = generate_closing_comment_with_gemini(articles)

    assert result == llm_response_text
    assert len(result) <= 100  # クロージングコメントが100文字以下であることを確認
    mock_generative_model.generate_content.assert_called_once()


def test_generate_closing_comment_with_gemini_api_error(mock_generative_model):
    """
    Gemini API呼び出し中にエラーが発生した場合の異常系テスト
    """
    # API呼び出しで例外を発生させるようにモック
    mock_generative_model.generate_content.side_effect = Exception("Gemini API Error")

    articles = [
        {"title": "記事A", "category": "データサイエンス"},
    ]
    result = generate_closing_comment_with_gemini(articles)

    assert (
        "今日のAIニュースレポートはいかがでしたか？" in result
    )  # フォールバックコメント
    mock_generative_model.generate_content.assert_called_once()



