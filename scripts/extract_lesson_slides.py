#!/usr/bin/env python3
"""Extract likely slide/application changes from the 720p YASA lesson videos."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import av
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def format_time(seconds: float) -> str:
    total = int(round(seconds))
    return f"{total // 3600:02d}-{(total % 3600) // 60:02d}-{total % 60:02d}"


def frame_signature(image: Image.Image) -> np.ndarray:
    # Ignore a narrow border where compression noise/watermarks tend to live.
    width, height = image.size
    cropped = image.crop((int(width * 0.02), int(height * 0.02), int(width * 0.98), int(height * 0.94)))
    return np.asarray(cropped.convert("L").resize((160, 90)), dtype=np.float32)


def extract(video: Path, output: Path, sample_seconds: float, threshold: float) -> list[dict]:
    output.mkdir(parents=True, exist_ok=True)
    container = av.open(str(video))
    stream = container.streams.video[0]
    next_sample = 0.0
    previous_signature = None
    pending: tuple[float, float, Image.Image] | None = None
    selected: list[tuple[float, float, Image.Image]] = []

    for frame in container.decode(stream):
        timestamp = float(frame.pts * frame.time_base) if frame.pts is not None else 0.0
        if timestamp + 1e-6 < next_sample:
            continue
        next_sample += sample_seconds
        image = frame.to_image().convert("RGB")
        signature = frame_signature(image)
        if previous_signature is None:
            selected.append((timestamp, 999.0, image.copy()))
            previous_signature = signature
            continue
        difference = float(np.mean(np.abs(signature - previous_signature)))
        previous_signature = signature
        if difference < threshold:
            # Flush a transition cluster after its visual changes settle.
            if pending and timestamp - pending[0] >= max(2.0, sample_seconds * 2):
                selected.append(pending)
                pending = None
            continue
        if pending is None or difference >= pending[1]:
            pending = (timestamp, difference, image.copy())
        elif timestamp - pending[0] >= max(2.0, sample_seconds * 2):
            selected.append(pending)
            pending = (timestamp, difference, image.copy())
    if pending:
        selected.append(pending)
    container.close()

    records = []
    for number, (timestamp, difference, image) in enumerate(selected, start=1):
        filename = f"scene-{number:03d}-{format_time(timestamp)}.jpg"
        image.save(output / filename, quality=92, optimize=True)
        records.append({
            "scene": number,
            "timestamp_seconds": round(timestamp, 3),
            "difference_score": round(difference, 3),
            "file": (output / filename).as_posix(),
        })
    return records


def contact_sheets(records: list[dict], output: Path, columns: int = 3, rows: int = 3) -> list[str]:
    per_sheet = columns * rows
    thumb_width, thumb_height = 400, 225
    label_height = 28
    result = []
    for sheet_index, start in enumerate(range(0, len(records), per_sheet), start=1):
        subset = records[start : start + per_sheet]
        sheet = Image.new("RGB", (columns * thumb_width, rows * (thumb_height + label_height)), "white")
        draw = ImageDraw.Draw(sheet)
        for local_index, record in enumerate(subset):
            row, column = divmod(local_index, columns)
            image = Image.open(record["file"]).convert("RGB")
            image.thumbnail((thumb_width, thumb_height))
            x = column * thumb_width + (thumb_width - image.width) // 2
            y = row * (thumb_height + label_height)
            sheet.paste(image, (x, y))
            seconds = record["timestamp_seconds"]
            label = f"#{record['scene']:03d}  {int(seconds)//60:02d}:{int(seconds)%60:02d}  diff={record['difference_score']:.1f}"
            draw.text((column * thumb_width + 6, y + thumb_height + 5), label, fill="black")
        filename = output / f"contact-sheet-{sheet_index:02d}.jpg"
        sheet.save(filename, quality=90, optimize=True)
        result.append(filename.as_posix())
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path(".work/video-lessons-hd"))
    parser.add_argument("--output", type=Path, default=Path(".work/lesson-scenes"))
    parser.add_argument("--sample-seconds", type=float, default=1.0)
    parser.add_argument("--threshold", type=float, default=7.0)
    args = parser.parse_args()
    videos = sorted(args.input.glob("lesson-*.mp4"))
    if len(videos) != 3:
        raise RuntimeError(f"Expected 3 videos in {args.input}, found {len(videos)}")

    index = []
    for number, video in enumerate(videos, start=1):
        lesson_output = args.output / video.stem
        print(f"[{number}/3] {video.name}", flush=True)
        records = extract(video, lesson_output, args.sample_seconds, args.threshold)
        sheets = contact_sheets(records, lesson_output)
        print(f"  selected {len(records)} scenes in {len(sheets)} sheets", flush=True)
        index.append({
            "video": video.as_posix(),
            "scene_count": len(records),
            "scenes": records,
            "contact_sheets": sheets,
        })
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "index.json").write_text(
        json.dumps({"lessons": index}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
