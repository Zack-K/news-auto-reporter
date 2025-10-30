# llm_processor.py
import os
import google.generativeai as genai
import json
import requests
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


def translate_and_summarize_with_gemini(text: str) -> dict:
    """
    Gemini-2.5-flashを使用してテキストを日本語に翻訳し、要約、初学者向けのポイント、会話を促すコメントをJSON形式で生成する。
    """

    try:
        model = genai.GenerativeModel("models/gemini-2.5-flash")
        prompt = f"""以下の記事の概要を日本語に翻訳し、簡潔に要約してください。さらに、その記事の初学者向けのポイントを3行で、そしてSlackでの会話を促すコメントを1行で生成してください。
    
    記事の概要:
    {text}
    
    出力形式はJSONオブジェクトで、以下のキーを含めてください。
    {{"summary": "[ここに要約]", "points": ["ポイント1", "ポイント2", "ポイント3"], "comment": "[ここにコメント]"}} """
        response = model.generate_content(prompt)
        response_text = response.text.strip()

        # LLMの応答からマークダウンのコードブロックを削除
        if response_text.startswith("```json"):
            response_text = response_text[len("```json") :].strip()
        if response_text.endswith("```"):
            response_text = response_text[: -len("```")].strip()

        try:
            llm_output = json.loads(response_text)
            return {
                "summary": llm_output.get("summary", ""),
                "points": llm_output.get("points", []),
                "comment": llm_output.get("comment", ""),
            }
        except json.JSONDecodeError as e:
            print(
                f"警告: LLM応答のJSONパースに失敗しました: {e}. 応答: {response_text[:200]}..."
            )
            # JSONパースに失敗した場合のフォールバック
            return {"summary": response_text.strip(), "points": [], "comment": ""}
    except Exception as e:
        print(f"Gemini API呼び出し中にエラーが発生しました: {e}")
        return {
            "summary": f"翻訳と要約に失敗しました: {text}",
            "points": [],
            "comment": "",
        }


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


def select_and_summarize_articles_with_gemini(articles: list, categories: list) -> list:
    """
    Gemini-2.5-flashを使用して、カテゴリごとに記事を選定し、最大3記事に絞り込み、
    初学者向けのポイントと会話を促すコメントを生成する。
    """
    selected_articles = []
    model = genai.GenerativeModel("models/gemini-2.5-flash")

    for category in categories:
        category_articles = [a for a in articles if a.get("category") == category]
        if not category_articles:
            continue

        # 各カテゴリから最大3記事を選定
        # ここでは、LLMに選定を依頼するプロンプトを作成
        articles_info = ""
        for i, article in enumerate(category_articles):
            articles_info += f"記事{i + 1} - タイトル: {article['title']}, 要約: {article['summary']}\n"

        prompt = f"""以下の{category}カテゴリの記事の中から、データサイエンス、データエンジニアリング、データ分析の学習者にとって最も有用で、会話のきっかけになりそうな記事を最大3つ選んでください。
選定した各記事について、初学者向けのポイントを3行で、そしてSlackでの会話を促すコメントを1行で生成してください。

記事リスト:
{articles_info}

出力はJSON配列のみとし、前後に余計なテキストを含めないでください。出力形式:
[
  {{
    "title": "選定された記事のタイトル",
    "url": "選定された記事のURL",
    "summary": "選定された記事の要約",
    "category": "{category}",
    "points": ["ポイント1", "ポイント2", "ポイント3"],
    "comment": "会話を促すコメント"
  }},
  ... (最大3記事)
]"""
        try:
            response = model.generate_content(prompt)
            response_text = response.text.strip()
            # LLMの応答からマークダウンのコードブロックを削除
            if response_text.startswith('```json'):
                response_text = response_text[len('```json'):].strip()
            if response_text.endswith('```'):
                response_text = response_text[:-len('```')].strip()

            # LLMの応答からJSON部分のみを抽出
            json_start = response_text.find('[')
            json_end = response_text.rfind(']')
            if json_start != -1 and json_end != -1:
                json_str = response_text[json_start : json_end + 1]
            else:
                raise json.JSONDecodeError("JSONの開始または終了が見つかりません", response_text, 0)

            selected_json = json.loads(json_str)
            for selected_item in selected_json:
                # 元の記事からURLを取得し、選定された記事情報に追加
                original_article = next(
                    (
                        a
                        for a in category_articles
                        if a["title"] == selected_item["title"]
                    ),
                    None,
                )
                if original_article:
                    selected_item["url"] = original_article["url"]
                    selected_articles.append(selected_item)
                else:
                    print(
                        f"警告: 選定された記事 '{selected_item['title']}' の元のURLが見つかりませんでした。"
                    )
        except json.JSONDecodeError as e:
            print(
                f"Gemini APIからのJSON応答のパース中にエラーが発生しました: {e}. 応答: {response_text[:200]}..."
            )
        except Exception as e:
            print(f"Gemini API呼び出し中に記事選定エラーが発生しました: {e}")
    return selected_articles

def generate_image_keywords_with_gemini(title: str, summary: str, category: str) -> str:
    """
    Gemini-2.5-flashを使用して、記事のタイトル、要約、カテゴリから画像検索用のキーワードを生成する。
    """
    try:
        model = genai.GenerativeModel("models/gemini-2.5-flash")
        prompt = f"""以下の記事のタイトル、要約、カテゴリを読み、記事の内容を最もよく表す英語の画像検索キーワードを3つ生成してください。キーワードはカンマで区切ってください。

カテゴリ: {category}
タイトル: {title}
要約: {summary}

キーワード:"""
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Gemini API呼び出し中に画像キーワード生成エラーが発生しました: {e}")
        return ""

def search_image_from_unsplash(keywords: str) -> str | None:
    """
    Unsplash APIを使用して、キーワードに基づいて画像を検索し、画像URLを返す。
    """
    unsplash_access_key = os.environ.get("UNSPLASH_ACCESS_KEY")
    if not unsplash_access_key:
        print("警告: UNSPLASH_ACCESS_KEY 環境変数が設定されていません。Unsplashからの画像検索をスキップします。")
        return None

    if not keywords:
        return None

    try:
        headers = {
            "Authorization": f"Client-ID {unsplash_access_key}"
        }
        params = {
            "query": keywords,
            "orientation": "landscape", # 横長の画像を優先
            "per_page": 1
        }
        response = requests.get("https://api.unsplash.com/search/photos", headers=headers, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()

        if data and data["results"]:
            # 最初の結果のregularサイズの画像URLを返す
            return data["results"][0]["urls"]["regular"]
        else:
            print(f"Unsplashでキーワード '{keywords}' に一致する画像が見つかりませんでした。")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Unsplash API呼び出し中にエラーが発生しました: {e}")
        return None
    except Exception as e:
        print(f"Unsplashからの画像検索中に予期せぬエラーが発生しました: {e}")
        return None