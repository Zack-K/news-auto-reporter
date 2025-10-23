# llm_processor.py
import os
import google.generativeai as genai
from langdetect import detect, DetectorFactory

# langdetectの決定論的モードを有効にする
DetectorFactory.seed = 0


def initialize_gemini():
    """Gemini APIクライアントを初期化します。"""
    google_api_key = os.environ.get("GOOGLE_API_KEY")
    if not google_api_key:
        raise ValueError("GOOGLE_API_KEY 環境変数が設定されていません。")
    genai.configure(api_key=google_api_key)


def list_available_gemini_models():
    """利用可能なGeminiモデルをリストし、generateContentをサポートするモデル名を出力します。"""
    print("利用可能なGeminiモデル:")
    for m in genai.list_models():
        if "generateContent" in m.supported_generation_methods:
            print(f"  {m.name}")


def is_foreign_language(text: str) -> bool:
    """
    langdetectを使用してテキストが日本語以外であるかを判定する。
    """
    try:
        return detect(text) != "ja"
    except Exception:
        return True  # 検出できない場合は外国語とみなす


def translate_and_summarize_with_gemini(text: str) -> str:
    """
    Gemini-2.5-flashを使用してテキストを日本語に翻訳し、要約する。
    """
    try:
        model = genai.GenerativeModel(
            "models/gemini-2.5-flash"
        )  # gemini-2.5-flashを使用
        prompt = f"""以下の記事の概要を日本語に翻訳し、簡潔に要約してください。

記事の概要:
{text}

日本語での要約:"""
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Gemini API呼び出し中にエラーが発生しました: {e}")
        return f"翻訳と要約に失敗しました: {text}"  # 元のテキストまたはエラーメッセージにフォールバック


def categorize_article_with_gemini(title: str, summary: str) -> str:
    """
    Gemini-2.5-flashを使用して記事をカテゴリ分類する。
    """
    categories = [
        "データサイエンス",
        "データエンジニアリング",
        "データ分析",
        "人工知能",
        "プログラミング",
        "パフォーマンス最適化",
    ]
    category_list = ", ".join(categories)
    try:
        model = genai.GenerativeModel("models/gemini-2.5-flash")
        prompt = f"""以下の記事のタイトルと要約を読み、最も適切なカテゴリを一つ選んでください。
利用可能なカテゴリ: {category_list}

タイトル: {title}
要約: {summary}

選択されたカテゴリ:"""
        response = model.generate_content(prompt)
        # Geminiの応答からカテゴリを抽出する簡単な処理
        # 応答が直接カテゴリ名であることを期待する
        predicted_category = response.text.strip()
        if predicted_category in categories:
            return predicted_category
        else:
            # 予測がカテゴリリストにない場合、デフォルトまたは汎用カテゴリを返す
            return "その他"
    except Exception as e:
        print(f"Gemini API呼び出し中にカテゴリ分類エラーが発生しました: {e}")
        return "その他"  # エラー時はデフォルトカテゴリ
