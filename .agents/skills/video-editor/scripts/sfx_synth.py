#!/usr/bin/env python3
"""Synthesize clean, royalty-free local SFX using FFmpeg lavfi.

Used as an offline fallback when `my-sounds/` has no user-supplied SFX.
Zero network calls, zero external downloads.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import security  # noqa: E402

SFX_RECIPES = {
    "whoosh-short.wav": [
        "-f", "lavfi", "-i", "anoisesrc=d=0.35:c=pink:r=48000",
        "-af", "bandpass=f=900:w=600,afade=t=in:st=0:d=0.12,afade=t=out:st=0.15:d=0.20,volume=0.35",
    ],
    "pop.wav": [
        "-f", "lavfi", "-i", "sine=f=680:d=0.08:r=48000",
        "-af", "afade=t=in:st=0:d=0.005,afade=t=out:st=0.02:d=0.06,volume=0.45",
    ],
    "click.wav": [
        "-f", "lavfi", "-i", "sine=f=1400:d=0.03:r=48000",
        "-af", "afade=t=out:st=0.005:d=0.025,volume=0.30",
    ],
    "impact-bass.wav": [
        "-f", "lavfi", "-i", "sine=f=75:d=0.45:r=48000",
        "-af", "afade=t=in:st=0:d=0.01,afade=t=out:st=0.08:d=0.37,volume=0.50",
    ],
}


def ensure_sfx(workspace_root: Path) -> Path:
    ffmpeg = security.find_binary("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg is required to synthesize local SFX.")

    out_dir = security.safe_resolve(workspace_root / "my-sounds" / "_generated", [workspace_root])
    out_dir.mkdir(parents=True, exist_ok=True)

    for filename, args in SFX_RECIPES.items():
        target = out_dir / filename
        if target.exists():
            continue
        cmd = [ffmpeg, "-y", "-hide_banner", "-loglevel", "error", *args, "-c:a", "pcm_s16le", str(target)]
        security.run_safe(cmd, cwd=workspace_root, timeout=30)
    return out_dir


def main() -> int:
    out_arg = sys.argv[1] if len(sys.argv) > 1 else None
    if out_arg:
        out_dir = security.is_safe_user_dir(out_arg)
        out_dir.mkdir(parents=True, exist_ok=True)
        ffmpeg = security.find_binary("ffmpeg")
        if not ffmpeg:
            raise RuntimeError("ffmpeg is required to synthesize local SFX.")
        for filename, args in SFX_RECIPES.items():
            target = out_dir / filename
            if not target.exists():
                cmd = [ffmpeg, "-y", "-hide_banner", "-loglevel", "error", *args, "-c:a", "pcm_s16le", str(target)]
                security.run_safe(cmd, cwd=out_dir, timeout=30)
    else:
        root = security.find_workspace_root()
        out_dir = ensure_sfx(root)
    print(f"STATUS local SFX ready at {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

