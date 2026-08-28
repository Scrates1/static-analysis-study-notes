#!/usr/bin/env python3
"""Fetch the public WeChat album and extract its article bodies for local study.

The script writes only GitHub-readable Markdown and the local content images
referenced by that Markdown. Full page HTML and JSON sidecars are intentionally
not retained in the study repository.
"""

from __future__ import annotations

import argparse
import datetime as dt
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
EXPERIMENT_VIDEO_URLS = {
    "YASA原理简介及功能演示": "https://www.bilibili.com/video/BV1y1mxBeEJu/",
    "YASA内部机制深入解析": "https://www.bilibili.com/video/BV1RUqhB6EUG/",
    "掌握Checker编写艺术": "https://www.bilibili.com/video/BV1x4BxB5EBH/",
}
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

    def __init__(self, inline_image_markers: bool = False) -> None:
        super().__init__(convert_charrefs=True)
        self.inline_image_markers = inline_image_markers
        self.depth = 0
        self.skip_depth = 0
        self.parts: list[str] = []
        self.images: list[dict[str, str]] = []
        self.links: list[str] = []
        self._active_link: str | None = None
        self.link_marker_stack: list[int | None] = []
        self.list_stack: list[str] = []

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
        preserve_list_marker = (
            self.inline_image_markers
            and tag in BLOCK_TAGS
            and self.parts
            and bool(re.fullmatch(r"\[\[LIST_\d+\]\](?:- |1\. )", self.parts[-1]))
        )
        if (tag in BLOCK_TAGS or tag == "br") and not preserve_list_marker:
            self._newline()
        if self.inline_image_markers and tag in {"ul", "ol"}:
            self.list_stack.append(tag)
        if self.inline_image_markers and tag == "li":
            depth = max(0, len(self.list_stack) - 1)
            marker = "1. " if self.list_stack and self.list_stack[-1] == "ol" else "- "
            self.parts.append(f"[[LIST_{depth}]]{marker}")
        if tag in {"td", "th"}:
            self.parts.append(" | ")
        if tag == "a":
            href = data.get("href", "")
            self._active_link = href
            marker_number: int | None = None
            if href:
                self.links.append(href)
                marker_number = len(self.links)
                if self.inline_image_markers:
                    self.parts.append(f"[[LINK_START_{marker_number:03d}]]")
            self.link_marker_stack.append(marker_number)
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
                marker = f"[[IMAGE_{len(self.images):02d}]]"
                self.parts.append(marker if self.inline_image_markers else f"\n{marker}\n")

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
            marker_number = self.link_marker_stack.pop() if self.link_marker_stack else None
            if self.inline_image_markers and marker_number is not None:
                self.parts.append(f"[[LINK_END_{marker_number:03d}]]")
            self._active_link = None
        if self.inline_image_markers and tag in {"ul", "ol"} and self.list_stack:
            self.list_stack.pop()
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


class CodeBlockExtractor(HTMLParser):
    """Recover source lines from WeChat's `<pre><code>…</code>…</pre>` layout."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.pre_depth = 0
        self.current: list[str] = []
        self.language = "text"
        self.blocks: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if not self.pre_depth and tag == "pre":
            data = {key.lower(): value or "" for key, value in attrs}
            language = data.get("data-lang") or data.get("lang") or "text"
            self.language = re.sub(r"[^0-9A-Za-z_+.-]", "", language) or "text"
            self.pre_depth = 1
            self.current = []
            return
        if not self.pre_depth:
            return
        if tag not in VOID_TAGS:
            self.pre_depth += 1
        if tag == "code" and self.current and not self.current[-1].endswith("\n"):
            self.current.append("\n")
        elif tag == "br":
            self.current.append("\n")

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self.pre_depth and tag.lower() == "br":
            self.current.append("\n")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if not self.pre_depth:
            return
        if tag == "code" and self.current and not self.current[-1].endswith("\n"):
            self.current.append("\n")
        if tag == "pre" and self.pre_depth == 1:
            code = "".join(self.current).replace("\xa0", " ").replace("\u200b", "")
            code_lines = [line.rstrip() for line in code.splitlines()]
            while code_lines and not code_lines[0].strip():
                code_lines.pop(0)
            while code_lines and not code_lines[-1].strip():
                code_lines.pop()
            self.blocks.append((self.language, "\n".join(code_lines)))
            self.current = []
            self.pre_depth = 0
            return
        if tag not in VOID_TAGS:
            self.pre_depth -= 1

    def handle_data(self, data: str) -> None:
        if self.pre_depth:
            self.current.append(data)


class TableBlockExtractor(HTMLParser):
    """Recover semantic rows from the article's real HTML tables."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.inside_table = False
        self.current_rows: list[list[str]] = []
        self.current_row: list[str] | None = None
        self.current_cell: list[str] | None = None
        self.blocks: list[list[list[str]]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag == "table" and not self.inside_table:
            self.inside_table = True
            self.current_rows = []
            return
        if not self.inside_table:
            return
        if tag == "tr":
            self.current_row = []
        elif tag in {"td", "th"}:
            self.current_cell = []
        elif tag == "br" and self.current_cell is not None:
            self.current_cell.append("\n")
        elif tag in {"p", "div", "li"} and self.current_cell:
            if not self.current_cell[-1].endswith("\n"):
                self.current_cell.append("\n")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if not self.inside_table:
            return
        if tag in {"td", "th"} and self.current_cell is not None:
            cell = "".join(self.current_cell).replace("\xa0", " ").replace("\u200b", "")
            cell = "<br>".join(
                re.sub(r"\s+", " ", part).strip()
                for part in cell.splitlines()
                if part.strip()
            )
            if self.current_row is not None:
                self.current_row.append(cell)
            self.current_cell = None
        elif tag == "tr" and self.current_row is not None:
            if any(cell for cell in self.current_row):
                self.current_rows.append(self.current_row)
            self.current_row = None
        elif tag == "table":
            if self.current_rows:
                self.blocks.append(self.current_rows)
            self.current_rows = []
            self.inside_table = False

    def handle_data(self, data: str) -> None:
        if self.inside_table and self.current_cell is not None:
            self.current_cell.append(data)


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


def repair_svg_for_rendering(content: bytes) -> tuple[bytes, bool]:
    """Repair MathJax SVG glyphs whose qpic copy lost the `<use>` reference."""
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        return content, False
    if "<svg" not in text or "<use" not in text:
        return content, False
    use_match = re.search(r"<use\b([^>]*)>", text)
    if not use_match or re.search(r"(?:href|xlink:href)\s*=", use_match.group(0)):
        return content, False
    path_match = re.search(r"<path\b([^>]*)>", text)
    if not path_match:
        return content, False

    glyph_id = "wechat-math-glyph"
    if not re.search(r"\bid\s*=", path_match.group(0)):
        replacement = path_match.group(0).replace("<path", f'<path id="{glyph_id}"', 1)
        text = text[:path_match.start()] + replacement + text[path_match.end():]
    else:
        id_match = re.search(r"\bid\s*=\s*[\"']([^\"']+)", path_match.group(0))
        if not id_match:
            return content, False
        glyph_id = id_match.group(1)

    use_match = re.search(r"<use\b", text)
    if not use_match:
        return content, False
    text = text[:use_match.end()] + f' xlink:href="#{glyph_id}"' + text[use_match.end():]
    return text.encode("utf-8"), True


def fetch_image(client: requests.Session, record: dict[str, str], stem: Path) -> dict[str, Any]:
    response = client.get(record["source_url"], timeout=90)
    response.raise_for_status()
    content_type = response.headers.get("content-type", "application/octet-stream")
    suffix = extension_for(content_type, record["source_url"])
    destination = stem.with_suffix(suffix)
    source_content = response.content
    local_content, _ = repair_svg_for_rendering(source_content)
    destination.write_bytes(local_content)
    return {**record, "local_path": destination.as_posix()}


def image_width_hint(record: dict[str, Any]) -> int | None:
    style = record.get("style", "")
    if "border-radius: 50%" in style or "border-radius:50%" in style:
        return 96
    match = re.search(r"(?:^|;)\s*width\s*:\s*([0-9]+(?:\.[0-9]+)?)px", style)
    if not match:
        return None
    return max(1, min(760, round(float(match.group(1)))))


def render_image(record: dict[str, Any], number: int, block: bool) -> str:
    filename = Path(record["local_path"]).name
    alt = record.get("alt") or f"原文图片 {number:02d}"
    width = image_width_hint(record)
    width_attr = f' width="{width}"' if width else ""
    image = (
        f'<img src="images/{html.escape(filename, quote=True)}" '
        f'alt="{html.escape(alt, quote=True)}"{width_attr}>'
    )
    return f'<p align="center">{image}</p>' if block else image


def render_link_markers(text: str, links: list[str]) -> str:
    pattern = re.compile(r"\[\[LINK_START_(\d{3})\]\](.*?)\[\[LINK_END_\1\]\]")

    def replace(match: re.Match[str]) -> str:
        number = int(match.group(1))
        content = match.group(2).strip()
        if not content or not 1 <= number <= len(links):
            return content
        href = links[number - 1]
        if "<img " in content:
            return f'<a href="{html.escape(href, quote=True)}">{content}</a>'
        return f"[{content}]({href})"

    rendered = pattern.sub(replace, text)
    if "[[LINK_" in rendered:
        raise RuntimeError(f"Unresolved inline link marker: {rendered[:160]}")
    return rendered


def render_table(rows: list[list[str]]) -> str:
    width = max(len(row) for row in rows)
    padded = [row + [""] * (width - len(row)) for row in rows]

    def row_text(row: list[str]) -> str:
        cells = [cell.replace("|", r"\|") for cell in row]
        return "| " + " | ".join(cells) + " |"

    return "\n".join([
        row_text(padded[0]),
        "| " + " | ".join(["---"] * width) + " |",
        *(row_text(row) for row in padded[1:]),
    ])


def code_language_hint(declared: str, code: str) -> str:
    stripped = code.lstrip()
    if re.search(r"(?m)^(?:def |from \S+ import |import \S+)", stripped):
        return "python"
    if re.search(r"(?m)^define\s+\w+\s+@", stripped) or " icmp " in code:
        return "llvm"
    if (
        ";" in code
        and re.search(r"(?:#include|\b(?:void|int|char|float|double)\s+\w+|malloc\s*\(|\bgoto\b)", code)
    ):
        return "c"
    if re.search(r"(?m)^\s*(?:\$\s+|git |python\d* |java |mvn |gradle |\./)", code):
        return "bash"
    return declared if declared in {"python", "json", "yaml", "xml", "html"} else "text"


def render_readable_markdown(
    title: str,
    source_url: str,
    published_at: dt.datetime,
    lines: list[str],
    image_records: list[dict[str, Any]],
    code_blocks: list[tuple[str, str]] | None = None,
    table_blocks: list[list[list[str]]] | None = None,
    links: list[str] | None = None,
    video_url: str | None = None,
) -> str:
    code_placements: dict[int, tuple[int, str, str]] = {}
    search_from = 0
    for language, code in code_blocks or []:
        target = re.sub(r"\s+", "", code)
        if not target:
            continue
        placement: tuple[int, int] | None = None
        for start in range(search_from, len(lines)):
            combined = ""
            for end in range(start, len(lines)):
                combined += re.sub(r"\s+", "", lines[end])
                if not combined:
                    continue
                if combined == target:
                    placement = (start, end)
                    break
                if not target.startswith(combined):
                    break
            if placement:
                break
        if not placement:
            raise RuntimeError(f"Could not place an HTML code block in Markdown: {title}")
        start, end = placement
        code_placements[start] = (end, language, code)
        search_from = end + 1

    table_placements: dict[int, tuple[int, list[list[str]]]] = {}
    table_search_from = 0
    for rows in table_blocks or []:
        target = re.sub(r"(?:<br>)|[\s|]+", "", "".join(cell for row in rows for cell in row))
        placement: tuple[int, int] | None = None
        for start in range(table_search_from, len(lines)):
            combined = ""
            for end in range(start, len(lines)):
                combined += re.sub(r"[\s|]+", "", lines[end])
                if not combined:
                    continue
                if combined == target:
                    placement = (start, end)
                    break
                if not target.startswith(combined):
                    break
            if placement:
                break
        if not placement:
            raise RuntimeError(f"Could not place an HTML table in Markdown: {title}")
        start, end = placement
        table_placements[start] = (end, rows)
        table_search_from = end + 1

    output = [
        f"# {title}",
        "",
        "[← 返回微信原文目录](../../README.md)",
        "",
        "> **归档信息**",
        ">",
        f"> **发布时间**：{published_at.isoformat()}<br>",
        f"> **公众号原文**：[打开官方页面]({source_url})<br>",
        *([f"> **配套视频**：[在 Bilibili 观看]({video_url})<br>"] if video_url else []),
        "> **归档说明**：正文顺序、原图和代码块均由公众号原文整理；本目录仅保留 GitHub 可直接阅读的 Markdown 版本。",
        "",
        "---",
        "",
    ]
    expect_part_title = False
    inside_part = False
    in_references = False
    in_related_reading = False
    index = 0
    while index < len(lines):
        if index in table_placements:
            end, rows = table_placements[index]
            output.extend([render_table(rows), ""])
            expect_part_title = False
            index = end + 1
            continue
        if index in code_placements:
            end, language, code = code_placements[index]
            fence = "````" if "```" in code else "```"
            output.extend([f"{fence}{code_language_hint(language, code)}", code, fence, ""])
            expect_part_title = False
            index = end + 1
            continue

        line = lines[index]
        index += 1
        list_marker = re.match(r"^\[\[LIST_(\d+)\]\](.*)$", line)
        if list_marker:
            line = "    " * int(list_marker.group(1)) + list_marker.group(2)
        if not line.strip() or line.strip() in {"∨", "-", "1."}:
            continue

        image_matches = list(re.finditer(r"\[\[IMAGE_(\d+)\]\]", line))
        if image_matches:
            for match in image_matches:
                number = int(match.group(1))
                if not 1 <= number <= len(image_records):
                    raise RuntimeError(f"Image marker out of range in {title}: {line}")
            single_image = re.fullmatch(r"\s*\[\[IMAGE_(\d+)\]\]\s*", line)
            if single_image:
                number = int(single_image.group(1))
                rendered = render_image(image_records[number - 1], number, block=True)
            else:
                def replace_image(match: re.Match[str]) -> str:
                    number = int(match.group(1))
                    return render_image(image_records[number - 1], number, block=False)
                rendered = re.sub(r"\[\[IMAGE_(\d+)\]\]", replace_image, line)
            rendered = render_link_markers(rendered, links or [])
            output.extend([rendered, ""])
            expect_part_title = False
            continue

        line = render_link_markers(line, links or [])
        if (
            video_url
            and "视频" in line
            and ("bilibili" in line.lower() or "阅读原文" in line)
            and video_url not in line
        ):
            line += f" [点击观看配套视频]({video_url})"
        part_match = re.fullmatch(r"Part\s+(\d+)", line, flags=re.IGNORECASE)
        if part_match:
            output.extend([f"## Part {part_match.group(1)}", ""])
            inside_part = True
            expect_part_title = True
            continue

        if expect_part_title and 0 < len(line) <= 80:
            output.extend([f"### {line}", ""])
            expect_part_title = False
            continue
        expect_part_title = False

        section_match = re.match(r"^(\d+(?:\.\d+)+)\s+(.+)$", line)
        if section_match and len(line) <= 120:
            depth = min(6, 3 + section_match.group(1).count("."))
            output.extend([f"{'#' * depth} {line}", ""])
            continue

        if line.strip() in {"参考文献", "参考资料", "Reference", "References", "总结", "小结", "关联阅读"}:
            heading = line.strip()
            level = "###" if inside_part else "##"
            output.extend([f"{level} {heading}", ""])
            in_references = heading in {"参考文献", "参考资料", "Reference", "References"}
            in_related_reading = heading == "关联阅读"
            continue

        if in_related_reading:
            if re.match(r"^\[[^]]+\]\(https?://", line):
                line = f"- {line}"
            else:
                in_related_reading = False

        reference_item = re.match(r"^\[(\d+)\]\s*(.+)$", line) if in_references else None
        if reference_item:
            following = index
            while following < len(lines) and not lines[following].strip():
                following += 1
            citation = reference_item.group(2)
            if following < len(lines) and re.match(r"https?://", lines[following].strip()):
                citation += f" — <{lines[following].strip()}>"
                index = following + 1
            line = f"{reference_item.group(1)}. {citation}"

        ordered_item = re.match(r"^(\d+)[.、](?!\d)(\S.*)$", line)
        if ordered_item:
            line = f"{ordered_item.group(1)}. {ordered_item.group(2)}"
        else:
            bullet_item = re.match(r"^[●•▪]\s*(.+)$", line)
            if bullet_item:
                line = f"- {bullet_item.group(1)}"
        is_list_item = bool(re.match(r"^\s*(?:- |\d+\. )", line))
        previous_is_list_item = (
            len(output) >= 2
            and output[-1] == ""
            and bool(re.match(r"^\s*(?:- |\d+\. )", output[-2]))
        )
        if is_list_item and previous_is_list_item:
            output.pop()
        output.extend([line, ""])

    while output and not output[-1]:
        output.pop()
    output.extend([
        "",
        "---",
        "",
        "[← 返回微信原文目录](../../README.md) · [查看公众号原文](" + source_url + ")",
    ])
    return "\n".join(output) + "\n"


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

    markdown_extractor = ArticleExtractor(inline_image_markers=True)
    markdown_extractor.feed(response.text)
    code_extractor = CodeBlockExtractor()
    code_extractor.feed(response.text)
    table_extractor = TableBlockExtractor()
    table_extractor.feed(response.text)
    lines = markdown_extractor.normalized_lines()
    if not lines:
        raise RuntimeError(f"No article body extracted for: {title}")

    for stale_image in assets_dir.glob("image-*"):
        if stale_image.is_file():
            stale_image.unlink()
    image_records: list[dict[str, Any]] = []
    for image_number, image in enumerate(markdown_extractor.images, start=1):
        image_records.append(
            fetch_image(client, image, assets_dir / f"image-{image_number:02d}")
        )
        if pause:
            time.sleep(pause)

    created_at = dt.datetime.fromtimestamp(
        int(article["create_time"]), tz=dt.timezone(dt.timedelta(hours=8))
    )
    if len(markdown_extractor.images) != len(image_records):
        raise RuntimeError(
            f"Markdown/downloaded image counts differ for {title}: "
            f"{len(markdown_extractor.images)} != {len(image_records)}"
        )

    readable_markdown_path = article_dir / "article.md"
    video_url = next(
        (video for fragment, video in EXPERIMENT_VIDEO_URLS.items() if fragment in title),
        None,
    )
    readable_markdown_path.write_text(
        render_readable_markdown(
            title,
            url,
            created_at,
            markdown_extractor.normalized_lines(),
            image_records,
            code_extractor.blocks,
            table_extractor.blocks,
            markdown_extractor.links,
            video_url,
        ),
        encoding="utf-8",
    )

    return {
        "series_number": number,
        "title": title,
        "source_url": url,
        "slug": slug,
        "content_images": len(image_records),
    }


def write_series_readme(output_root: Path, articles: list[dict[str, Any]]) -> None:
    markdown = [
        "# 微信公众号课程原文（Markdown）",
        "",
        "本目录只保留适合 GitHub 直接阅读的资料：",
        "",
        f"- {len(articles)} 篇 `article.md`：恢复标题层级、列表、表格、代码块、原文链接和配套视频；",
        f"- {sum(article.get('content_images', 0) for article in articles)} 张 `images/` 本地图片：供 Markdown 正文引用，不能单独删除；",
        "- 每篇文章顶部均保留公众号官方页面链接。",
        "",
        "| # | 文章 | GitHub 阅读 |",
        "|---:|---|---|",
    ]
    for article in articles:
        title = article["title"].replace("|", "\\|")
        markdown.append(
            f"| {article['series_number']} | {title} | "
            f"[直接阅读](articles/{article['slug']}/article.md) |"
        )
    (output_root / "README.md").write_text("\n".join(markdown) + "\n", encoding="utf-8")


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

    official_count = int(base_info.get("article_count", 0))
    complete = len(index_articles) == official_count
    write_series_readme(output_root, index_articles)
    summary = {
        "album_title": base_info.get("title", ""),
        "official_article_count": official_count,
        "written_markdown": len(index_articles),
        "written_images": sum(article["content_images"] for article in index_articles),
        "is_updating": base_info.get("isupdating") == "1",
        "complete": complete,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if not complete:
        raise RuntimeError("Not all officially listed articles were written")


if __name__ == "__main__":
    main()
