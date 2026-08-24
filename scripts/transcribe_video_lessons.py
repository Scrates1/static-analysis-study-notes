#!/usr/bin/env python3
"""Create timestamped working transcripts for the three YASA lesson videos.

Run with the repository virtual environment after installing faster-whisper:
    .venv/bin/python scripts/transcribe_video_lessons.py

The output is research material used to produce paraphrased study notes; it is not
intended as an official or verbatim transcript.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from faster_whisper import WhisperModel

PROMPT = (
    "这是一门中文研究生课程《静态程序分析原理与实践》的 YASA 实验课。"
    "技术词包括 YASA、YASA-Engine、UAST、Unified Abstract Syntax Tree、"
    "Checker、UQL、AST、CFG、Call Graph、Data Flow、Taint Analysis、Source、"
    "Sink、Sanitizer、JSON、symbol、symbol table、preprocess、interpretation、"
    "flow-sensitive、context-sensitive、path-sensitive、field-sensitive。"
)


def timestamp(seconds: float) -> str:
    milliseconds = round(seconds * 1000)
    hours, milliseconds = divmod(milliseconds, 3_600_000)
    minutes, milliseconds = divmod(milliseconds, 60_000)
    secs, milliseconds = divmod(milliseconds, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{milliseconds:03d}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path(".work/video-lessons"))
    parser.add_argument("--output", type=Path, default=Path(".work/transcripts"))
    parser.add_argument("--model", default="large-v3-turbo")
    parser.add_argument("--threads", type=int, default=24)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    print(f"Loading {args.model} on CPU (int8, {args.threads} threads)", flush=True)
    model = WhisperModel(
        args.model,
        device="cpu",
        compute_type="int8",
        cpu_threads=args.threads,
        num_workers=1,
    )
    videos = sorted(args.input.glob("lesson-*.mp4"))
    if len(videos) != 3:
        raise RuntimeError(f"Expected 3 videos in {args.input}, found {len(videos)}")

    for index, video in enumerate(videos, start=1):
        print(f"[{index}/3] Transcribing {video.name}", flush=True)
        segments_iterator, info = model.transcribe(
            str(video),
            language="zh",
            task="transcribe",
            beam_size=5,
            temperature=0.0,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 500},
            initial_prompt=PROMPT,
            condition_on_previous_text=True,
        )
        segments = []
        markdown = [
            f"# 工作转写：{video.stem}",
            "",
            "> 自动语音识别结果，仅用于知识整理；技术名词和代码必须与仓库/画面交叉核验。",
            "",
        ]
        for segment in segments_iterator:
            record = {
                "id": segment.id,
                "start": segment.start,
                "end": segment.end,
                "text": segment.text.strip(),
                "avg_logprob": segment.avg_logprob,
                "no_speech_prob": segment.no_speech_prob,
            }
            segments.append(record)
            markdown.append(
                f"- `{timestamp(segment.start)}–{timestamp(segment.end)}` {record['text']}"
            )
        payload = {
            "video": video.as_posix(),
            "model": args.model,
            "detected_language": info.language,
            "language_probability": info.language_probability,
            "duration": info.duration,
            "duration_after_vad": info.duration_after_vad,
            "segments": segments,
        }
        stem = args.output / video.stem
        stem.with_suffix(".json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        stem.with_suffix(".md").write_text("\n".join(markdown) + "\n", encoding="utf-8")
        print(f"Wrote {stem.with_suffix('.md')} ({len(segments)} segments)", flush=True)


if __name__ == "__main__":
    main()
