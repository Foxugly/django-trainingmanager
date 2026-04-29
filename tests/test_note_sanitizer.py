"""Unit tests for the bleach-based HTML sanitizer used on Note.content."""

from note.sanitizer import sanitize_html


def test_strips_script_tags():
    out = sanitize_html('<p>Hello</p><script>alert("xss")</script>')
    assert "<script>" not in out
    assert "<p>Hello</p>" in out


def test_keeps_allowed_tags():
    out = sanitize_html("<p><strong>Bold</strong> <em>italic</em></p>")
    assert "<strong>" in out
    assert "<em>" in out


def test_strips_dangerous_attrs():
    out = sanitize_html('<a href="http://x.com" onclick="bad()">link</a>')
    assert "onclick" not in out
    assert 'href="http://x.com"' in out


def test_empty_input_returns_empty():
    assert sanitize_html("") == ""
    assert sanitize_html(None) == ""


def test_strips_javascript_protocol():
    out = sanitize_html('<a href="javascript:alert(1)">link</a>')
    assert "javascript:" not in out


def test_keeps_lists():
    out = sanitize_html("<ul><li>one</li><li>two</li></ul>")
    assert "<ul>" in out
    assert "<li>one</li>" in out


def test_strips_iframe():
    out = sanitize_html('<p>safe</p><iframe src="evil.com"></iframe>')
    assert "<iframe" not in out
    assert "<p>safe</p>" in out


def test_utf8_content_is_preserved():
    out = sanitize_html("<p>Salut, écoute le café résumé naïveté</p>")
    assert "écoute" in out
    assert "café" in out
