"""Small JSON-over-HTTP client with timeouts and polite retries."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request


class FetchError(Exception):
    """Any failure to get usable data from a service (message goes to the log)."""


class HTTP:
    def __init__(self, user_agent: str = "retro-profile-readme/1.0", timeout: float = 25,
                 retries: int = 2, pause: float = 2.0) -> None:
        self.user_agent = user_agent
        self.timeout = timeout
        self.retries = retries
        self.pause = pause

    def _open(self, request: urllib.request.Request) -> object:
        last: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as resp:
                    body = resp.read()
                return json.loads(body.decode("utf-8"))
            except urllib.error.HTTPError as exc:
                last = exc
                if exc.code not in (429, 500, 502, 503, 504):
                    break
            except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
                last = exc
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                raise FetchError(f"{request.full_url}: not JSON ({exc})") from exc
            if attempt < self.retries:
                time.sleep(self.pause * (attempt + 1))
        raise FetchError(f"{request.full_url}: {last}")

    def get_json(self, url: str, headers: dict[str, str] | None = None) -> object:
        request = urllib.request.Request(url, headers={"User-Agent": self.user_agent,
                                                       "Accept": "application/json", **(headers or {})})
        return self._open(request)

    def post_json(self, url: str, payload: dict, headers: dict[str, str] | None = None) -> object:
        request = urllib.request.Request(
            url, data=json.dumps(payload).encode("utf-8"), method="POST",
            headers={"User-Agent": self.user_agent, "Content-Type": "application/json",
                     "Accept": "application/json", **(headers or {})})
        return self._open(request)
