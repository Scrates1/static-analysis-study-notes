#!/usr/bin/env python3
"""Fetch public YASA Yuque documents that substantiate the experimental lessons."""

from __future__ import annotations

import html
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote

import requests

BOOK_ID = 69470335
BOOK_BASE = "https://www.yuque.com/u22090306/bebf6g"
DOCS = [
    ("qgswkd2qa07yr5z2", "名词解释"),
    ("gm7b32tcn9vosgll", "安装部署"),
    ("uuupnlgx4pkbrmv5", "操作手册"),
    ("okuzgsdc66gbmk39", "污点分析"),
    ("zkw8i3ffw8n884sd", "ruleConfig配置"),
    ("ouenen3i3en236ek", "内置Checker介绍"),
    ("mzaslh9b1hook19l", "AST查询"),
    ("ahif12ik3vnapoin", "获取CallGraph"),
    ("dgyshe6zve9tuef2", "自定义分析"),
    ("wtucc3wf7gzwkuhs", "YASA-UAST设计"),
    ("idrc3p344fz19h4g", "YASA-Engine设计"),
    ("lwe1xqg1nw1gh1u8", "Checker设计"),
    ("as70rglyr24h3tqc", "Checker开发文档"),
    ("axsqw5texifp1mmq", "Checker与rule-config设计"),
    ("bow6bkg8xwm9flew", "Checker研发案例"),
    ("tzw6osk2hh5wst22", "寻找空函数"),
    ("yys952qa6ibu94fi", "统计超长文件"),
    ("ffds4irumtmmd4am", "支持新框架污点分析"),
    ("kf9yhos9qxhtflos", "Go-mux框架Checker"),
    ("tsxs2vcvs5aq5xym", "Django框架Checker"),
    ("sr0y5fqg0kcua5nf", "华中科技大学教学合作课程"),
]
BLOCKS = {
    "address", "article", "aside", "blockquote", "div", "figcaption", "figure",
    "h1", "h2", "h3", "h4", "h5", "h6", "hr", "li", "ol", "p", "pre",
    "section", "table", "tbody", "tfoot", "thead", "tr", "ul",
}


class LakeExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.links: list[str] = []
        self.images: list[str] = []
        self.cards: list[dict] = []
        self.code_depth = 0

    def newline(self) -> None:
        if self.parts and not self.parts[-1].endswith("\n"):
            self.parts.append("\n")

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = {key: value or "" for key, value in attrs}
        if tag in BLOCKS or tag == "br":
            self.newline()
        if tag in {"td", "th"}:
            self.parts.append(" | ")
        if tag in {"pre", "code"}:
            self.code_depth += 1
        if tag == "a" and data.get("href"):
            self.links.append(data["href"])
        if tag == "img" and data.get("src"):
            self.images.append(data["src"])
            self.parts.append(f"\n[[IMAGE_{len(self.images):02d}]]\n")
        if tag == "card":
            card = dict(data)
            value = card.get("value", "")
            if value.startswith("data:"):
                try:
                    card["decoded_value"] = json.loads(unquote(value[5:]))
                except Exception:
                    card["decoded_value"] = unquote(value[5:])
            self.cards.append(card)
            marker = f"[[CARD_{len(self.cards):02d}]]"
            decoded = card.get("decoded_value")
            if isinstance(decoded, dict) and card.get("name") == "codeblock" and decoded.get("code"):
                language = decoded.get("mode") or "text"
                self.parts.append(f"\n{marker}\n```{language}\n{decoded['code']}\n```\n")
            elif isinstance(decoded, dict) and card.get("name") == "file":
                self.parts.append(
                    f"\n{marker} [附件：{decoded.get('name', '')}]({decoded.get('src', '')})\n"
                )
            elif isinstance(decoded, dict) and card.get("name") == "board":
                labels: list[str] = []
                body = decoded.get("diagramData", {}).get("body", [])
                for element in body:
                    label = element.get("html") if isinstance(element, dict) else ""
                    if label:
                        label = html.unescape(re.sub(r"<[^>]+>", " ", label))
                        label = re.sub(r"\s+", " ", label).strip()
                        if label and label not in labels:
                            labels.append(label)
                self.parts.append(f"\n{marker} [图示文字：{' → '.join(labels)}]\n")
            else:
                self.parts.append(f"\n{marker}\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"pre", "code"} and self.code_depth:
            self.code_depth -= 1
        if tag in BLOCKS:
            self.newline()

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def lines(self) -> list[str]:
        raw = "".join(self.parts).replace("\xa0", " ").replace("\u200b", "")
        lines: list[str] = []
        blank = True
        for line in raw.splitlines():
            line = re.sub(r"[ \t\r\f\v]+", " ", line).strip()
            if not line:
                if not blank and lines:
                    lines.append("")
                blank = True
                continue
            lines.append(html.unescape(line))
            blank = False
        while lines and not lines[-1]:
            lines.pop()
        return lines


def main() -> None:
    output = Path("sources/yasa-docs")
    output.mkdir(parents=True, exist_ok=True)
    client = requests.Session()
    client.headers.update({
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
        "Accept": "application/json",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": f"{BOOK_BASE}/sr0y5fqg0kcua5nf",
    })
    records = []
    for number, (slug, label) in enumerate(DOCS, start=1):
        response = client.get(
            f"https://www.yuque.com/api/docs/{slug}",
            params={
                "book_id": BOOK_ID,
                "include_contributors": "false",
                "include_like": "false",
                "include_hits": "false",
                "merge_dynamic_data": "false",
            },
            timeout=90,
        )
        response.raise_for_status()
        payload = response.json()
        if not payload.get("data"):
            raise RuntimeError(f"No document data for {slug}: {payload}")
        document = payload["data"]
        extractor = LakeExtractor()
        extractor.feed(document.get("content", ""))
        safe_label = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "-", label).strip("-")
        destination = output / f"{number:02d}-{safe_label}.md"
        header = [
            "---",
            f"title: {json.dumps(document.get('title', label), ensure_ascii=False)}",
            f"slug: {slug}",
            f"source_url: {BOOK_BASE}/{slug}",
            f"updated_at: {document.get('updated_at', '')}",
            f"word_count: {document.get('word_count', 0)}",
            f"image_count: {len(extractor.images)}",
            f"card_count: {len(extractor.cards)}",
            "---",
            "",
            f"# {document.get('title', label)}",
            "",
        ]
        destination.write_text("\n".join(header + extractor.lines()) + "\n", encoding="utf-8")
        sidecar = destination.with_suffix(".assets.json")
        sidecar.write_text(
            json.dumps(
                {"links": extractor.links, "images": extractor.images, "cards": extractor.cards},
                ensure_ascii=False,
                indent=2,
            ) + "\n",
            encoding="utf-8",
        )
        records.append({
            "title": document.get("title", label),
            "slug": slug,
            "source_url": f"{BOOK_BASE}/{slug}",
            "updated_at": document.get("updated_at"),
            "word_count": document.get("word_count"),
            "extracted_path": destination.as_posix(),
            "assets_path": sidecar.as_posix(),
            "image_count": len(extractor.images),
            "card_count": len(extractor.cards),
        })
        print(f"[{number}/{len(DOCS)}] {document.get('title', label)}", flush=True)
    (output / "index.json").write_text(
        json.dumps({"book_id": BOOK_ID, "documents": records}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
