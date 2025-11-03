# src/utils.py
import re

def remove_html_tags(text: str) -> str:
    """
    テキストからHTMLタグを除去します。
    """
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)
