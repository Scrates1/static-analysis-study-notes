#!/usr/bin/env python3
"""Download the three public Bilibili videos linked by the YASA lesson articles.

Video files are working material for note-taking and go to .work/video-lessons by
default. Metadata is kept separately so the source mapping remains reproducible.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import requests

LESSONS = [
    {
        "lesson": 1,
        "article": "YASA原理简介及功能演示",
        "bvid": "BV1y1mxBeEJu",
        "expected_cid": 34637155299,
    },
    {
        "lesson": 2,
        "article": "YASA内部机制深入解析",
        "bvid": "BV1RUqhB6EUG",
        "expected_cid": 34773205725,
    },
    {
        "lesson": 3,
        "article": "掌握Checker编写艺术",
        "bvid": "BV1x4BxB5EBH",
        "expected_cid": 34903559990,
    },
]
API = "https://api.bilibili.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
    "Referer": "https://www.bilibili.com/",
}


def api_json(client: requests.Session, path: str, **params: Any) -> dict[str, Any]:
    response = client.get(f"{API}{path}", params=params, timeout=60)
    response.raise_for_status()
    payload = response.json()
    if payload.get("code") != 0:
        raise RuntimeError(f"Bilibili API {path}: {payload}")
    return payload["data"]


def download(client: requests.Session, url: str, destination: Path) -> int:
    with client.get(url, stream=True, timeout=120) as response:
        response.raise_for_status()
        with destination.open("wb") as output:
            for chunk in response.iter_content(1024 * 1024):
                if chunk:
                    output.write(chunk)
    return destination.stat().st_size


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path(".work/video-lessons"))
    parser.add_argument("--metadata", type=Path, default=Path(".work/video-lessons.json"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    args.metadata.parent.mkdir(parents=True, exist_ok=True)

    client = requests.Session()
    client.headers.update(HEADERS)
    records = []
    for lesson in LESSONS:
        bvid = lesson["bvid"]
        view = api_json(client, "/x/web-interface/view", bvid=bvid)
        pages = view.get("pages") or []
        if len(pages) != 1:
            raise RuntimeError(f"Expected one page for {bvid}, got {len(pages)}")
        cid = int(pages[0]["cid"])
        if cid != lesson["expected_cid"]:
            raise RuntimeError(f"CID changed for {bvid}: {cid}")
        play = api_json(
            client, "/x/player/playurl", bvid=bvid, cid=cid, qn=64, fnval=0, fourk=0
        )
        durls = play.get("durl") or []
        if len(durls) != 1:
            raise RuntimeError(f"Expected one progressive stream for {bvid}")
        destination = args.output / f"lesson-{lesson['lesson']}-{bvid}.mp4"
        print(f"[{lesson['lesson']}/3] {view['title']}", flush=True)
        size = download(client, durls[0]["url"], destination)
        records.append({
            **lesson,
            "cid": cid,
            "aid": view.get("aid"),
            "title": view.get("title"),
            "description": view.get("desc"),
            "owner": view.get("owner"),
            "duration_seconds": view.get("duration"),
            "published_at_unix": view.get("pubdate"),
            "web_url": f"https://www.bilibili.com/video/{bvid}/",
            "downloaded_file": destination.as_posix(),
            "downloaded_bytes": size,
            "stream_quality": play.get("quality"),
            "stream_format": play.get("format"),
        })
    args.metadata.write_text(
        json.dumps({"lessons": records}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {args.metadata}")


if __name__ == "__main__":
    main()
