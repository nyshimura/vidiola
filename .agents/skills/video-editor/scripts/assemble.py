#!/usr/bin/env python3
"""Assemble an EDL (edl.json) into a clean 30fps CFR video inside the user's output folder.

Originals in the user's source folder are never modified.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import security  # noqa: E402


def fmt_srt_time(seconds: float) -> str:
    ms_total = max(0, int(round(seconds * 1000)))
    hrs, rem = divmod(ms_total, 3600000)
    mins, rem = divmod(rem, 60000)
    secs, ms = divmod(rem, 1000)
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{ms:03d}"


def build_segment_filter(zoom: float, cx: float, cy: float, target_w: int, target_h: int) -> str:
    zoom = max(1.0, min(3.0, float(zoom)))
    cx = max(0.0, min(1.0, float(cx)))
    cy = max(0.0, min(1.0, float(cy)))
    return (
        f"fps=30,scale=w={int(target_w * zoom)}:h={int(target_h * zoom)}:force_original_aspect_ratio=increase,"
        f"crop=w={target_w}:h={target_h}:x='(iw-ow)*{cx:.3f}':y='(ih-oh)*{cy:.3f}',setsar=1"
    )


def write_srt(segments: list[dict], srt_path: Path) -> None:
    lines: list[str] = []
    cursor = 0.0
    idx = 1
    for seg in segments:
        dur = max(0.0, float(seg["out"]) - float(seg["in"]))
        text = security.sanitize_caption_text(str(seg.get("line", "")))
        if text and dur > 0.05:
            lines.append(str(idx))
            lines.append(f"{fmt_srt_time(cursor)} --> {fmt_srt_time(cursor + dur)}")
            lines.append(text)
            lines.append("")
            idx += 1
        cursor += dur
    srt_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Assemble edl.json into draft/final MP4.")
    parser.add_argument("project_dir", help="Path to project folder created by ingest.py (e.g. .../vidiola-edits/<slug>)")
    parser.add_argument("--format", choices=["9:16", "16:9"], default="9:16")
    parser.add_argument("--burn-captions", action="store_true", help="Burn captions.srt into output video")
    parser.add_argument("--version", default="v1", help="Output suffix (e.g. v1, v2, final)")
    args = parser.parse_args()

    ffmpeg = security.find_binary("ffmpeg")
    if not ffmpeg:
        print("ERROR: ffmpeg is required on PATH.", file=sys.stderr)
        return 1

    proj_dir = security.is_safe_user_dir(args.project_dir)
    edl_path = proj_dir / "edl.json"
    manifest_path = proj_dir / "manifest.json"
    if not edl_path.is_file() or not manifest_path.is_file():
        print("ERROR: Both manifest.json and edl.json are required in project_dir.", file=sys.stderr)
        return 1

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    edl = json.loads(edl_path.read_text(encoding="utf-8"))
    slug = security.safe_slug(manifest.get("slug", proj_dir.name))
    source_dir = security.is_safe_user_dir(manifest["source_dir"])
    out_root = security.is_safe_user_dir(manifest.get("output_dir", str(proj_dir.parent)))

    clip_map = {c["id"]: c for c in manifest.get("clips", [])}
    allowed_media = [source_dir, proj_dir]

    target_w, target_h = (1080, 1920) if args.format == "9:16" else (1920, 1080)
    work_dir = proj_dir / "work"
    seg_dir = work_dir / "segs"
    seg_dir.mkdir(parents=True, exist_ok=True)

    seg_files: list[Path] = []
    for i, seg in enumerate(edl):
        cid = seg["clip"]
        if cid not in clip_map:
            raise security.SecurityError(f"Unknown clip id in edl.json: {cid}")
        src = security.validate_media_file(Path(clip_map[cid]["path"]), allowed_media, kind="video")
        t_in = float(seg["in"])
        t_out = float(seg["out"])
        if t_out <= t_in:
            raise ValueError(f"Invalid segment {i}: out ({t_out}) <= in ({t_in})")

        vf = build_segment_filter(seg.get("zoom", 1.0), seg.get("cx", 0.5), seg.get("cy", 0.5), target_w, target_h)
        af = "pan=stereo|c0=c0|c1=c0,aresample=48000" if clip_map[cid].get("audio_channels", 2) == 1 else "aresample=48000"
        out_seg = seg_dir / f"seg_{i:03d}.mp4"
        cmd = [
            ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
            "-ss", f"{t_in:.3f}", "-to", f"{t_out:.3f}", "-i", str(src),
            "-vf", vf, "-af", af,
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
            "-c:a", "aac", "-b:a", "192k", "-ac", "2",
            str(out_seg),
        ]
        security.run_safe(cmd, cwd=proj_dir, timeout=300)
        seg_files.append(out_seg)

    concat_txt = work_dir / "concat.txt"
    concat_txt.write_text("\n".join(f"file '{p.as_posix()}'" for p in seg_files), encoding="utf-8")

    aroll_path = work_dir / "aroll.mp4"
    security.run_safe([
        ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", str(concat_txt),
        "-c:v", "copy", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
        "-c:a", "aac", "-b:a", "192k",
        str(aroll_path),
    ], cwd=proj_dir, timeout=300)

    srt_path = work_dir / "captions.srt"
    write_srt(edl, srt_path)

    out_root.mkdir(parents=True, exist_ok=True)
    ver_slug = security.safe_slug(args.version)
    final_out = security.safe_resolve(out_root / f"{slug}-{ver_slug}.mp4", [out_root])

    if args.burn_captions and srt_path.read_text(encoding="utf-8").strip():
        escaped_srt = security.escape_ffmpeg_filter_path(srt_path)
        margin_v = 480 if args.format == "9:16" else 60
        style = f"FontName=Arial,FontSize=18,Bold=1,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2,MarginV={margin_v}"
        security.run_safe([
            ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
            "-i", str(aroll_path),
            "-vf", f"subtitles='{escaped_srt}':force_style='{style}'",
            "-c:v", "libx264", "-preset", "medium", "-crf", "18",
            "-c:a", "copy", str(final_out),
        ], cwd=proj_dir, timeout=600)
    else:
        shutil.copy2(aroll_path, final_out)

    print(f"ASSEMBLE_OK output={final_out} segments={len(seg_files)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
