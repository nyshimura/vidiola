#!/usr/bin/env python3
"""Automated QA check on the final rendered video.

Verifies:
1. Playable file with valid video & audio streams
2. Exact expected resolution (1080x1920 for 9:16 or 1920x1080 for 16:9) & non-zero duration
3. Extracts a frame-level contact sheet from the FINAL render for visual inspection
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import security  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run QA on a rendered video.")
    parser.add_argument("video", help="Path to rendered video")
    parser.add_argument("--format", choices=["9:16", "16:9"], default="9:16")
    parser.add_argument("--project", help="Optional project_dir to store qa_frames.jpg")
    args = parser.parse_args()

    ffmpeg = security.find_binary("ffmpeg")
    ffprobe = security.find_binary("ffprobe")
    if not ffmpeg or not ffprobe:
        print("ERROR: ffmpeg and ffprobe are required on PATH.", file=sys.stderr)
        return 1

    raw_video = security.is_safe_user_dir(args.video)
    video_path = security.validate_media_file(raw_video, [raw_video.parent], kind="video")

    probe = json.loads(
        security.run_safe(
            [ffprobe, "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", str(video_path)],
            timeout=60,
        ).stdout
    )
    v_stream = next((s for s in probe.get("streams", []) if s.get("codec_type") == "video"), None)
    a_stream = next((s for s in probe.get("streams", []) if s.get("codec_type") == "audio"), None)
    duration = float(probe.get("format", {}).get("duration", 0.0))

    exp_w, exp_h = (1080, 1920) if args.format == "9:16" else (1920, 1080)
    checks = {
        "playable_video_stream": v_stream is not None and duration > 0.2,
        "has_audio_stream": a_stream is not None,
        "exact_resolution": bool(v_stream and int(v_stream.get("width", 0)) == exp_w and int(v_stream.get("height", 0)) == exp_h),
        "frames_extracted": False,
    }

    if args.project:
        proj_dir = security.is_safe_user_dir(args.project)
        qa_dir = security.safe_resolve(proj_dir / "work", [proj_dir])
        qa_dir.mkdir(parents=True, exist_ok=True)
        qa_sheet = qa_dir / "qa_frames.jpg"
        security.run_safe([
            ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
            "-i", str(video_path),
            "-vf", "fps=1,scale=270:-1,tile=5x4",
            "-frames:v", "1", str(qa_sheet),
        ], timeout=120, check=False)
        checks["frames_extracted"] = qa_sheet.is_file()

    passed = sum(1 for v in checks.values() if v)
    print(f"QA_REPORT file={video_path.name} duration={duration:.2f}s passed={passed}/4")
    for k, v in checks.items():
        print(f"  - {k}: {'PASS' if v else 'FAIL'}")

    return 0 if checks["playable_video_stream"] and checks["exact_resolution"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
