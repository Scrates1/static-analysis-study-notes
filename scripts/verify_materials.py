#!/usr/bin/env python3
"""Verify the lean Markdown-only course snapshot and learning-note structure."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "sources"
WECHAT = SOURCES / "wechat-series"
ARTICLE_ROOT = WECHAT / "articles"
EXPECTED_IMAGE_COUNTS = [3, 10, 4, 51, 33, 3, 2, 3]
EXPECTED_VIDEO_IDS = {"BV1y1mxBeEJu", "BV1RUqhB6EUG", "BV1x4BxB5EBH"}
ALLOWED_SOURCE_SUFFIXES = {".md", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}
FINAL_DOCS = [
    ROOT / "README.md",
    ROOT / "00-系列索引与完整性.md",
    ROOT / "notes/01-静态分析基础与中间表示.md",
    ROOT / "notes/02-数据流分析.md",
    ROOT / "notes/03-指针分析与抽象解释.md",
    ROOT / "notes/04-YASA三次实验.md",
    ROOT / "公式与术语速查.md",
    ROOT / "勘误与辨析.md",
    ROOT / "练习与参考答案.md",
    ROOT / "学习路线.md",
    ROOT / "参考资料.md",
    SOURCES / "README.md",
]
LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")
IMAGE_RE = re.compile(r"(?:src=[\"']|\]\()images/(image-[^\"'\s)>]+)")
FORBIDDEN_REFERENCES = (
    "sources/video-lessons",
    "wechat-series/index.json",
    "yasa-docs/index.json",
    "original.raw.html",
    "extracted.md",
    "images.json",
    ".assets.json",
)


class Verification:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.notes: list[str] = []

    def require(self, condition: bool, message: str) -> None:
        if not condition:
            self.errors.append(message)

    def note(self, message: str) -> None:
        self.notes.append(message)


def valid_image(path: Path, check: Verification, label: str) -> None:
    suffix = path.suffix.lower()
    if suffix == ".svg":
        text = path.read_text(encoding="utf-8")
        check.require("<svg" in text, f"{label}: invalid SVG root")
        if "<use" in text:
            check.require(
                bool(re.search(r"<use\b[^>]*(?:xlink:href|href)=", text)),
                f"{label}: SVG use has no glyph reference",
            )
        return

    header = path.read_bytes()[:16]
    valid = {
        ".png": header.startswith(b"\x89PNG\r\n\x1a\n"),
        ".jpg": header.startswith(b"\xff\xd8\xff"),
        ".jpeg": header.startswith(b"\xff\xd8\xff"),
        ".gif": header.startswith((b"GIF87a", b"GIF89a")),
        ".webp": header.startswith(b"RIFF") and header[8:12] == b"WEBP",
    }.get(suffix, False)
    check.require(valid, f"{label}: invalid {suffix} signature")


def verify_source_shape(check: Verification) -> None:
    files = [path for path in SOURCES.rglob("*") if path.is_file()]
    unexpected = [
        path.relative_to(ROOT).as_posix()
        for path in files
        if path.suffix.lower() not in ALLOWED_SOURCE_SUFFIXES
    ]
    check.require(not unexpected, f"non-Markdown source artifacts remain: {unexpected}")
    check.require(not list(SOURCES.rglob("*.html")), "HTML files remain under sources/")
    check.require(not list(SOURCES.rglob("*.json")), "JSON sidecars remain under sources/")
    check.note(f"lean sources layout: {len(files)} files; Markdown plus required images only")


def verify_wechat(check: Verification) -> None:
    check.require((WECHAT / "README.md").is_file(), "missing WeChat Markdown index")
    article_dirs = sorted(path for path in ARTICLE_ROOT.glob("[0-9][0-9]-*") if path.is_dir())
    check.require(len(article_dirs) == 8, f"found {len(article_dirs)} WeChat article directories, expected 8")

    total_images = 0
    video_headers = 0
    video_ids: set[str] = set()
    svg_count = 0
    for number, article_dir in enumerate(article_dirs, start=1):
        article = article_dir / "article.md"
        check.require(article.is_file(), f"article {number}: missing article.md")
        direct_files = sorted(path.name for path in article_dir.iterdir() if path.is_file())
        check.require(direct_files == ["article.md"], f"article {number}: redundant direct files remain: {direct_files}")
        if not article.is_file():
            continue

        text = article.read_text(encoding="utf-8")
        check.require(text.startswith("# "), f"article {number}: Markdown lacks H1")
        check.require("mp.weixin.qq.com" in text, f"article {number}: official source link is absent")
        check.require(text.count("```") % 2 == 0, f"article {number}: unbalanced code fences")
        check.require(
            not any(marker in text for marker in ("[[IMAGE_", "[[LINK_", "[[LIST_")),
            f"article {number}: unresolved renderer marker",
        )
        check.require(not re.search(r"(?m)^∨$", text), f"article {number}: decorative placeholder remains")

        references = IMAGE_RE.findall(text)
        images_dir = article_dir / "images"
        local_images = sorted(path for path in images_dir.glob("image-*") if path.is_file())
        expected = EXPECTED_IMAGE_COUNTS[number - 1] if number <= len(EXPECTED_IMAGE_COUNTS) else -1
        check.require(len(references) == expected, f"article {number}: {len(references)} image references, expected {expected}")
        check.require(len(local_images) == expected, f"article {number}: {len(local_images)} image files, expected {expected}")
        check.require(
            references == [path.name for path in local_images],
            f"article {number}: image references and local files differ",
        )
        total_images += len(local_images)
        for position, image in enumerate(local_images, start=1):
            valid_image(image, check, f"article {number} image {position}")
            svg_count += image.suffix.lower() == ".svg"

        video_headers += text.count("**配套视频**")
        video_ids.update(re.findall(r"BV[0-9A-Za-z]+", text))

    check.require(total_images == 109, f"found {total_images} WeChat images, expected 109")
    check.require(svg_count == 3, f"found {svg_count} SVG images, expected 3")
    check.require(video_headers == 3, f"found {video_headers} companion-video headers, expected 3")
    check.require(EXPECTED_VIDEO_IDS <= video_ids, f"missing companion video IDs: {sorted(EXPECTED_VIDEO_IDS - video_ids)}")
    check.note(f"WeChat reading set: {len(article_dirs)}/8 Markdown, {total_images}/109 images, {svg_count}/3 SVG")


def verify_yasa_docs(check: Verification) -> None:
    docs_root = SOURCES / "yasa-docs"
    check.require((docs_root / "README.md").is_file(), "missing YASA Markdown index")
    docs = sorted(docs_root.glob("[0-9][0-9]-*.md"))
    check.require(len(docs) == 21, f"found {len(docs)} YASA Markdown docs, expected 21")
    markdown_images = 0
    for document in docs:
        text = document.read_text(encoding="utf-8")
        check.require(text.startswith("---\n"), f"{document.name}: missing front matter")
        check.require("\nsource_url: " in text, f"{document.name}: source URL missing from front matter")
        check.require("\n# " in text, f"{document.name}: document H1 missing")
        check.require(
            "[[CARD_" not in text and "[[IMAGE_" not in text,
            f"{document.name}: unresolved Yuque placeholder",
        )
        check.require(text.count("```") % 2 == 0, f"{document.name}: unbalanced code fences")
        markdown_images += len(re.findall(r"!\[[^\]]*\]\(https?://", text))
    check.require(markdown_images == 4, f"found {markdown_images} YASA Markdown images, expected 4")
    check.note(f"YASA reading set: {len(docs)}/21 Markdown documents, {markdown_images}/4 linked images")


def verify_work_evidence(check: Verification, require_work: bool = False) -> None:
    work_root = ROOT / ".work"
    if not work_root.exists():
        message = "ignored .work video/ASR/scene evidence is absent (normal in a clean clone)"
        if require_work:
            check.require(False, message)
        else:
            check.note(message)
        return

    transcripts = sorted((work_root / "transcripts").glob("lesson-*.md"))
    scene_counts = [
        len(list(directory.glob("scene-*.jpg")))
        for directory in sorted((work_root / "lesson-scenes").glob("lesson-*"))
        if directory.is_dir()
    ]
    if require_work:
        check.require(len(transcripts) == 3, f"found {len(transcripts)} transcripts, expected 3")
        check.require(scene_counts == [43, 30, 19], f"scene counts are {scene_counts}, expected [43, 30, 19]")
    check.note(f"optional local evidence: {len(transcripts)} transcripts, {sum(scene_counts)} scene frames")


def verify_markdown(check: Verification) -> None:
    documents = FINAL_DOCS + sorted(SOURCES.rglob("*.md"))
    seen: set[Path] = set()
    for document in documents:
        if document in seen:
            continue
        seen.add(document)
        check.require(document.is_file(), f"missing Markdown document: {document.relative_to(ROOT)}")
        if not document.is_file():
            continue
        text = document.read_text(encoding="utf-8")
        relative = document.relative_to(ROOT)
        if document in FINAL_DOCS:
            check.require(text.startswith("# "), f"{relative}: first line is not an H1")
        check.require(text.count("```") % 2 == 0, f"{relative}: unbalanced fenced code blocks")
        for stale in FORBIDDEN_REFERENCES:
            check.require(stale not in text, f"{relative}: stale reference to removed artifact {stale}")

        link_text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
        for match in LINK_RE.finditer(link_text):
            raw = match.group(1).strip()
            target = raw.split(maxsplit=1)[0].strip("<>")
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target = unquote(target.split("#", 1)[0])
            if not target:
                continue
            linked = (document.parent / target).resolve()
            check.require(linked.exists(), f"{relative}: broken local link {raw}")
    check.note(f"Markdown/link checks: {len(seen)} documents")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--require-work-evidence",
        action="store_true",
        help="fail when ignored local ASR or scene evidence is absent",
    )
    args = parser.parse_args()

    check = Verification()
    verify_source_shape(check)
    verify_wechat(check)
    verify_yasa_docs(check)
    verify_work_evidence(check, require_work=args.require_work_evidence)
    verify_markdown(check)
    for note in check.notes:
        print(f"OK: {note}")
    if check.errors:
        for error in check.errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"Verification failed with {len(check.errors)} error(s).", file=sys.stderr)
        return 1
    print("Verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
