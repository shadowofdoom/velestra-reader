"""Read-only Reddit Data API client."""

from __future__ import annotations

import base64
import json
import time
from dataclasses import dataclass
from typing import Any, Mapping
from urllib import error, parse, request

from .config import ReaderConfig


TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
OAUTH_HOST = "oauth.reddit.com"
VALID_LISTING_SORTS = {"hot", "new", "top", "rising", "controversial"}
VALID_SEARCH_SORTS = {"relevance", "hot", "top", "new", "comments"}
VALID_TIMES = {"hour", "day", "week", "month", "year", "all"}


@dataclass(frozen=True)
class OAuthToken:
    access_token: str
    token_type: str
    expires_at: float
    scope: str


def _validate_subreddit(subreddit: str) -> str:
    name = subreddit.removeprefix("r/").strip()
    if not name or not all(character.isalnum() or character == "_" for character in name):
        raise ValueError("Subreddit names may only contain letters, numbers, and underscores.")
    return name


def _bounded_limit(limit: int) -> int:
    if limit < 1 or limit > 100:
        raise ValueError("limit must be between 1 and 100.")
    return limit


def oauth_url_for_reddit_url(url: str) -> str:
    """Convert a reddit.com URL or path into an oauth.reddit.com API URL."""
    candidate = url.strip()
    if candidate.startswith("/"):
        parsed = parse.urlparse("https://www.reddit.com" + candidate)
    else:
        parsed = parse.urlparse(candidate)

    host = parsed.netloc.lower()
    if not parsed.scheme or not host.endswith("reddit.com"):
        raise ValueError("Expected a reddit.com URL or Reddit API path.")

    path = parsed.path or "/"
    if path.endswith(".json"):
        path = path[:-5]

    normalized = parsed._replace(scheme="https", netloc=OAUTH_HOST, path=path)
    return parse.urlunparse(normalized)


def build_thread_path(thread_url: str) -> str:
    """Return the read-only OAuth API path for a public Reddit thread."""
    parsed = parse.urlparse(thread_url.strip())
    host = parsed.netloc.lower()
    if not parsed.scheme or not host.endswith("reddit.com"):
        raise ValueError("Expected a reddit.com thread URL.")

    path = parsed.path.rstrip("/")
    if path.endswith(".json"):
        path = path[:-5]
    if "/comments/" not in path:
        raise ValueError("Expected a Reddit comments thread URL.")

    query = parse.urlencode({"limit": 500, "depth": 10, "raw_json": 1})
    return f"{path}?{query}"


def build_subreddit_listing_path(
    subreddit: str,
    *,
    sort: str = "hot",
    time: str = "all",
    limit: int = 25,
) -> str:
    """Return a read-only OAuth API path for a subreddit listing."""
    subreddit_name = _validate_subreddit(subreddit)
    if sort not in VALID_LISTING_SORTS:
        raise ValueError(f"Unsupported listing sort: {sort}")
    if time not in VALID_TIMES:
        raise ValueError(f"Unsupported time filter: {time}")

    query = parse.urlencode({"limit": _bounded_limit(limit), "t": time, "raw_json": 1})
    return f"/r/{subreddit_name}/{sort}?{query}"


def build_search_path(
    query: str,
    *,
    subreddit: str | None = None,
    sort: str = "relevance",
    time: str = "all",
    limit: int = 25,
) -> str:
    """Return a read-only OAuth API path for Reddit search."""
    search_query = query.strip()
    if not search_query:
        raise ValueError("Search query must not be empty.")
    if sort not in VALID_SEARCH_SORTS:
        raise ValueError(f"Unsupported search sort: {sort}")
    if time not in VALID_TIMES:
        raise ValueError(f"Unsupported time filter: {time}")

    if subreddit:
        subreddit_name = _validate_subreddit(subreddit)
        params: dict[str, str | int] = {
            "q": search_query,
            "restrict_sr": "on",
            "sort": sort,
            "t": time,
            "limit": _bounded_limit(limit),
            "raw_json": 1,
        }
        path = f"/r/{subreddit_name}/search"
    else:
        params = {
            "q": search_query,
            "sort": sort,
            "t": time,
            "limit": _bounded_limit(limit),
            "raw_json": 1,
        }
        path = "/search"

    return f"{path}?{parse.urlencode(params)}"


def _basic_auth_header(client_id: str, client_secret: str | None) -> str:
    raw = f"{client_id}:{client_secret or ''}".encode("utf-8")
    return "Basic " + base64.b64encode(raw).decode("ascii")


class VelestraReaderClient:
    """Small OAuth-only client for manually requested public Reddit content."""

    def __init__(self, config: ReaderConfig) -> None:
        self.config = config
        self._token: OAuthToken | None = None

    def get_access_token(self) -> OAuthToken:
        if self.config.access_token:
            return OAuthToken(
                access_token=self.config.access_token,
                token_type="bearer",
                expires_at=time.time() + 3600,
                scope="",
            )
        if self._token and self._token.expires_at > time.time() + 60:
            return self._token

        self._token = self.request_access_token()
        return self._token

    def request_access_token(self) -> OAuthToken:
        if not self.config.client_id:
            raise ValueError("VELESTRA_READER_CLIENT_ID is required for OAuth token requests.")

        if self.config.refresh_token:
            form: Mapping[str, str] = {
                "grant_type": "refresh_token",
                "refresh_token": self.config.refresh_token,
            }
        else:
            form = {"grant_type": "client_credentials"}

        req = request.Request(
            TOKEN_URL,
            data=parse.urlencode(form).encode("utf-8"),
            headers={
                "Authorization": _basic_auth_header(
                    self.config.client_id,
                    self.config.client_secret,
                ),
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": self.config.user_agent,
                "Accept": "application/json",
            },
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=30) as response:
                body = response.read().decode("utf-8", errors="replace")
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"OAuth token request failed with HTTP {exc.code}: {body[:200]}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"OAuth token request failed: {exc.reason}") from exc

        data = json.loads(body)
        access_token = data.get("access_token")
        if not access_token:
            raise RuntimeError("OAuth token response did not include access_token.")
        expires_in = int(data.get("expires_in", 3600))
        return OAuthToken(
            access_token=access_token,
            token_type=data.get("token_type", "bearer"),
            expires_at=time.time() + expires_in,
            scope=data.get("scope", ""),
        )

    def get_json(self, url_or_path: str) -> Any:
        oauth_url = oauth_url_for_reddit_url(url_or_path)
        token = self.get_access_token()
        req = request.Request(
            oauth_url,
            headers={
                "Authorization": f"Bearer {token.access_token}",
                "User-Agent": self.config.user_agent,
                "Accept": "application/json",
            },
            method="GET",
        )
        try:
            with request.urlopen(req, timeout=30) as response:
                body = response.read().decode("utf-8", errors="replace")
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Reddit API request failed with HTTP {exc.code}: {body[:200]}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"Reddit API request failed: {exc.reason}") from exc
        return json.loads(body)

    def fetch_thread(self, thread_url: str) -> Any:
        return self.get_json(build_thread_path(thread_url))

    def fetch_subreddit(
        self,
        subreddit: str,
        *,
        sort: str = "hot",
        time: str = "all",
        limit: int = 25,
    ) -> Any:
        return self.get_json(
            build_subreddit_listing_path(subreddit, sort=sort, time=time, limit=limit)
        )

    def search(
        self,
        query: str,
        *,
        subreddit: str | None = None,
        sort: str = "relevance",
        time: str = "all",
        limit: int = 25,
    ) -> Any:
        return self.get_json(
            build_search_path(query, subreddit=subreddit, sort=sort, time=time, limit=limit)
        )
