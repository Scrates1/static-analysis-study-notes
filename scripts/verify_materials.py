#!/usr/bin/env python3
"""Verify the local course snapshot and final learning-note structure."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "sources/wechat-series/index.json"
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
    ROOT / "sources/README.md",
]
LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")


class Verification:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.notes: list[str] = []

    def require(self, condition: bool, message: str) -> None:
        if not condition:
            self.errors.append(message)

    def note(self, message: str) -> None:
        self.notes.append(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_source_path(relative: str) -> Path:
    path = Path(relative)
    if path.parts and path.parts[0] == "wechat-series":
        return ROOT / "sources" / path
    return ROOT / path


def verify_sources(check: Verification) -> None:
    check.require(INDEX.is_file(), "missing sources/wechat-series/index.json")
    if not INDEX.is_file():
        return
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    source = index.get("source", {})
    completeness = index.get("completeness", {})
    articles = index.get("articles", [])
    check.require(source.get("album_title") == "高校教学系列-程序分析", "unexpected album title")
    check.require(source.get("official_article_count") == 8, "official article count is not 8")
    check.require(len(articles) == 8, f"index lists {len(articles)} articles, expected 8")
    check.require(completeness.get("listed") == 8, "completeness.listed is not 8")
    check.require(completeness.get("extracted") == 8, "completeness.extracted is not 8")
    check.require(completeness.get("all_officially_listed_articles_extracted") is True, "article extraction flag is false")
    check.require(completeness.get("continue_flag_was_clear") is True, "album pagination was not exhausted")

    total_images = 0
    for article in articles:
        number = article.get("series_number")
        extracted = resolve_source_path(article.get("extracted_path", ""))
        manifest = resolve_source_path(article.get("image_manifest_path", ""))
        check.require(extracted.is_file(), f"article {number}: missing extracted text {extracted}")
        check.require(manifest.is_file(), f"article {number}: missing image manifest {manifest}")
        if not manifest.is_file():
            continue
        records = json.loads(manifest.read_text(encoding="utf-8"))
        expected_count = article.get("content_images")
        check.require(len(records) == expected_count, f"article {number}: manifest has {len(records)} images, expected {expected_count}")
        total_images += len(records)
        for position, record in enumerate(records, start=1):
            local = Path(record.get("local_path", ""))
            if not local.is_absolute():
                local = ROOT / local
            elif not local.exists():
                # Manifests retain the acquisition-time absolute path; fall back after relocation.
                local = manifest.parent / "images" / local.name
            check.require(local.is_file(), f"article {number} image {position}: missing {local}")
            if local.is_file() and record.get("sha256"):
                check.require(sha256(local) == record["sha256"], f"article {number} image {position}: SHA-256 mismatch")
    check.require(total_images == 109, f"found {total_images} article images, expected 109")
    check.note(f"official snapshot: {len(articles)}/8 articles, {total_images}/109 images")


def verify_yasa_docs(check: Verification) -> None:
    docs_root = ROOT / "sources/yasa-docs"
    index_path = docs_root / "index.json"
    yasa_docs = sorted(docs_root.glob("[0-9][0-9]-*.md"))
    sidecars = sorted(docs_root.glob("[0-9][0-9]-*.assets.json"))
    check.require(index_path.is_file(), "missing sources/yasa-docs/index.json")
    check.require(len(yasa_docs) == 21, f"found {len(yasa_docs)} normalized YASA docs, expected 21")
    check.require(len(sidecars) == 21, f"found {len(sidecars)} YASA asset sidecars, expected 21")
    if index_path.is_file():
        index = json.loads(index_path.read_text(encoding="utf-8"))
        check.require(len(index.get("documents", [])) == 21, "YASA document index does not list 21 documents")
    check.note(f"retained YASA docs: {len(yasa_docs)}/21 markdown, {len(sidecars)}/21 sidecars")


def verify_video_evidence(check: Verification, require_work: bool = False) -> None:
    metadata_path = ROOT / "sources/video-lessons-hd.json"
    check.require(metadata_path.is_file(), "missing sources/video-lessons-hd.json")
    lessons: list[dict] = []
    if metadata_path.is_file():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        lessons = metadata.get("lessons", metadata if isinstance(metadata, list) else [])
        check.require(len(lessons) == 3, f"video metadata contains {len(lessons)} lessons, expected 3")

    work_root = ROOT / ".work"
    if not work_root.exists():
        message = "local .work video/ASR/scene evidence is absent (expected in a clean Git clone)"
        if require_work:
            check.require(False, message)
        else:
            check.note(message + "; metadata and public links remain available")
        return

    for lesson in lessons:
        video = ROOT / lesson.get("downloaded_file", "")
        check.require(video.is_file(), f"missing lesson video: {video}")
        if video.is_file() and lesson.get("downloaded_bytes"):
            check.require(video.stat().st_size == lesson["downloaded_bytes"], f"lesson video size mismatch: {video}")
    transcripts = sorted((work_root / "transcripts").glob("lesson-*.md"))
    check.require(len(transcripts) == 3, f"found {len(transcripts)} transcripts, expected 3")
    segment_counts = [
        sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.startswith("- `"))
        for path in transcripts
    ]
    check.require(segment_counts == [678, 846, 631], f"transcript segment counts are {segment_counts}, expected [678, 846, 631]")
    scene_counts = []
    for directory in sorted((work_root / "lesson-scenes").glob("lesson-*")):
        if directory.is_dir():
            scene_counts.append(len(list(directory.glob("scene-*.jpg"))))
    check.require(scene_counts == [43, 30, 19], f"scene counts are {scene_counts}, expected [43, 30, 19]")
    check.note(
        f"local video evidence: {len(transcripts)}/3 transcripts, {sum(segment_counts)} segments, "
        f"{sum(scene_counts)} scene frames"
    )


def verify_markdown(check: Verification) -> None:
    for document in FINAL_DOCS:
        check.require(document.is_file(), f"missing final document: {document.relative_to(ROOT)}")
        if not document.is_file():
            continue
        text = document.read_text(encoding="utf-8")
        relative = document.relative_to(ROOT)
        check.require(text.startswith("# "), f"{relative}: first line is not an H1")
        check.require(text.count("```") % 2 == 0, f"{relative}: unbalanced fenced code blocks")
        if relative.parts and relative.parts[0] == "notes":
            check.require("[[IMAGE_" not in text, f"{relative}: unresolved image placeholder")
            check.require("[[CARD_" not in text, f"{relative}: unresolved Yuque card placeholder")
            check.require("详尽草稿" not in text and "专项研究草稿" not in text, f"{relative}: draft marker remains")
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
    check.note(f"final documents: {sum(path.is_file() for path in FINAL_DOCS)}/{len(FINAL_DOCS)} present")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--require-work-evidence",
        action="store_true",
        help="fail when ignored local videos, ASR, or scene frames are absent",
    )
    args = parser.parse_args()

    check = Verification()
    verify_sources(check)
    verify_yasa_docs(check)
    verify_video_evidence(check, require_work=args.require_work_evidence)
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
