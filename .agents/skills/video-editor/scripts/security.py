"""Security helpers for local-first video editing.

Provides:
- Workspace path jailing (prevents path traversal & accidental writes outside workspace)
- Safe slug generation
- Safe subprocess execution (shell=False, explicit timeouts)
- Text sanitization for SRT/ASS/FFmpeg filtergraphs
- Disk space pre-flight checks
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Iterable, Sequence

VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm", ".m4v", ".avi"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".aac", ".m4a", ".flac", ".ogg"}


class SecurityError(ValueError):
    """Raised when a path, filename, or command violates local safety rules."""


def find_workspace_root(start: Path | None = None) -> Path:
    """Locate the workspace root containing .agents/ or inbox/."""
    cur = (start or Path.cwd()).resolve()
    for candidate in (cur, *cur.parents):
        if (candidate / ".agents").is_dir() or (candidate / "inbox").is_dir():
            return candidate
    return cur


def is_safe_user_dir(path: str | os.PathLike) -> Path:
    """Resolve a user-supplied folder/file and reject OS/system directories."""
    target = Path(path).expanduser().resolve(strict=False)
    blocked_prefixes = (
        Path("C:/Windows"),
        Path("C:/Program Files"),
        Path("C:/Program Files (x86)"),
        Path("/System"),
        Path("/usr"),
        Path("/bin"),
        Path("/sbin"),
        Path("/etc"),
    )
    for blocked in blocked_prefixes:
        try:
            target.relative_to(blocked.resolve(strict=False))
            raise SecurityError(f"System directory not allowed: {target}")
        except ValueError:
            continue
    return target


def safe_resolve(path: str | os.PathLike, allowed_roots: Iterable[Path]) -> Path:
    """Resolve `path` and verify it sits inside one of `allowed_roots`."""
    target = Path(path).expanduser().resolve(strict=False)
    for root in allowed_roots:
        resolved_root = Path(root).resolve(strict=False)
        try:
            target.relative_to(resolved_root)
            return target
        except ValueError:
            continue
    roots_str = ", ".join(str(Path(r).resolve()) for r in allowed_roots)
    raise SecurityError(f"Path '{target}' is outside allowed directories: {roots_str}")


def safe_slug(raw: str, max_len: int = 48) -> str:
    """Normalize a project or file name into a safe [a-z0-9_-] slug."""
    cleaned = re.sub(r"[^a-zA-Z0-9_-]+", "-", raw.strip().lower())
    cleaned = re.sub(r"-{2,}", "-", cleaned).strip("-_")
    if not cleaned:
        cleaned = "video-project"
    return cleaned[:max_len]


def validate_media_file(path: Path, allowed_roots: Iterable[Path], kind: str = "video") -> Path:
    """Ensure a media file exists, is inside allowed_roots, and has an expected extension."""
    resolved = safe_resolve(path, allowed_roots)
    if not resolved.is_file():
        raise SecurityError(f"Media file not found: {resolved}")
    exts = VIDEO_EXTENSIONS if kind == "video" else AUDIO_EXTENSIONS
    if resolved.suffix.lower() not in exts:
        raise SecurityError(f"Unsupported {kind} extension '{resolved.suffix}' for {resolved.name}")
    return resolved


def sanitize_caption_text(text: str) -> str:
    """Strip control characters and normalize whitespace for captions."""
    cleaned = re.sub(r"[\x00-\x1f\x7f]", " ", text)
    # Remove em-dashes per editorial style and collapse spaces
    cleaned = cleaned.replace("\u2014", " ").replace("\u2013", "-")
    return re.sub(r"\s+", " ", cleaned).strip()


def escape_ffmpeg_filter_path(path: Path) -> str:
    """Escape a file path for FFmpeg filter arguments (e.g. subtitles=...)."""
    posix = path.resolve().as_posix()
    # Escape backslashes, colons (Windows drive letters), and single quotes
    return posix.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")


def run_safe(
    argv: Sequence[str],
    cwd: Path | None = None,
    timeout: int = 600,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Execute a command with shell=False and explicit timeout."""
    if not argv:
        raise SecurityError("Empty command argv")
    proc = subprocess.run(
        list(argv),
        cwd=str(cwd) if cwd else None,
        shell=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    if check and proc.returncode != 0:
        raise RuntimeError(
            f"Command failed ({proc.returncode}): {' '.join(argv)}\n{proc.stderr[-1000:]}"
        )
    return proc


def find_binary(name: str) -> str | None:
    """Locate a binary on PATH, falling back to Windows Registry PATH if newly installed."""
    found = shutil.which(name)
    if found:
        return found
    if os.name == "nt":
        try:
            import winreg  # stdlib on Windows

            extra_dirs: list[str] = []
            for hive, subkey in (
                (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"),
                (winreg.HKEY_CURRENT_USER, r"Environment"),
            ):
                try:
                    with winreg.OpenKey(hive, subkey) as key:
                        val, _ = winreg.QueryValueEx(key, "Path")
                        extra_dirs.extend(p for p in str(val).split(";") if p.strip())
                except OSError:
                    continue
            if extra_dirs:
                search_path = os.pathsep.join(extra_dirs)
                return shutil.which(name, path=search_path)
        except Exception:
            pass
    return None


def check_disk_space(path: Path, min_gb: float = 2.0) -> tuple[bool, float]:
    """Return (ok, free_gb) for the drive hosting `path`."""
    target = path if path.exists() else path.parent
    usage = shutil.disk_usage(str(target))
    free_gb = usage.free / (1024**3)
    return free_gb >= min_gb, round(free_gb, 2)
