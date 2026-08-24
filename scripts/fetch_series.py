#!/usr/bin/env python3
"""Fetch the public WeChat album and extract its article bodies for local study.

The script deliberately keeps no raw page HTML. It writes a reproducible metadata
index, normalized text with image placeholders, and the content images needed to
understand diagrams/formulas that are not represented in HTML text.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import mimetypes
import re
import time
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests

BIZ = "MzU1NTc1NDMxMQ=="
ALBUM_ID = "4283734360739921922"
ALBUM_API = "https://mp.weixin.qq.com/mp/appmsgalbum"
ALBUM_PAGE = (
    "https://mp.weixin.qq.com/mp/appmsgalbum?"
    f"__biz={BIZ}&action=getalbum&album_id={ALBUM_ID}&scene=173"
)
WECHAT_UA = (
    "Mozilla/5.0 (Linux; Android 13; Pixel 7 Pro Build/TQ3A.230901.001; wv) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 "
    "Chrome/112.0.5615.136 Mobile Safari/537.36 XWEB/5267 "
    "MMWEBSDK/20231202 MMWEBID/883 MicroMessenger/8.0.45.2521(0x28002D3D) "
    "WeChat/arm64 Weixin NetType/WIFI Language/zh_CN ABI/arm64"
)

VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
}
BLOCK_TAGS = {
    "address", "article", "aside", "blockquote", "dd", "div", "dl", "dt",
    "figcaption", "figure", "footer", "header", "h1", "h2", "h3", "h4",
    "h5", "h6", "hr", "li", "main", "nav", "ol", "p", "pre", "section",
    "table", "tbody", "tfoot", "thead", "tr", "ul",
}
SKIP_TAGS = {"script", "style", "noscript"}


def clean_slug(number: int, title: str) -> str:
    short = re.sub(r"^高校教学系列[：:]?", "", title)
    short = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "-", short).strip("-")
    return f"{number:02d}-{short[:48]}"


def normalize_article_url(url: str) -> str:
    return url.replace("http://", "https://", 1).split("#", 1)[0]


def best_image_url(url: str) -> str:
    """Ask qpic for the original image while retaining format query metadata."""
    if not url:
        return url
    url = url.replace("&amp;", "&")
    parsed = urlparse(url)
    path = re.sub(r"/(?:300|640)$", "/0", parsed.path)
    return parsed._replace(path=path, fragment="").geturl()


def extension_for(content_type: str, url: str) -> str:
    content_type = content_type.split(";", 1)[0].strip().lower()
    explicit = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/gif": ".gif",
        "image/webp": ".webp",
        "image/svg+xml": ".svg",
    }.get(content_type)
    if explicit:
        return explicit
    match = re.search(r"(?:^|[?&])wx_fmt=([a-zA-Z0-9]+)", url)
    if match:
        fmt = match.group(1).lower()
        return ".jpg" if fmt in {"jpg", "jpeg"} else f".{fmt}"
    guessed = mimetypes.guess_extension(content_type)
    return guessed or ".bin"


class ArticleExtractor(HTMLParser):
    """Extract readable text and ordered content-image records from js_content."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.skip_depth = 0
        self.parts: list[str] = []
        self.images: list[dict[str, str]] = []
        self.links: list[str] = []
        self._active_link: str | None = None

    @property
    def inside(self) -> bool:
        return self.depth > 0

    def _newline(self) -> None:
        if self.parts and not self.parts[-1].endswith("\n"):
            self.parts.append("\n")

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        data = {key: value or "" for key, value in attrs}
        starting_root = not self.inside and data.get("id") == "js_content"
        if starting_root:
            self.depth = 1
        elif self.inside and tag not in VOID_TAGS:
            self.depth += 1
        if not self.inside:
            return

        if tag in SKIP_TAGS:
            self.skip_depth += 1
        if tag in BLOCK_TAGS or tag == "br":
            self._newline()
        if tag in {"td", "th"}:
            self.parts.append(" | ")
        if tag == "a":
            href = data.get("href", "")
            self._active_link = href
            if href:
                self.links.append(href)
        if tag == "img":
            src = data.get("data-src") or data.get("src") or ""
            # Ignore WeChat's transparent lazy-loading placeholder.
            if src and "data:image/" not in src:
                record = {
                    "source_url": best_image_url(src),
                    "display_url": src.replace("&amp;", "&"),
                    "alt": data.get("alt", ""),
                    "declared_type": data.get("data-type", ""),
                    "style": data.get("style", ""),
                }
                self.images.append(record)
                self.parts.append(f"\n[[IMAGE_{len(self.images):02d}]]\n")

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if tag.lower() not in VOID_TAGS:
            self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if not self.inside:
            return
        if tag in SKIP_TAGS and self.skip_depth:
            self.skip_depth -= 1
        if tag in BLOCK_TAGS:
            self._newline()
        if tag == "a":
            self._active_link = None
        if tag not in VOID_TAGS:
            self.depth -= 1

    def handle_data(self, data: str) -> None:
        if self.inside and not self.skip_depth:
            self.parts.append(data)

    def normalized_lines(self) -> list[str]:
        raw = "".join(self.parts).replace("\xa0", " ").replace("\u200b", "")
        result: list[str] = []
        previous_blank = True
        for line in raw.splitlines():
            line = re.sub(r"[ \t\r\f\v]+", " ", line).strip()
            if not line:
                if not previous_blank and result:
                    result.append("")
                previous_blank = True
                continue
            result.append(line)
            previous_blank = False
        while result and not result[-1]:
            result.pop()
        return result


def session() -> requests.Session:
    result = requests.Session()
    result.headers.update({
        "User-Agent": WECHAT_UA,
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Referer": ALBUM_PAGE,
    })
    return result


def get_json(client: requests.Session, url: str, params: dict[str, str]) -> dict[str, Any]:
    response = client.get(url, params=params, timeout=90)
    response.raise_for_status()
    return response.json()


def get_album(client: requests.Session) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    payload = get_json(client, ALBUM_API, {
        "action": "getalbum",
        "__biz": BIZ,
        "album_id": ALBUM_ID,
        "count": "100",
        "f": "json",
    })
    response = payload["getalbum_resp"]
    base_info = response["base_info"]
    articles = response["article_list"]
    expected = int(base_info["article_count"])
    if len(articles) != expected or response.get("continue_flag") != "0":
        raise RuntimeError(
            f"Album pagination incomplete: received {len(articles)} of {expected}; "
            f"continue_flag={response.get('continue_flag')!r}"
        )
    return base_info, articles


def fetch_image(client: requests.Session, record: dict[str, str], stem: Path) -> dict[str, Any]:
    response = client.get(record["source_url"], timeout=90)
    response.raise_for_status()
    content_type = response.headers.get("content-type", "application/octet-stream")
    suffix = extension_for(content_type, record["source_url"])
    destination = stem.with_suffix(suffix)
    destination.write_bytes(response.content)
    return {
        **record,
        "local_path": destination.as_posix(),
        "content_type": content_type,
        "bytes": len(response.content),
        "sha256": hashlib.sha256(response.content).hexdigest(),
    }


def fetch_article(
    client: requests.Session,
    article: dict[str, Any],
    number: int,
    output_root: Path,
    pause: float,
) -> dict[str, Any]:
    title = article["title"]
    slug = clean_slug(number, title)
    article_dir = output_root / "articles" / slug
    assets_dir = article_dir / "images"
    assets_dir.mkdir(parents=True, exist_ok=True)
    url = normalize_article_url(article["url"])

    response = client.get(url, timeout=120)
    response.raise_for_status()
    if "wappoc_appmsgcaptcha" in response.url or 'id="js_content"' not in response.text:
        raise RuntimeError(f"WeChat returned a verification page for: {title}")

    extractor = ArticleExtractor()
    extractor.feed(response.text)
    lines = extractor.normalized_lines()
    if not lines:
        raise RuntimeError(f"No body text extracted for: {title}")

    image_records: list[dict[str, Any]] = []
    for image_number, image in enumerate(extractor.images, start=1):
        image_records.append(
            fetch_image(client, image, assets_dir / f"image-{image_number:02d}")
        )
        if pause:
            time.sleep(pause)

    created_at = dt.datetime.fromtimestamp(
        int(article["create_time"]), tz=dt.timezone(dt.timedelta(hours=8))
    )
    relative_dir = article_dir.relative_to(output_root.parent)
    frontmatter = [
        "---",
        f"series_number: {number}",
        f"title: {json.dumps(title, ensure_ascii=False)}",
        f"published_at: {created_at.isoformat()}",
        f"source_url: {json.dumps(url, ensure_ascii=False)}",
        f"msgid: {article.get('msgid', '')}",
        f"itemidx: {article.get('itemidx', '')}",
        f"image_count: {len(image_records)}",
        "---",
        "",
        f"# {title}",
        "",
        "> 研究用规范化抽取：保留原文信息顺序，以图片占位符关联本地图片；不含页面广告和脚本。",
        "",
    ]
    (article_dir / "extracted.md").write_text(
        "\n".join(frontmatter + lines) + "\n", encoding="utf-8"
    )
    (article_dir / "images.json").write_text(
        json.dumps(image_records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return {
        "series_number": number,
        "title": title,
        "published_at": created_at.isoformat(),
        "source_url": url,
        "msgid": article.get("msgid", ""),
        "itemidx": article.get("itemidx", ""),
        "slug": slug,
        "extracted_path": (relative_dir / "extracted.md").as_posix(),
        "image_manifest_path": (relative_dir / "images.json").as_posix(),
        "body_characters": sum(len(line) for line in lines),
        "body_lines": len(lines),
        "content_images": len(image_records),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output", type=Path, default=Path("sources/wechat-series"),
        help="output directory (default: sources/wechat-series)",
    )
    parser.add_argument(
        "--pause", type=float, default=0.15,
        help="delay in seconds between image requests",
    )
    args = parser.parse_args()
    output_root = args.output.resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    client = session()
    # Opening the album page first mirrors a normal public navigation path.
    album_response = client.get(ALBUM_PAGE, timeout=90)
    album_response.raise_for_status()
    base_info, articles = get_album(client)

    index_articles = []
    for number, article in enumerate(articles, start=1):
        print(f"[{number}/{len(articles)}] {article['title']}", flush=True)
        index_articles.append(
            fetch_article(client, article, number, output_root, args.pause)
        )
        if args.pause:
            time.sleep(args.pause)

    generated_at = dt.datetime.now(dt.timezone.utc).isoformat()
    index = {
        "source": {
            "platform": "微信公众号",
            "album_title": base_info.get("title", ""),
            "album_id": ALBUM_ID,
            "biz": BIZ,
            "account_name": base_info.get("nickname", ""),
            "account_username": base_info.get("username", ""),
            "official_article_count": int(base_info.get("article_count", 0)),
            "is_updating": base_info.get("isupdating") == "1",
            "album_page": ALBUM_PAGE,
        },
        "retrieved_at": generated_at,
        "completeness": {
            "listed": len(articles),
            "extracted": len(index_articles),
            "all_officially_listed_articles_extracted": len(index_articles)
            == int(base_info.get("article_count", 0)),
            "continue_flag_was_clear": True,
        },
        "articles": index_articles,
    }
    (output_root / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Wrote {output_root / 'index.json'}")


if __name__ == "__main__":
    main()
