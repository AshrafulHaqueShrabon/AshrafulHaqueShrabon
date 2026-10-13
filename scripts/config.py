"""Load and validate profile.toml (the single source of truth).

Content problems never raise: they become Issues that `build.py --check`
prints, and the build hides whatever they affect instead of emitting broken
links, "None" or "undefined".
"""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from . import urls

PLATFORMS = ("codeforces", "atcoder", "leetcode", "codechef", "hackerrank", "beecrowd", "cses", "vjudge")
PLATFORM_LABELS = {
    "codeforces": "Codeforces", "atcoder": "AtCoder", "leetcode": "LeetCode", "codechef": "CodeChef",
    "hackerrank": "HackerRank", "beecrowd": "beecrowd", "cses": "CSES", "vjudge": "vjudge",
}
ARCADE_GAMES = ("pacman", "breakout", "galaga", "puzzle-bobble", "bomberman", "minesweeper", "snake")
ACCENTS = ("amber", "green")
GITHUB_USER_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9]|-(?=[A-Za-z0-9])){0,38}$")

KNOWN = {
    "profile": {"name", "github_username", "headline", "bio"},
    "contact": {"email", "linkedin", "website", "website_label"},
    "profiles": set(PLATFORMS),
    "skills": None,  # free-form groups
    "github": {"top_languages", "exclude_languages"},
    "display": {"accent", "arcade", "visitor_counter"},
}


@dataclass
class Issue:
    level: str   # "error" | "warn" | "info"
    field: str
    message: str


@dataclass
class Profile:
    key: str
    label: str    # button text, e.g. "Codeforces"
    url: str      # canonical profile URL
    handle: str


@dataclass
class Config:
    path: Path
    name: str = ""
    github_username: str = ""
    headline: list[str] = field(default_factory=list)
    bio: str = ""
    email: str = ""
    linkedin: str = ""
    website: str = ""
    website_label: str = "Website"
    profiles: list[Profile] = field(default_factory=list)
    skills: list[tuple[str, list[tuple[str, str | None]]]] = field(default_factory=list)
    top_languages: int = 5
    exclude_languages: list[str] = field(default_factory=list)
    accent: str = "amber"
    arcade: str = "pacman"
    visitor_counter: bool = False
    issues: list[Issue] = field(default_factory=list)

    def error(self, field_name: str, message: str) -> None:
        self.issues.append(Issue("error", field_name, message))

    def warn(self, field_name: str, message: str) -> None:
        self.issues.append(Issue("warn", field_name, message))

    def info(self, field_name: str, message: str) -> None:
        self.issues.append(Issue("info", field_name, message))

    @property
    def has_errors(self) -> bool:
        return any(i.level == "error" for i in self.issues)

    @property
    def display_name(self) -> str:
        return self.name or "Your Name"


def _str(cfg: Config, data: dict, key: str, path: str, default: str = "") -> str:
    value = data.get(key, default)
    if value is None:
        return default
    if not isinstance(value, str):
        cfg.error(path, f"should be text in quotes, got {type(value).__name__}")
        return default
    return value.strip()


def _str_list(cfg: Config, data: dict, key: str, path: str) -> list[str]:
    value = data.get(key, [])
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list):
        cfg.error(path, 'should be a list like ["a", "b"]')
        return []
    out = []
    for i, item in enumerate(value):
        if not isinstance(item, str):
            cfg.error(f"{path}[{i}]", "should be text in quotes")
        elif item.strip():
            out.append(item.strip())
    return out


def load(path: str | Path) -> Config:
    path = Path(path)
    cfg = Config(path=path)
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        cfg.error("file", f"{path} not found")
        return cfg
    except tomllib.TOMLDecodeError as exc:
        cfg.error("file", f"TOML syntax error: {exc}")
        return cfg

    for table, value in data.items():
        if table not in KNOWN:
            cfg.warn(table, "unknown section (typo, or a setting from an older version?) — it is ignored")
        elif isinstance(value, dict) and KNOWN[table] is not None:
            for key in value:
                if key not in KNOWN[table]:
                    cfg.warn(f"{table}.{key}", "unknown setting (typo?) — it is ignored")

    _profile(cfg, data.get("profile", {}))
    _contact(cfg, data.get("contact", {}))
    _profiles(cfg, data.get("profiles", {}))
    _skills(cfg, data.get("skills", {}))
    _github(cfg, data.get("github", {}))
    _display(cfg, data.get("display", {}))
    return cfg


def _profile(cfg: Config, d: dict) -> None:
    cfg.name = _str(cfg, d, "name", "profile.name")
    if cfg.name.upper() == "YOUR NAME":
        cfg.warn("profile.name", "still the placeholder — enter your name as you want it shown")
        cfg.name = ""
    elif not cfg.name:
        cfg.warn("profile.name", "empty — enter your name")

    user = _str(cfg, d, "github_username", "profile.github_username").lstrip("@")
    if user.lower().startswith(("http://", "https://", "github.com/")):
        user = user.rstrip("/").rsplit("/", 1)[-1]
        cfg.info("profile.github_username", f"took '{user}' from the URL you entered")
    if not user:
        cfg.error("profile.github_username", "empty — top languages and the contribution game need it "
                                             "(they are hidden until you add it)")
    elif not GITHUB_USER_RE.match(user):
        cfg.error("profile.github_username", f"'{user}' isn't a valid GitHub username")
        user = ""
    cfg.github_username = user

    cfg.headline = _str_list(cfg, d, "headline", "profile.headline")
    if len(" | ".join(cfg.headline)) > 90:
        cfg.warn("profile.headline", "long headline; it wraps to two lines (90 characters or fewer fits one)")
    cfg.bio = " ".join(_str(cfg, d, "bio", "profile.bio").split())
    if not cfg.bio:
        cfg.info("profile.bio", "empty — a 1–2 sentence summary helps readers (optional)")


def _contact(cfg: Config, d: dict) -> None:
    cfg.email = _str(cfg, d, "email", "contact.email")
    if cfg.email:
        problem = urls.check_email(cfg.email)
        if problem:
            cfg.error("contact.email", f"{problem} — button hidden")
            cfg.email = ""
    for key, host in (("linkedin", "linkedin.com"), ("website", None)):
        value = _str(cfg, d, key, f"contact.{key}")
        if value and "://" not in value:
            value = "https://" + value
            cfg.info(f"contact.{key}", "added https:// in front")
        if value:
            problem = urls.check_web_url(value, host)
            if problem:
                cfg.error(f"contact.{key}", f"{problem} — button hidden")
                value = ""
        setattr(cfg, key, value)
    label = _str(cfg, d, "website_label", "contact.website_label", "Website") or "Website"
    if len(label) > 11:
        cfg.warn("contact.website_label", "longer than 11 characters; it is shortened to fit the button")
        label = label[:10] + "…"
    cfg.website_label = label


def _profiles(cfg: Config, d: dict) -> None:
    if not isinstance(d, dict):
        cfg.error("profiles", 'should be lines like codeforces = "https://…"')
        return
    for key, value in d.items():
        if key not in PLATFORMS:
            continue  # already reported as unknown
        path = f"profiles.{key}"
        if not isinstance(value, str):
            cfg.error(path, "should be the profile URL in quotes")
            continue
        if not value.strip():
            continue
        try:
            prof = urls.parse(key, value)
        except urls.URLError as exc:
            cfg.error(path, f"{exc} — button hidden")
            continue
        cfg.profiles.append(Profile(key, PLATFORM_LABELS[key], prof.url, prof.handle))


def _skills(cfg: Config, d: dict) -> None:
    from . import icons

    if not isinstance(d, dict):
        cfg.error("skills", 'should be groups like languages = ["c", "cpp"]')
        return
    for group in d:
        parsed = []
        for item in _str_list(cfg, d, group, f"skills.{group}"):
            slug, _, label = item.partition(":")
            slug = slug.strip().lower()
            problem = icons.check_slug(slug)
            if problem:
                cfg.error(f"skills.{group}", f"'{slug}': {problem} — item hidden")
                continue
            parsed.append((slug, label.strip() or None))
        if parsed:
            cfg.skills.append((group.replace("_", " "), parsed))


def _github(cfg: Config, d: dict) -> None:
    top = d.get("top_languages", 5)
    if isinstance(top, bool) or not isinstance(top, int) or not 1 <= top <= 8:
        cfg.error("github.top_languages", "should be a number from 1 to 8")
        top = 5
    cfg.top_languages = top
    cfg.exclude_languages = _str_list(cfg, d, "exclude_languages", "github.exclude_languages")


def _display(cfg: Config, d: dict) -> None:
    accent = _str(cfg, d, "accent", "display.accent", "amber").lower()
    if accent not in ACCENTS:
        cfg.error("display.accent", f"'{accent}' must be \"amber\" or \"green\" (using amber)")
        accent = "amber"
    cfg.accent = accent
    arcade = _str(cfg, d, "arcade", "display.arcade", "pacman").lower()
    if arcade and arcade not in ARCADE_GAMES:
        cfg.error("display.arcade", f"'{arcade}' must be one of: {', '.join(ARCADE_GAMES)} (or \"\" to hide)")
        arcade = "pacman"
    cfg.arcade = arcade
    counter = d.get("visitor_counter", False)
    if not isinstance(counter, bool):
        cfg.error("display.visitor_counter", "should be true or false (no quotes)")
        counter = False
    cfg.visitor_counter = counter
