#!/usr/bin/env python3
"""Ingest raw video clips safely (read-only on originals) from any user folder.

Usage:
  python ingest.py <slug> <source_file_or_folder> [--out <output_dir>] [--newest N] [--no-transcribe]
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import security  # noqa: E402


def probe_clip(ffprobe: str, clip: Path) -> dict:
    cmd = [
        ffprobe, "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", str(clip),
    ]
    res = security.run_safe(cmd, timeout=60)
    data = json.loads(res.stdout)
    v_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), {})
    a_stream = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), {})
    fps_raw = v_stream.get("r_frame_rate", "30/1")
    num, _, den = fps_raw.partition("/")
    fps = round(float(num) / float(den or 1), 3) if num else 30.0
    return {
        "file": clip.name,
        "path": str(clip),
        "duration": round(float(data.get("format", {}).get("duration", 0.0)), 3),
        "width": int(v_stream.get("width", 0)),
        "height": int(v_stream.get("height", 0)),
        "fps": fps,
        "audio_channels": int(a_stream.get("channels", 0)),
        "audio_layout": a_stream.get("channel_layout", "unknown"),
    }


def detect_silences(ffmpeg: str, clip: Path, noise_db: str = "-32dB", min_dur: float = 0.35) -> list[dict]:
    cmd = [
        ffmpeg, "-hide_banner", "-i", str(clip),
        "-af", f"silencedetect=noise={noise_db}:d={min_dur}",
        "-f", "null", "-",
    ]
    res = security.run_safe(cmd, timeout=180, check=False)
    silences: list[dict] = []
    cur_start: float | None = None
    for line in res.stderr.splitlines():
        m_start = re.search(r"silence_start:\s*([0-9.]+)", line)
        if m_start:
            cur_start = float(m_start.group(1))
        m_end = re.search(r"silence_end:\s*([0-9.]+)\s*\|\s*silence_duration:\s*([0-9.]+)", line)
        if m_end and cur_start is not None:
            silences.append({
                "start": round(cur_start, 3),
                "end": round(float(m_end.group(1)), 3),
                "duration": round(float(m_end.group(2)), 3),
            })
            cur_start = None
    return silences


def make_contact_sheet(ffmpeg: str, clip: Path, out_jpg: Path) -> None:
    cmd = [
        ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(clip),
        "-vf", "fps=1/2,scale=320:-1,tile=5x4",
        "-frames:v", "1", str(out_jpg),
    ]
    security.run_safe(cmd, timeout=120, check=False)


def transcribe_local(clip: Path, model_size: str = "base") -> dict:
    if importlib.util.find_spec("faster_whisper") is None:
        return {"engine": "none", "words": [], "text": "", "note": "faster-whisper not installed; skipped"}

    from faster_whisper import WhisperModel  # type: ignore

    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments, info = model.transcribe(str(clip), word_timestamps=True)
    words: list[dict] = []
    full_text: list[str] = []
    idx = 0
    for seg in segments:
        full_text.append(seg.text.strip())
        for w in seg.words or []:
            words.append({
                "idx": idx,
                "word": security.sanitize_caption_text(w.word),
                "start": round(float(w.start), 3),
                "end": round(float(w.end), 3),
            })
            idx += 1
    return {
        "engine": f"faster-whisper:{model_size}",
        "language": getattr(info, "language", "unknown"),
        "words": words,
        "text": security.sanitize_caption_text(" ".join(full_text)),
    }


def collect_clips(source: Path, newest: int) -> tuple[Path, list[Path]]:
    if source.is_file():
        parent = source.parent
        clip = security.validate_media_file(source, [parent], kind="video")
        return parent, [clip]
    if source.is_dir():
        candidates = [
            p for p in source.iterdir()
            if p.is_file() and p.suffix.lower() in security.VIDEO_EXTENSIONS
        ]
        candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return source, candidates[:newest]
    raise security.SecurityError(f"Source path not found: {source}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Safe local ingest from any user-selected folder.")
    parser.add_argument("slug", help="Project slug")
    parser.add_argument("source", help="Path to raw video file or folder")
    parser.add_argument("--out", help="Output folder (default: <source_folder>/vidiola-edits)")
    parser.add_argument("--newest", type=int, default=5, help="Max newest clips if source is a folder")
    parser.add_argument("--no-transcribe", action="store_true", help="Skip local Whisper transcription")
    parser.add_argument("--whisper-model", default="base", help="faster-whisper model size")
    args = parser.parse_args()

    ffmpeg = security.find_binary("ffmpeg")
    ffprobe = security.find_binary("ffprobe")
    if not ffmpeg or not ffprobe:
        print("ERROR: ffmpeg and ffprobe are required on PATH.", file=sys.stderr)
        return 1

    src_path = security.is_safe_user_dir(args.source)
    source_dir, clips = collect_clips(src_path, args.newest)
    if not clips:
        print(f"ERROR: No valid video clips found in {source_dir}", file=sys.stderr)
        return 1

    slug = security.safe_slug(args.slug)
    out_root = security.is_safe_user_dir(args.out) if args.out else (source_dir / "vidiola-edits")
    proj_dir = security.safe_resolve(out_root / slug, [out_root])
    work_dir = proj_dir / "work"
    work_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "slug": slug,
        "source_dir": str(source_dir),
        "output_dir": str(out_root),
        "project_dir": str(proj_dir),
        "clips": [],
    }
    transcript_lines: list[str] = []

    for i, clip in enumerate(clips, start=1):
        cid = f"c{i}"
        info = probe_clip(ffprobe, clip)
        info["id"] = cid
        info["silences"] = detect_silences(ffmpeg, clip)
        sheet_path = work_dir / f"sheet_{cid}.jpg"
        make_contact_sheet(ffmpeg, clip, sheet_path)
        info["contact_sheet"] = str(sheet_path.relative_to(proj_dir))

        if args.no_transcribe:
            tr = {"engine": "skipped", "words": [], "text": ""}
        else:
            tr = transcribe_local(clip, model_size=args.whisper_model)
        info["transcript"] = tr
        manifest["clips"].append(info)

        transcript_lines.append(f"=== {cid}: {clip.name} ({info['duration']}s, {info['width']}x{info['height']} @ {info['fps']}fps) ===")
        if tr["words"]:
            for w in tr["words"]:
                transcript_lines.append(f"[{w['idx']:04d}] {w['start']:7.2f}s - {w['end']:7.2f}s : {w['word']}")
        else:
            transcript_lines.append(f"(no word transcript; silences: {len(info['silences'])})")
        transcript_lines.append("")

    (proj_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    (proj_dir / "transcript.txt").write_text("\n".join(transcript_lines), encoding="utf-8")
    print(f"INGEST_OK project={proj_dir} output_dir={out_root} clips={len(clips)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
