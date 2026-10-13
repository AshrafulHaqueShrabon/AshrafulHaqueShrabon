"""GitHub GraphQL: language bytes over the user's own, non-fork repositories.

Needs a token: GITHUB_TOKEN in Actions (public repos), or the optional
PROFILE_PAT secret to include private repositories.
"""

from __future__ import annotations

from .http import HTTP, FetchError

URL = "https://api.github.com/graphql"
QUERY = """query languages($login: String!, $after: String) {
  user(login: $login) {
    login
    repositories(first: 100, after: $after, ownerAffiliations: OWNER, isFork: false) {
      pageInfo { hasNextPage endCursor }
      nodes { languages(first: 10, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name color } } } }
    }
  }
}"""


def _user(payload: object) -> dict:
    if not isinstance(payload, dict) or payload.get("errors"):
        errors = payload.get("errors") if isinstance(payload, dict) else None
        raise FetchError(f"github: {errors[0].get('message') if errors else 'unexpected response'}")
    user = (payload.get("data") or {}).get("user")
    if not user:
        raise FetchError("github: user not found")
    return user


def parse(pages: list[object]) -> dict:
    """{"handle", "languages": [[name, bytes, color], …] largest first}."""
    first = _user(pages[0])
    sizes: dict[str, int] = {}
    colors: dict[str, str | None] = {}
    for page in pages:
        for repo in _user(page)["repositories"]["nodes"]:
            for edge in repo["languages"]["edges"]:
                name = edge["node"]["name"]
                sizes[name] = sizes.get(name, 0) + edge["size"]
                colors[name] = edge["node"].get("color")
    ordered = sorted(sizes.items(), key=lambda kv: (-kv[1], kv[0]))
    return {"handle": first["login"], "languages": [[n, s, colors[n]] for n, s in ordered]}


def fetch(login: str, token: str, http: HTTP) -> dict:
    headers = {"Authorization": f"bearer {token}"}
    variables: dict = {"login": login, "after": None}
    pages = []
    for _ in range(10):  # up to 1000 repositories
        page = http.post_json(URL, {"query": QUERY, "variables": variables}, headers)
        pages.append(page)
        info = _user(page)["repositories"]["pageInfo"]
        if not info["hasNextPage"]:
            break
        variables["after"] = info["endCursor"]
    return parse(pages)
