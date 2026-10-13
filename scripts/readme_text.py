"""Escaping for text that lands in README.md (Markdown and inline HTML)."""

from __future__ import annotations

import re


def html(text: str) -> str:
    """Text inside an HTML element."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def attr(text: str) -> str:
    """Text inside a double-quoted HTML attribute."""
    return html(text).replace('"', "&quot;")


def md_text(text: str) -> str:
    """Plain text as one Markdown paragraph: nothing in it is interpreted."""
    text = " ".join(text.split())  # one paragraph, no stray line breaks
    text = html(text)
    text = re.sub(r"([\\`*_{}\[\]()#+!|~])", r"\\\1", text)
    return re.sub(r"^(\d+)\.(\s)", r"\1\\.\2", re.sub(r"^([-=>])", r"\\\1", text))
