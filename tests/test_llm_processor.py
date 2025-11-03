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


# test_initialize_gemini
@patch.dict(os.environ, {}, clear=True)  # 環境変数をクリア
def test_initialize_gemini_no_api_key():
    """GOOGLE_API_KEYが設定されていない場合にValueErrorが送出されることをテスト"""
    with pytest.raises(
        ValueError, match="GOOGLE_API_KEY 環境変数が設定されていません。"
    ):
        initialize_gemini()


@patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"})
@patch("google.generativeai.configure")
def test_initialize_gemini_with_api_key(mock_genai_configure):
    """GOOGLE_API_KEYが設定されている場合にgenai.configureが呼び出されることをテスト"""
    initialize_gemini()
    mock_genai_configure.assert_called_once_with(api_key="test_key")


# test_is_foreign_language
@patch("src.llm_processor.detect")  # 修正
def test_is_foreign_language_japanese(mock_detect):
    """日本語テキストが与えられた場合にFalseを返すことをテスト"""
    mock_detect.return_value = "ja"
    assert is_foreign_language("これは日本語のテキストです。") is False
    mock_detect.assert_called_once_with("これは日本語のテキストです。")


@patch("src.llm_processor.detect")  # 修正
def test_is_foreign_language_english(mock_detect):
    """英語テキストが与えられた場合にTrueを返すことをテスト"""
    mock_detect.return_value = "en"
    assert is_foreign_language("This is an English text.") is True
    mock_detect.assert_called_once_with("This is an English text.")


@patch("src.llm_processor.detect")  # 修正
def test_is_foreign_language_unknown(mock_detect):
    """言語検出が困難なテキストが与えられた場合にTrueを返すことをテスト"""
    mock_detect.side_effect = Exception("Language detection failed")
    assert is_foreign_language("abc") is True
    mock_detect.assert_called_once_with("abc")


# Mock for genai.GenerativeModel().generate_content().text
class MockGenerateContentResponse:
    def __init__(self, text):
        self.text = text


@patch("google.generativeai.GenerativeModel")
def test_translate_and_summarize_with_gemini_success(mock_generative_model):
    """
    translate_and_summarize_with_geminiの正常系テスト
    """
    mock_model_instance = MagicMock()
    mock_generative_model.return_value = mock_model_instance

    # LLMからの正常な応答をモック
    llm_response_text = """
    ```json
    {
      "summary": "これはテストの要約です。約200文字を目標とします。データサイエンスの初学者にも分かりやすいように、具体例を交えて説明します。",
      "points": ["ポイント1", "ポイント2", "ポイント3"]
    }
    ```
    """
    mock_model_instance.generate_content.return_value = MockGenerateContentResponse(
        llm_response_text
    )

    text_to_process = "This is a test article in English."
    result = translate_and_summarize_with_gemini(text_to_process)

    assert "summary" in result
    assert "points" in result
    assert (
        result["summary"]
        == "これはテストの要約です。約200文字を目標とします。データサイエンスの初学者にも分かりやすいように、具体例を交えて説明します。"
    )
    assert result["points"] == ["ポイント1", "ポイント2", "ポイント3"]
    assert mock_generative_model.called
    assert mock_model_instance.generate_content.called


@patch("google.generativeai.GenerativeModel")
def test_translate_and_summarize_with_gemini_invalid_json(mock_generative_model):
    """
    LLMからの応答が不正なJSON文字列の場合の異常系テスト
    """
    mock_model_instance = MagicMock()
    mock_generative_model.return_value = mock_model_instance

    # LLMからの不正なJSON応答をモック
    llm_response_text = "これは不正なJSON文字列です。ただのテキストです。"
    mock_model_instance.generate_content.return_value = MockGenerateContentResponse(
        llm_response_text
    )

    text_to_process = "This is a test article."
    result = translate_and_summarize_with_gemini(text_to_process)

    assert "summary" in result
    assert "points" in result
    assert result["summary"] == llm_response_text.strip()
    assert result["points"] == []
    assert mock_generative_model.called
    assert mock_model_instance.generate_content.called


@patch("google.generativeai.GenerativeModel")
def test_translate_and_summarize_with_gemini_missing_keys(mock_generative_model):
    """
    LLMからの応答がJSON形式だが、期待されるキーが含まれていない場合の異常系テスト
    """
    mock_model_instance = MagicMock()
    mock_generative_model.return_value = mock_model_instance

    # LLMからのキーが欠落したJSON応答をモック
    llm_response_text = """
    ```json
    {
      "summary_only": "要約のみの応答です。"
    }
    ```
    """
    mock_model_instance.generate_content.return_value = MockGenerateContentResponse(
        llm_response_text
    )

    text_to_process = "This is a test article."
    result = translate_and_summarize_with_gemini(text_to_process)

    assert "summary" in result
    assert "points" in result
    assert result["summary"] == ""  # 期待されるキーがないため空文字列
    assert result["points"] == []
    assert mock_generative_model.called
    assert mock_model_instance.generate_content.called


@patch("google.generativeai.GenerativeModel")
def test_translate_and_summarize_with_gemini_api_error(mock_generative_model):
    """
    Gemini API呼び出し中にエラーが発生した場合の異常系テスト
    """
    mock_model_instance = MagicMock()
    mock_generative_model.return_value = mock_model_instance

    # API呼び出しで例外を発生させるようにモック
    mock_model_instance.generate_content.side_effect = Exception("Gemini API Error")

    text_to_process = "This is a test article."
    result = translate_and_summarize_with_gemini(text_to_process)

    assert "summary" in result
    assert "points" in result
    assert "翻訳と要約に失敗しました" in result["summary"]
    assert result["points"] == []
    assert mock_generative_model.called
    assert mock_model_instance.generate_content.called


@patch("google.generativeai.GenerativeModel")
def test_categorize_article_with_gemini_success(mock_generative_model):
    """
    categorize_article_with_geminiの正常系テスト
    """
    mock_model_instance = MagicMock()
    mock_generative_model.return_value = mock_model_instance

    # LLMからの正常な応答をモック
    mock_model_instance.generate_content.return_value = MockGenerateContentResponse(
        "データサイエンス"
    )

    title = "データサイエンスの最新トレンド"
    summary = "データ分析に関する記事の要約"
    result = categorize_article_with_gemini(title, summary)

    assert result == "データサイエンス"
    assert mock_generative_model.called
    assert mock_model_instance.generate_content.called


@patch("google.generativeai.GenerativeModel")
def test_categorize_article_with_gemini_unknown_category(mock_generative_model):
    """
    LLMが定義外のカテゴリ名を返した場合の異常系テスト
    """
    mock_model_instance = MagicMock()
    mock_generative_model.return_value = mock_model_instance

    # LLMからの定義外カテゴリ応答をモック
    mock_model_instance.generate_content.return_value = MockGenerateContentResponse(
        "未知のカテゴリ"
    )

    title = "未知のトピック"
    summary = "カテゴリ不明な記事の要約"
    result = categorize_article_with_gemini(title, summary)

    assert result == "その他"
    assert mock_generative_model.called
    assert mock_model_instance.generate_content.called


@patch("google.generativeai.GenerativeModel")
def test_categorize_article_with_gemini_api_error(mock_generative_model):
    """
    Gemini API呼び出し中にエラーが発生した場合の異常系テスト
    """
    mock_model_instance = MagicMock()
    mock_generative_model.return_value = mock_model_instance

    # API呼び出しで例外を発生させるようにモック
    mock_model_instance.generate_content.side_effect = Exception("Gemini API Error")

    title = "エラー発生記事"
    summary = "エラー発生時の記事要約"
    result = categorize_article_with_gemini(title, summary)

    assert result == "その他"
    assert mock_generative_model.called
    assert mock_model_instance.generate_content.called


@patch("google.generativeai.GenerativeModel")
def test_select_and_summarize_articles_with_gemini_success(mock_generative_model):
    """
    select_and_summarize_articles_with_geminiの正常系テスト
    """
    mock_model_instance = MagicMock()
    mock_generative_model.return_value = mock_model_instance

    # LLMからの正常な応答をモック
    llm_response_text = """
    ```json
    [
      {
        "title": "記事A",
        "summary": "記事Aの要約",
        "category": "データサイエンス",
        "points": ["A1", "A2", "A3"]
      },
      {
        "title": "記事B",
        "summary": "記事Bの要約",
        "category": "データサイエンス",
        "points": ["B1", "B2", "B3"]
      }
    ]
    ```
    """
    mock_model_instance.generate_content.return_value = MockGenerateContentResponse(
        llm_response_text
    )

    articles = [
        {
            "title": "記事A",
            "url": "http://example.com/a",
            "summary": "記事Aの要約",
            "category": "データサイエンス",
        },
        {
            "title": "記事B",
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
    assert result[0]["title"] == "記事A"
    assert result[0]["url"] == "http://example.com/a"
    assert result[0]["points"] == ["A1", "A2", "A3"]
    assert result[1]["title"] == "記事B"
    assert result[1]["url"] == "http://example.com/b"
    assert result[1]["points"] == ["B1", "B2", "B3"]
    assert mock_generative_model.called
    assert mock_model_instance.generate_content.called


@patch("google.generativeai.GenerativeModel")
def test_select_and_summarize_articles_with_gemini_invalid_json(mock_generative_model):
    """
    LLMからの応答が不正なJSONの場合の異常系テスト
    """
    mock_model_instance = MagicMock()
    mock_generative_model.return_value = mock_model_instance

    # LLMからの不正なJSON応答をモック
    llm_response_text = "これは不正なJSON文字列です。"
    mock_model_instance.generate_content.return_value = MockGenerateContentResponse(
        llm_response_text
    )

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
    assert mock_generative_model.called
    assert mock_model_instance.generate_content.called


@patch("google.generativeai.GenerativeModel")
def test_select_and_summarize_articles_with_gemini_api_error(mock_generative_model):
    """
    Gemini API呼び出し中にエラーが発生した場合の異常系テスト
    """
    mock_model_instance = MagicMock()
    mock_generative_model.return_value = mock_model_instance

    # API呼び出しで例外を発生させるようにモック
    mock_model_instance.generate_content.side_effect = Exception("Gemini API Error")

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
    assert mock_generative_model.called
    assert mock_model_instance.generate_content.called


@patch("google.generativeai.GenerativeModel")
@patch("builtins.print")  # print関数をモック
def test_select_and_summarize_articles_with_gemini_missing_original_article(
    mock_print, mock_generative_model
):
    """
    選定された記事のタイトルが元記事に存在しない場合、警告が出力されること
    """
    mock_model_instance = MagicMock()
    mock_generative_model.return_value = mock_model_instance

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
    mock_model_instance.generate_content.return_value = MockGenerateContentResponse(
        llm_response_text
    )

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
    mock_print.assert_called_with(
        "警告: 選定された記事 '存在しない記事' の元のURLが見つかりませんでした。"
    )
    assert mock_generative_model.called
    assert mock_model_instance.generate_content.called


@patch("google.generativeai.GenerativeModel")
def test_generate_closing_comment_with_gemini_success(mock_generative_model):
    """
    generate_closing_comment_with_geminiの正常系テスト
    """
    mock_model_instance = MagicMock()
    mock_generative_model.return_value = mock_model_instance

    # LLMからの正常な応答をモック
    llm_response_text = "今日のAIニュースレポートはいかがでしたか？ぜひコミュニティで感想や意見を共有し、議論を深めましょう！"
    mock_model_instance.generate_content.return_value = MockGenerateContentResponse(
        llm_response_text
    )

    articles = [
        {"title": "記事A", "category": "データサイエンス"},
        {"title": "記事B", "category": "人工知能"},
    ]
    result = generate_closing_comment_with_gemini(articles)

    assert result == llm_response_text
    assert mock_generative_model.called
    assert mock_model_instance.generate_content.called


@patch("google.generativeai.GenerativeModel")
def test_generate_closing_comment_with_gemini_api_error(mock_generative_model):
    """
    Gemini API呼び出し中にエラーが発生した場合の異常系テスト
    """
    mock_model_instance = MagicMock()
    mock_generative_model.return_value = mock_model_instance

    # API呼び出しで例外を発生させるようにモック
    mock_model_instance.generate_content.side_effect = Exception("Gemini API Error")

    articles = [
        {"title": "記事A", "category": "データサイエンス"},
    ]
    result = generate_closing_comment_with_gemini(articles)

    assert (
        "今日のAIニュースレポートはいかがでしたか？" in result
    )  # フォールバックコメント
    assert mock_generative_model.called
    assert mock_model_instance.generate_content.called



