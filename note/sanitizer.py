"""HTML sanitization for Note.content via bleach.

Whitelist tags suitable for the rich text editor used on the
frontend (PrimeNG / Quill style). All disallowed tags and attributes
are stripped on save.
"""

import bleach

ALLOWED_TAGS = [
    "p",
    "br",
    "strong",
    "b",
    "em",
    "i",
    "u",
    "s",
    "ul",
    "ol",
    "li",
    "blockquote",
    "code",
    "pre",
    "h1",
    "h2",
    "h3",
    "h4",
    "a",
    "span",
]

ALLOWED_ATTRIBUTES = {
    "a": ["href", "title", "target", "rel"],
    "span": ["class"],
}

ALLOWED_PROTOCOLS = ["http", "https", "mailto"]


def sanitize_html(html):
    """Sanitize HTML coming from a rich text editor.

    Returns the cleaned HTML, or '' for None / empty input.
    """
    if not html:
        return ""
    return bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )
