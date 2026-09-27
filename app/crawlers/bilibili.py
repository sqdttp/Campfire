import hashlib
import json
import re
import time
from collections.abc import Iterator
from pathlib import PurePosixPath
from typing import Any
from urllib.parse import urlencode, urlparse

import httpx

from app.core.config import get_settings

BVID_PATTERN = re.compile(r"(?<![0-9A-Za-z])(BV[0-9A-Za-z]{10})(?![0-9A-Za-z])", re.IGNORECASE)
MIXIN_KEY_ORDER = (
    46,
    47,
    18,
    2,
    53,
    8,
    23,
    32,
    15,
    50,
    10,
    31,
    58,
    3,
    45,
    35,
    27,
    43,
    5,
    49,
    33,
    9,
    42,
    19,
    29,
    28,
    14,
    39,
    12,
    38,
    41,
    13,
    37,
    48,
    7,
    16,
    24,
    55,
    40,
    61,
    26,
    17,
    0,
    1,
    60,
    51,
    30,
    4,
    22,
    25,
    54,
    21,
    56,
    59,
    6,
    63,
    57,
    62,
    11,
    36,
    20,
    34,
    44,
    52,
)


class BilibiliAPIError(Exception):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def extract_bvid(value: str) -> str:
    match = BVID_PATTERN.search(value.strip())
    if match is None:
        raise ValueError("Expected a Bilibili BV id or video URL")
    bvid = match.group(1)
    return "BV" + bvid[2:]


class BilibiliClient:
    def __init__(
        self,
        base_url: str,
        timeout_seconds: float,
        cookie: str | None = None,
        trust_env: bool = True,
    ) -> None:
        headers = {
            "Accept": "application/json",
            "Referer": "https://www.bilibili.com/",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
            ),
        }
        if cookie:
            headers["Cookie"] = cookie
        self._client = httpx.Client(
            base_url=base_url.rstrip("/"),
            headers=headers,
            timeout=timeout_seconds,
            follow_redirects=True,
            trust_env=trust_env,
        )
        self._has_configured_cookie = bool(cookie)
        self._anonymous_identity_initialized = False
        self._wbi_mixin_key: str | None = None

    def close(self) -> None:
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

    def _request(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        try:
            response = self._client.get(path, params=params)
            if response.status_code == 429:
                raise BilibiliAPIError("Bilibili rate limited this request", 429)
            response.raise_for_status()
            payload = response.json()
        except httpx.TimeoutException as exc:
            raise BilibiliAPIError("Bilibili request timed out", 504) from exc
        except httpx.HTTPStatusError as exc:
            raise BilibiliAPIError(f"Bilibili returned HTTP {exc.response.status_code}") from exc
        except (httpx.RequestError, ValueError) as exc:
            raise BilibiliAPIError("Could not read a valid response from Bilibili") from exc

        if not isinstance(payload, dict):
            raise BilibiliAPIError("Bilibili response was not a JSON object")
        return payload

    def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        payload = self._request(path, params)
        code = payload.get("code")
        if code != 0:
            message = str(payload.get("message") or "Bilibili API request failed")
            if code == -404:
                status_code = 404
            elif code == -400:
                status_code = 400
            elif code in {-352, -412}:
                status_code = 429
            else:
                status_code = 502
            raise BilibiliAPIError(message, status_code)
        data = payload.get("data")
        if not isinstance(data, dict):
            raise BilibiliAPIError("Bilibili response did not contain an object")
        return data

    def get_video(self, bvid: str) -> dict[str, Any]:
        return self._get("/x/web-interface/view", {"bvid": bvid})

    def get_comments(self, aid: int, limit: int) -> list[dict[str, Any]]:
        if limit <= 0:
            return []

        self._initialize_anonymous_identity()
        mixin_key = self._get_wbi_mixin_key()
        collected: list[dict[str, Any]] = []
        seen: set[str] = set()
        offset = ""
        page = 0
        while len(collected) < limit and page < 50:
            page += 1
            page_size = min(20, limit - len(collected))
            params = {
                "oid": aid,
                "type": 1,
                "mode": 3,
                "ps": page_size,
                "plat": 1,
                "pagination_str": json.dumps(
                    {"offset": offset}, ensure_ascii=False, separators=(",", ":")
                ),
                "web_location": 1315875,
            }
            data = self._get(
                "/x/v2/reply/wbi/main",
                _sign_wbi(params, mixin_key),
            )
            replies = data.get("replies") or []
            if page == 1:
                top_replies = data.get("top_replies") or []
                if isinstance(top_replies, list):
                    replies = [*top_replies, *replies]
            if not isinstance(replies, list) or not replies:
                break
            for reply in self._flatten_replies(replies):
                reply_id = str(reply.get("rpid") or "")
                if not reply_id or reply_id in seen:
                    continue
                seen.add(reply_id)
                collected.append(reply)
                if len(collected) >= limit:
                    break
            cursor = data.get("cursor") or {}
            pagination = cursor.get("pagination_reply") or {}
            next_offset = pagination.get("next_offset")
            if cursor.get("is_end") is True or next_offset in {None, "", offset}:
                break
            offset = str(next_offset)
        return collected

    def _initialize_anonymous_identity(self) -> None:
        if self._has_configured_cookie or self._anonymous_identity_initialized:
            return
        data = self._get("/x/frontend/finger/spi", {})
        for response_key, cookie_name in (("b_3", "buvid3"), ("b_4", "buvid4")):
            value = data.get(response_key)
            if value:
                self._client.cookies.set(cookie_name, str(value), domain=".bilibili.com")
        self._anonymous_identity_initialized = True

    def _get_wbi_mixin_key(self) -> str:
        if self._wbi_mixin_key:
            return self._wbi_mixin_key
        payload = self._request("/x/web-interface/nav", {})
        data = payload.get("data") or {}
        wbi_img = data.get("wbi_img") or {}
        img_key = _filename_stem(wbi_img.get("img_url"))
        sub_key = _filename_stem(wbi_img.get("sub_url"))
        raw_key = img_key + sub_key
        if len(raw_key) < 64:
            raise BilibiliAPIError("Bilibili did not provide WBI signing keys")
        self._wbi_mixin_key = "".join(raw_key[index] for index in MIXIN_KEY_ORDER)[:32]
        return self._wbi_mixin_key

    @classmethod
    def _flatten_replies(cls, replies: list[dict[str, Any]]) -> Iterator[dict[str, Any]]:
        for reply in replies:
            if not isinstance(reply, dict):
                continue
            yield reply
            nested = reply.get("replies") or []
            if isinstance(nested, list):
                yield from cls._flatten_replies(nested)


def get_bilibili_client() -> Iterator[BilibiliClient]:
    settings = get_settings()
    with BilibiliClient(
        base_url=settings.bilibili_api_base_url,
        timeout_seconds=settings.bilibili_request_timeout_seconds,
        cookie=settings.bilibili_cookie,
        trust_env=settings.bilibili_trust_env,
    ) as client:
        yield client


def _filename_stem(value: Any) -> str:
    if not value:
        return ""
    return PurePosixPath(urlparse(str(value)).path).stem


def _sign_wbi(
    params: dict[str, Any], mixin_key: str, timestamp: int | None = None
) -> dict[str, Any]:
    signed = {**params, "wts": timestamp or int(time.time())}
    filtered = {key: re.sub(r"[!'()*]", "", str(value)) for key, value in sorted(signed.items())}
    query = urlencode(filtered)
    signed["w_rid"] = hashlib.md5(f"{query}{mixin_key}".encode()).hexdigest()
    return signed
