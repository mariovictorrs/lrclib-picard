"""Utilities for writing LRCLIB lyrics as sidecar LRC files."""

from pathlib import Path
import shutil


def lrc_path_for(audio_filename):
    """Return the sidecar LRC path for an audio file."""
    return Path(audio_filename).with_suffix(".lrc")


def write_lrc_file(audio_filename, lyrics, overwrite):
    """Write lyrics as UTF-8 LRC text and return whether a file was written."""
    lrc_path = lrc_path_for(audio_filename)
    if lrc_path.exists() and not overwrite:
        return False

    contents = lyrics if lyrics.endswith("\n") else lyrics + "\n"
    with lrc_path.open("w", encoding="utf-8", newline="\n") as lrc_file:
        lrc_file.write(contents)
    return True


def move_lrc_file(source_path, destination_path, overwrite):
    """Move a sidecar LRC file, preserving a conflicting destination if requested."""
    source_path = Path(source_path)
    destination_path = Path(destination_path)
    if not source_path.exists() or source_path == destination_path:
        return False
    if destination_path.exists():
        if not overwrite:
            return False
        destination_path.unlink()

    shutil.move(str(source_path), str(destination_path))
    return True
