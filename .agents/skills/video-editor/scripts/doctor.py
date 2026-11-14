#!/usr/bin/env python3
"""Environment diagnostic & permission-gated installer for the local video-editor skill.

Default mode is strictly read-only.
Passing `--install --yes` (only after explicit user permission) installs missing
local dependencies: ffmpeg (via winget/brew/apt) and Python packages (faster-whisper, pillow).
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import platform
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import security  # noqa: E402


def check_binary(name: str, version_arg: str = "-version") -> dict:
    path = security.find_binary(name)
    if not path:
        return {"ok": False, "path": None, "version": None}
    try:
        res = security.run_safe([path, version_arg], timeout=15, check=False)
        first_line = (res.stdout or res.stderr).splitlines()[0] if (res.stdout or res.stderr) else "unknown"
        return {"ok": res.returncode == 0, "path": path, "version": first_line.strip()}
    except Exception as exc:
        return {"ok": False, "path": path, "version": str(exc)}


def check_python_pkg(mod_name: str) -> bool:
    return importlib.util.find_spec(mod_name) is not None


def check_pyav_compatible() -> tuple[bool, str]:
    """PyAV 19+ removed metadata_errors= which faster-whisper 1.2.1 still passes."""
    if not check_python_pkg("av"):
        return False, "missing"
    try:
        import av  # type: ignore

        ver = getattr(av, "__version__", "0.0.0")
        major = int(str(ver).split(".")[0])
        if major >= 19:
            return False, ver
        # Functional smoke test: decode 0.1s of silence via faster_whisper.audio.decode_audio
        if check_python_pkg("faster_whisper"):
            import os
            import tempfile
            import wave
            from faster_whisper.audio import decode_audio  # type: ignore

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
                tmp_wav = tf.name
            try:
                with wave.open(tmp_wav, "wb") as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(16000)
                    wf.writeframes(b"\x00\x00" * 1600)
                decode_audio(tmp_wav)
            finally:
                if os.path.exists(tmp_wav):
                    os.remove(tmp_wav)
        return True, ver
    except Exception as exc:
        return False, str(exc)


def ffmpeg_install_cmd(os_name: str) -> list[str]:
    if os_name == "windows":
        return [
            "winget", "install", "--id", "Gyan.FFmpeg", "-e",
            "--accept-package-agreements", "--accept-source-agreements",
        ]
    if os_name == "darwin":
        return ["brew", "install", "ffmpeg"]
    return ["sudo", "apt-get", "install", "-y", "ffmpeg"]


def install_missing(os_name: str, missing_ffmpeg: bool, missing_py: list[str]) -> int:
    failed = False
    if missing_py:
        print(f"INSTALLING python packages: {', '.join(missing_py)}")
        try:
            security.run_safe([sys.executable, "-m", "pip", "install", *missing_py], timeout=600)
            print("STATUS python packages installed OK")
        except Exception as exc:
            print(f"ERROR installing python packages: {exc}", file=sys.stderr)
            failed = True

    if missing_ffmpeg:
        cmd = ffmpeg_install_cmd(os_name)
        print(f"INSTALLING ffmpeg via: {' '.join(cmd)}")
        try:
            security.run_safe(cmd, timeout=600)
            print("STATUS ffmpeg installed OK")
        except Exception as exc:
            print(f"ERROR installing ffmpeg automatically: {exc}", file=sys.stderr)
            print(f"MANUAL_FIX: {' '.join(cmd)}", file=sys.stderr)
            failed = True

    return 1 if failed else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnose and optionally install video-editor dependencies.")
    parser.add_argument("--install", action="store_true", help="Install missing dependencies (requires --yes)")
    parser.add_argument("--yes", action="store_true", help="Confirm user permission to install")
    parser.add_argument("--json", action="store_true", help="Print full JSON report")
    args = parser.parse_args()

    os_name = platform.system().lower()
    root = security.find_workspace_root()
    disk_ok, free_gb = security.check_disk_space(root, min_gb=2.0)

    ffmpeg = check_binary("ffmpeg")
    ffprobe = check_binary("ffprobe")
    node = check_binary("node", "--version")

    encoders_ok = False
    missing_encoders: list[str] = []
    if ffmpeg["ok"] and ffmpeg["path"]:
        enc_out = security.run_safe([ffmpeg["path"], "-hide_banner", "-encoders"], timeout=15, check=False).stdout
        for enc in ("libx264", "aac"):
            if enc not in enc_out:
                missing_encoders.append(enc)
        encoders_ok = len(missing_encoders) == 0

    pkgs = {
        "faster_whisper": check_python_pkg("faster_whisper"),
        "PIL": check_python_pkg("PIL"),
        "rembg": check_python_pkg("rembg"),
    }

    missing_ffmpeg = not (ffmpeg["ok"] and encoders_ok and ffprobe["ok"])
    av_ok, av_ver = check_pyav_compatible()
    missing_py: list[str] = []
    if not pkgs["faster_whisper"]:
        missing_py.append("faster-whisper==1.2.1")
    if not av_ok:
        missing_py.append("av>=11,<19")
    if not pkgs["PIL"]:
        missing_py.append("pillow")

    if args.install:
        if not args.yes:
            print("PERMISSION_REQUIRED: Pass --yes only after the user approves installing:")
            if missing_ffmpeg:
                print(f"  - {' '.join(ffmpeg_install_cmd(os_name))}")
            if missing_py:
                print(f"  - {sys.executable} -m pip install {' '.join(missing_py)}")
            return 2
        rc = install_missing(os_name, missing_ffmpeg, missing_py)
        if rc != 0:
            return rc
        # Re-check after install
        ffmpeg = check_binary("ffmpeg")
        ffprobe = check_binary("ffprobe")
        encoders_ok = ffmpeg["ok"]
        pkgs["faster_whisper"] = check_python_pkg("faster_whisper")
        av_ok, av_ver = check_pyav_compatible()
        pkgs["PIL"] = check_python_pkg("PIL")

    report = {
        "os": os_name,
        "python": sys.version.split()[0],
        "workspace": str(root),
        "disk_free_gb": free_gb,
        "disk_ok": disk_ok,
        "ffmpeg": ffmpeg,
        "ffmpeg_encoders_ok": encoders_ok,
        "missing_encoders": missing_encoders,
        "ffprobe": ffprobe,
        "node": node,
        "python_packages": pkgs,
    }

    print(f"STATUS workspace OK ({root})")
    print(f"STATUS disk {'OK' if disk_ok else 'LOW'} ({free_gb} GB free)")
    print(f"STATUS python OK ({report['python']})")

    if ffmpeg["ok"] and encoders_ok:
        print(f"STATUS ffmpeg OK ({ffmpeg['version']})")
    elif ffmpeg["ok"]:
        print(f"STATUS ffmpeg INCOMPLETE (missing encoders: {', '.join(missing_encoders)})")
    else:
        print(f"STATUS ffmpeg MISSING -> {' '.join(ffmpeg_install_cmd(os_name))}")

    print(f"STATUS ffprobe {'OK' if ffprobe['ok'] else 'MISSING'}")
    print(f"STATUS node {'OK (' + (node['version'] or '') + ')' if node['ok'] else 'OPTIONAL_MISSING (only needed for HyperFrames/Remotion)'}")
    print(f"STATUS faster_whisper {'OK' if pkgs['faster_whisper'] else 'MISSING -> pip install faster-whisper'}")
    print(f"STATUS pyav {'OK (' + av_ver + ')' if av_ok else 'INCOMPATIBLE (' + av_ver + ', need av<19) -> pip install \"av>=11,<19\"'}")
    print(f"STATUS pillow {'OK' if pkgs['PIL'] else 'MISSING -> pip install pillow'}")
    print(f"STATUS rembg {'OK' if pkgs['rembg'] else 'OPTIONAL_MISSING (only needed for behind-head cutout: pip install rembg onnxruntime)'}")

    core_ready = (
        ffmpeg["ok"]
        and encoders_ok
        and ffprobe["ok"]
        and disk_ok
        and pkgs["faster_whisper"]
        and av_ok
        and pkgs["PIL"]
    )
    print("READY" if core_ready else "NOT_READY")

    if args.json:
        print(json.dumps(report, indent=2))

    return 0 if core_ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
