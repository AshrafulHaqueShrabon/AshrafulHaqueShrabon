"""Profile URL → handle parsing for every supported platform.

You paste full profile URLs into profile.toml; APIs need handles. Common
variants are accepted: missing scheme, http, www/mobile hosts, trailing
slashes, query strings, extra path parts and legacy domains.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlsplit


class URLError(ValueError):
    """A URL that can't be turned into a profile handle (message is user-facing)."""


@dataclass(frozen=True)
class Profile:
    platform: str
    handle: str
    url: str  # canonical profile URL we link to


@dataclass(frozen=True)
class Rule:
    hosts: tuple[str, ...]
    patterns: tuple[str, ...]  # regexes over the path; group "h" is the handle
    canonical: str             # format string with {h}
    handle_re: str
    example: str
    numeric: bool = False      # handle is a numeric user id (beecrowd, CSES)


_H = r"(?P<h>[^/]+)"

RULES: dict[str, Rule] = {
    "codeforces": Rule(
        hosts=("codeforces.com", "m1.codeforces.com", "m2.codeforces.com", "m3.codeforces.com",
               "codeforces.ru", "mirror.codeforces.com"),
        patterns=(rf"^/profile/{_H}", rf"^/submissions/{_H}", rf"^/u/{_H}"),
        canonical="https://codeforces.com/profile/{h}",
        handle_re=r"[A-Za-z0-9_.\-]{2,24}",
        example="https://codeforces.com/profile/your_handle",
    ),
    "atcoder": Rule(
        hosts=("atcoder.jp",),
        patterns=(rf"^/users/{_H}",),
        canonical="https://atcoder.jp/users/{h}",
        handle_re=r"[A-Za-z0-9_]{3,16}",
        example="https://atcoder.jp/users/your_handle",
    ),
    "leetcode": Rule(
        hosts=("leetcode.com",),
        patterns=(rf"^/u/{_H}", rf"^/profile/{_H}", rf"^/{_H}/?$"),
        canonical="https://leetcode.com/u/{h}/",
        handle_re=r"[A-Za-z0-9_\-.]{1,40}",
        example="https://leetcode.com/u/your_handle/",
    ),
    "codechef": Rule(
        hosts=("codechef.com",),
        patterns=(rf"^/users/{_H}",),
        canonical="https://www.codechef.com/users/{h}",
        handle_re=r"[A-Za-z0-9_.]{2,30}",
        example="https://www.codechef.com/users/your_handle",
    ),
    "hackerrank": Rule(
        hosts=("hackerrank.com",),
        patterns=(rf"^/profile/{_H}", rf"^/{_H}/?$"),
        canonical="https://www.hackerrank.com/profile/{h}",
        handle_re=r"[A-Za-z0-9_\-.]{1,40}",
        example="https://www.hackerrank.com/profile/your_handle",
    ),
    "beecrowd": Rule(
        hosts=("judge.beecrowd.com", "beecrowd.com.br", "urionlinejudge.com.br"),
        patterns=(r"^/(?:judge/)?[a-z]{2}/profile/(?P<h>\d+)", r"^/(?:judge/)?profile/(?P<h>\d+)"),
        canonical="https://judge.beecrowd.com/en/profile/{h}",
        handle_re=r"\d{1,12}",
        example="https://judge.beecrowd.com/en/profile/123456",
        numeric=True,
    ),
    "cses": Rule(
        hosts=("cses.fi",),
        patterns=(r"^/user/(?P<h>\d+)", r"^/problemset/user/(?P<h>\d+)"),
        canonical="https://cses.fi/user/{h}",
        handle_re=r"\d{1,12}",
        example="https://cses.fi/user/123456",
        numeric=True,
    ),
    "vjudge": Rule(
        hosts=("vjudge.net",),
        patterns=(rf"^/user/{_H}",),
        canonical="https://vjudge.net/user/{h}",
        handle_re=r"[A-Za-z0-9_\-.]{1,40}",
        example="https://vjudge.net/user/your_handle",
    ),
}

# First path segments that are site pages, not usernames (for /<handle> style URLs).
RESERVED = {
    "leetcode": {"problems", "problemset", "contest", "discuss", "explore", "u", "profile", "accounts",
                 "studyplan", "assessment", "subscribe", "store", "jobs", "interview", "tag", "company"},
    "hackerrank": {"domains", "challenges", "contests", "dashboard", "profile", "auth", "certify",
                   "skills-verification", "interview", "settings", "leaderboard", "jobs", "work"},
}


def _host(netloc: str) -> str:
    host = netloc.lower().split("@")[-1].split(":")[0]
    return host[4:] if host.startswith("www.") else host


def parse(platform: str, url: str) -> Profile:
    """Turn a pasted profile URL into a Profile, or raise URLError."""
    rule = RULES[platform]
    raw = url.strip()
    if not raw:
        raise URLError("empty")
    if "://" not in raw:
        raw = "https://" + raw
    parts = urlsplit(raw)
    if parts.scheme not in ("http", "https"):
        raise URLError(f"must start with https:// (got {parts.scheme}://)")
    host = _host(parts.netloc)
    if host == "leetcode.cn":
        raise URLError("leetcode.cn has a separate API; use your leetcode.com profile URL")
    if host not in rule.hosts:
        raise URLError(f"expected a {rule.hosts[0]} link like {rule.example}")
    path = re.sub(r"/{2,}", "/", parts.path) or "/"
    for pattern in rule.patterns:
        match = re.match(pattern, path)
        if not match:
            continue
        handle = match.group("h").strip()
        if handle.lower() in RESERVED.get(platform, ()):
            continue
        if not re.fullmatch(rule.handle_re, handle):
            raise URLError(f"'{handle}' doesn't look like a {platform} "
                           f"{'user id' if rule.numeric else 'handle'}")
        return Profile(platform, handle, rule.canonical.format(h=handle))
    raise URLError(f"couldn't find a profile in this link; expected something like {rule.example}")


EMAIL_RE = re.compile(r"^[^@\s<>\"']+@[^@\s<>\"']+\.[A-Za-z]{2,}$")


def check_email(value: str) -> str | None:
    """Error message for a malformed email, or None."""
    if value.lower().startswith("mailto:"):
        return "write just the address, without 'mailto:'"
    if not EMAIL_RE.match(value):
        return "doesn't look like an email address (expected you@example.com)"
    return None


def check_web_url(value: str, host_hint: str | None = None) -> str | None:
    """Error message for a malformed http(s) URL, or None."""
    parts = urlsplit(value.strip())
    if parts.scheme not in ("http", "https"):
        return "must be a full URL starting with https://"
    host = _host(parts.netloc)
    if "." not in host or any(c.isspace() for c in value.strip()):
        return "doesn't look like a valid web address"
    if host_hint and not (host == host_hint or host.endswith("." + host_hint)):
        return f"expected a {host_hint} link"
    return None
