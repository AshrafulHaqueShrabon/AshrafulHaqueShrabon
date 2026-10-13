"""Tiny, dependency-free SVG string builder."""

from __future__ import annotations

from typing import Any


def num(value: float) -> str:
    """Compact, deterministic number formatting (max 2 decimals)."""
    if isinstance(value, int):
        return str(value)
    text = f"{value:.2f}".rstrip("0").rstrip(".")
    return "0" if text in ("-0", "") else text


def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def esc_attr(text: str) -> str:
    return esc(text).replace('"', "&quot;")


def attrs(values: dict[str, Any]) -> str:
    parts = []
    for key, value in values.items():
        if value is None or value is False:
            continue
        key = key.rstrip("_").replace("_", "-")
        if value is True:
            value = key
        elif isinstance(value, (int, float)):
            value = num(value)
        parts.append(f'{key}="{esc_attr(str(value))}"')
    return (" " + " ".join(parts)) if parts else ""


def el(tag: str, values: dict[str, Any] | None = None, *children: str) -> str:
    """Build an element. Children are already-rendered strings."""
    inner = "".join(c for c in children if c)
    if inner:
        return f"<{tag}{attrs(values or {})}>{inner}</{tag}>"
    return f"<{tag}{attrs(values or {})}/>"


def text_el(content: str, values: dict[str, Any]) -> str:
    return f"<text{attrs(values)}>{esc(content)}</text>"


def group(*children: str, **values: Any) -> str:
    return el("g", values, *children)


def rect(x: float, y: float, w: float, h: float, **values: Any) -> str:
    return el("rect", {"x": x, "y": y, "width": w, "height": h, **values})
