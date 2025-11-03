# llm_processor.py
# llm_processor.py
import os
import google.generativeai as genai
import json
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
        prompt = f"""以下の記事の概要を日本語に翻訳し、データサイエンス、データエンジニアリング、データ分析の初学者が読みやすいように、専門用語を避けつつ、具体例や比喩を交えながら、もう少し詳しく要約してください。要約の長さは200文字程度を目標とします。また、その記事の初学者向けのポイントを3行で生成してください。
    
    記事の概要:
    {text}
    
    出力形式はJSONオブジェクトで、以下のキーを含めてください。
    {{"summary": "[ここに要約]", "points": ["ポイント1", "ポイント2", "ポイント3"]}} """
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
選定した各記事について、初学者向けのポイントを3行で生成してください。

記事リスト:
{articles_info}

出力はJSON配列のみとし、前後に余計なテキストを含めないでください。出力形式:
[
  {{
    "title": "選定された記事のタイトル",
    "url": "選定された記事のURL",
    "summary": "選定された記事の要約",
    "category": "{category}",
    "points": ["ポイント1", "ポイント2", "ポイント3"]
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

def generate_closing_comment_with_gemini(articles: list) -> str:
    """
    Gemini-2.5-flashを使用して、選定された記事のリストに基づいて、
    コミュニティメンバーのコミュニケーションを促進するクロージングコメントを生成する。
    """
    try:
        model = genai.GenerativeModel("models/gemini-2.5-flash")
        articles_info = ""
        for i, article in enumerate(articles):
            articles_info += f"- {article.get('title', 'タイトルなし')} ({article.get('category', 'カテゴリ不明')})\n"

        prompt = f"""以下のAIニュースレポートで選定された記事のリストを参考に、データサイエンス、データエンジニアリング、データ分析の学習者コミュニティのメンバーが、これらのニュースについて活発にコミュニケーションを取りたくなるような、ポジティブで魅力的なクロージングコメントを100文字程度で生成してください。

選定された記事:
{articles_info}

クロージングコメント:"""
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Gemini API呼び出し中にクロージングコメント生成エラーが発生しました: {e}")
        return "今日のAIニュースレポートはいかがでしたか？ぜひコミュニティで感想や意見を共有し、議論を深めましょう！" # フォールバックコメント

