"""`python build.py --check`: a short checklist of profile.toml."""

from __future__ import annotations

from . import icons
from .config import Config

TAG = {"ok": "[ OK ]", "info": "[INFO]", "warn": "[WARN]", "error": "[FAIL]"}


def _line(level: str, label: str, text: str) -> str:
    dots = "." * max(2, 26 - len(label))
    return f" {TAG[level]} {label} {dots} {text}"


def report(cfg: Config) -> tuple[str, int]:
    for _, items in cfg.skills:
        for slug, _ in items:
            if not icons.available(slug):
                cfg.warn("skills", f"icon '{slug}' isn't downloaded yet (a '?' tile is shown): run "
                                   "`python build.py --fetch-icons`, or just push — the workflow fetches it")
    flagged = [i.field for i in cfg.issues if i.level in ("warn", "error")]
    lines = [f"README CHECK ({cfg.path.name})", "─" * 64]

    def ok(label: str, text: str, key: str) -> None:
        if not any(f == key or f.startswith((key + ".", key + "[")) for f in flagged):
            lines.append(_line("ok", label, text))

    ok("name", cfg.name, "profile.name")
    ok("github_username", cfg.github_username, "profile.github_username")
    ok("headline", " | ".join(cfg.headline) or "none", "profile.headline")
    contact = [k for k in ("email", "linkedin", "website") if getattr(cfg, k)]
    ok("contact buttons", ", ".join(contact) or "none (hidden)", "contact")
    ok("profile buttons", ", ".join(p.label for p in cfg.profiles) or "none (hidden)", "profiles")
    ok("skills", f"{sum(len(i) for _, i in cfg.skills)} in {len(cfg.skills)} group(s)" if cfg.skills
       else "none (hidden)", "skills")
    ok("display", f"{cfg.accent} accent, game: {cfg.arcade or 'hidden'}, "
                  f"visitor counter: {'on' if cfg.visitor_counter else 'off'}", "display")
    order = {"error": 0, "warn": 1, "info": 2}
    if cfg.issues:
        lines.append("─" * 64)
        for issue in sorted(cfg.issues, key=lambda i: order[i.level]):
            lines.append(_line(issue.level, issue.field, issue.message))
    errors = sum(i.level == "error" for i in cfg.issues)
    warns = sum(i.level == "warn" for i in cfg.issues)
    lines.append("─" * 64)
    lines.append(f" {errors} error(s), {warns} warning(s). Fix the [FAIL] lines; affected elements stay hidden."
                 if errors else f" No errors, {warns} warning(s). Next: python build.py")
    return "\n".join(lines), errors
