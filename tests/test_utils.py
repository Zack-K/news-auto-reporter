import pytest
from src.utils import remove_html_tags


@pytest.mark.parametrize(
    "input_text, expected_text",
    [
        ("<p>Hello <b>World</b>!</p>", "Hello World!"),
        ("Hello World!", "Hello World!"),
        ("", ""),
        ('<a href="http://example.com" class="link">Link</a>', "Link"),
    ],
)
def test_remove_html_tags_various_cases(input_text, expected_text):
    """様々なHTMLタグ除去のケースをテスト"""
    assert remove_html_tags(input_text) == expected_text


def test_remove_html_tags_malformed_tags():
    """壊れたHTMLタグが与えられた場合に可能な限り除去されることをテスト"""
    html_text = "Text with <broken tag and <another one>"
    expected_text = "Text with "
    assert remove_html_tags(html_text) == expected_text


def test_remove_html_tags_multiple_lines():
    """複数行にわたるHTMLタグが正しく除去されることをテスト"""
    html_text = """<div>
    <h1>Title</h1>
    <p>Paragraph content.</p>
</div>"""
    expected_text = """
    Title
    Paragraph content.
"""
    assert remove_html_tags(html_text) == expected_text
