#!/usr/bin/env python3
"""Fetch the public WeChat album and extract its article bodies for local study.

The script writes a reproducible metadata index, the exact fetched page HTML,
a safe local-view HTML that preserves the original js_content element structure,
normalized text, and the content images needed for offline study.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
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


class ArticleHTMLExtractor(HTMLParser):
    """Preserve the js_content tree while localizing its ordered images.

    The exact HTTP response is stored separately. This serializer intentionally
    removes inline event-handler attributes and remote srcset values so the local
    view remains inert under its restrictive Content-Security-Policy.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.depth = 0
        self.parts: list[str] = []
        self.image_count = 0

    @property
    def inside(self) -> bool:
        return self.depth > 0

    def _attributes(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> list[tuple[str, str | None]]:
        result: list[tuple[str, str | None]] = []
        data = {key.lower(): value or "" for key, value in attrs}
        image_source = ""
        if tag == "img":
            image_source = data.get("data-src") or data.get("src") or ""
            if image_source and "data:image/" not in image_source:
                self.image_count += 1

        for key, value in attrs:
            lowered = key.lower()
            if lowered.startswith("on"):
                continue
            if tag == "img" and lowered in {"src", "data-src", "srcset", "data-srcset"}:
                continue
            result.append((key, value))

        if tag == "img" and image_source and "data:image/" not in image_source:
            placeholder = f"__WECHAT_LOCAL_IMAGE_{self.image_count:02d}__"
            result.extend([
                ("src", placeholder),
                ("data-original-src", image_source.replace("&amp;", "&")),
                ("loading", "lazy"),
            ])
        return result

    @staticmethod
    def _tag(tag: str, attrs: list[tuple[str, str | None]], closing: str = ">") -> str:
        rendered = [f"<{tag}"]
        for key, value in attrs:
            rendered.append(f" {html.escape(key, quote=True)}")
            if value is not None:
                rendered.append(f'="{html.escape(value, quote=True)}"')
        rendered.append(closing)
        return "".join(rendered)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        data = {key.lower(): value or "" for key, value in attrs}
        starting_root = not self.inside and data.get("id") == "js_content"
        if starting_root:
            self.depth = 1
        elif self.inside and tag not in VOID_TAGS:
            self.depth += 1
        if self.inside:
            self.parts.append(self._tag(tag, self._attributes(tag, attrs)))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if self.inside:
            self.parts.append(self._tag(tag, self._attributes(tag, attrs), " />"))

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if not self.inside:
            return
        self.parts.append(f"</{tag}>")
        if tag not in VOID_TAGS:
            self.depth -= 1

    def handle_data(self, data: str) -> None:
        if self.inside:
            self.parts.append(data)

    def handle_entityref(self, name: str) -> None:
        if self.inside:
            self.parts.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        if self.inside:
            self.parts.append(f"&#{name};")

    def handle_comment(self, data: str) -> None:
        if self.inside:
            self.parts.append(f"<!--{data}-->")

    def body_html(self) -> str:
        return "".join(self.parts)


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


def render_local_article(
    title: str,
    source_url: str,
    published_at: dt.datetime,
    body: str,
    image_records: list[dict[str, Any]],
) -> str:
    for number, record in enumerate(image_records, start=1):
        placeholder = f"__WECHAT_LOCAL_IMAGE_{number:02d}__"
        local_name = Path(record["local_path"]).name
        body = body.replace(placeholder, f"images/{local_name}")
    if "__WECHAT_LOCAL_IMAGE_" in body:
        raise RuntimeError(f"Unresolved local image placeholder in: {title}")

    safe_title = html.escape(title)
    safe_url = html.escape(source_url, quote=True)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src 'self' data:; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>{safe_title}</title>
<style>
html {{ background: #f5f5f5; }}
body {{ box-sizing: border-box; max-width: 820px; margin: 0 auto; padding: 24px; background: white; color: #222; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; line-height: 1.75; overflow-wrap: anywhere; }}
.archive-meta {{ margin: 0 0 24px; padding: 12px 16px; border: 1px solid #ddd; border-radius: 8px; background: #fafafa; font-size: 14px; }}
.archive-meta a {{ color: #0969da; }}
#js_content {{ display: block !important; visibility: visible !important; opacity: 1 !important; max-width: 100% !important; }}
#js_content img {{ max-width: 100% !important; height: auto !important; }}
#js_content pre {{ overflow-x: auto; white-space: pre-wrap; }}
</style>
</head>
<body>
<header class="archive-meta">
<strong>本地正文 HTML 结构快照</strong><br>
发布时间：{published_at.isoformat()}<br>
官方页面：<a href="{safe_url}">{safe_url}</a><br>
说明：保留公众号 <code>#js_content</code> 的标签层次与内联样式；图片改为本地副本，脚本和外部资源被 CSP 禁用。
</header>
{body}
</body>
</html>
"""


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
    structured = ArticleHTMLExtractor()
    structured.feed(response.text)
    lines = extractor.normalized_lines()
    body_html = structured.body_html()
    if not lines or not body_html:
        raise RuntimeError(f"No article body extracted for: {title}")

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
    if structured.image_count != len(image_records):
        raise RuntimeError(
            f"HTML/text image counts differ for {title}: "
            f"{structured.image_count} != {len(image_records)}"
        )

    raw_html_path = article_dir / "original.raw.html"
    local_html_path = article_dir / "article.html"
    raw_html_path.write_bytes(response.content)
    local_html_path.write_text(
        render_local_article(title, url, created_at, body_html, image_records),
        encoding="utf-8",
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
        f"> HTML 证据：[本地正文结构视图](article.html) · [抓取原页](original.raw.html) · [公众号官方页面]({url})",
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
        "local_html_path": (relative_dir / "article.html").as_posix(),
        "raw_html_path": (relative_dir / "original.raw.html").as_posix(),
        "raw_html_sha256": hashlib.sha256(response.content).hexdigest(),
        "image_manifest_path": (relative_dir / "images.json").as_posix(),
        "body_characters": sum(len(line) for line in lines),
        "body_lines": len(lines),
        "content_images": len(image_records),
    }


def write_series_indexes(output_root: Path, articles: list[dict[str, Any]]) -> None:
    markdown = [
        "# 微信公众号原文归档",
        "",
        "本目录同时保留三种形态：",
        "",
        "- `article.html`：保留公众号正文 `#js_content` 标签层次和内联样式，图片已本地化；推荐克隆后用浏览器阅读；",
        "- `original.raw.html`：抓取时收到的完整原始页面 HTML，用于结构核验；可能依赖微信远程资源，不建议直接执行其中脚本；",
        "- `extracted.md`：供检索、审计和脚本处理的规范化纯文本，不追求还原公众号排版。",
        "",
        "本地阅读入口：直接用浏览器打开本目录的 `index.html`，或运行：",
        "",
        "```bash",
        "python -m http.server 8000 --directory sources/wechat-series",
        "```",
        "",
        "然后访问 <http://127.0.0.1:8000/>。",
        "",
        "| # | 标题 | 本地 HTML | 原始页面 HTML | 规范化文本 | 官方页面 |",
        "|---:|---|---|---|---|---|",
    ]
    html_items: list[str] = []
    for article in articles:
        number = article["series_number"]
        title = article["title"]
        markdown_title = title.replace("|", "\\|")
        slug = article["slug"]
        official = article["source_url"]
        markdown.append(
            f"| {number} | {markdown_title} | [阅读](articles/{slug}/article.html) | "
            f"[原页](articles/{slug}/original.raw.html) | "
            f"[文本](articles/{slug}/extracted.md) | [微信]({official}) |"
        )
        html_items.append(
            "<li>"
            f"<strong>{number}. {html.escape(title)}</strong><br>"
            f'<a href="articles/{html.escape(slug, quote=True)}/article.html">本地 HTML 结构视图</a> · '
            f'<a href="articles/{html.escape(slug, quote=True)}/extracted.md">规范化文本</a> · '
            f'<a href="{html.escape(official, quote=True)}">公众号官方页面</a>'
            "</li>"
        )

    (output_root / "README.md").write_text("\n".join(markdown) + "\n", encoding="utf-8")
    html_index = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'">
<title>微信公众号原文归档</title>
<style>body{max-width:820px;margin:40px auto;padding:0 20px;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;line-height:1.7}li{margin:18px 0}a{color:#0969da}</style>
</head><body><h1>微信公众号原文归档</h1>
<p>以下“本地 HTML 结构视图”保留正文标签层次与内联样式，并使用本地图片。</p><ol>
""" + "\n".join(html_items) + "\n</ol></body></html>\n"
    (output_root / "index.html").write_text(html_index, encoding="utf-8")


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
    write_series_indexes(output_root, index_articles)
    print(f"Wrote {output_root / 'index.json'} and local HTML indexes")


if __name__ == "__main__":
    main()
