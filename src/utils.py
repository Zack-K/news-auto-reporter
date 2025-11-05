# src/utils.py
import re
import html # 追加

def remove_html_tags(text: str) -> str:
    """
    テキストからHTMLタグとHTMLエンティティを除去します。
    """
    # まずHTMLエンティティをデコード
    decoded_text = html.unescape(text)
    # ノーブレークスペースを通常のスペースに変換
    decoded_text = decoded_text.replace('\xa0', ' ')
    # その後HTMLタグを除去
    clean = re.compile('<.*?>')
    return re.sub(clean, '', decoded_text)
