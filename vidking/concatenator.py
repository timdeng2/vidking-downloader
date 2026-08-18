from __future__ import annotations

import subprocess
from pathlib import Path

from .playlist import Playlist

# downloads and concatenates video segments into a single file
class VideoConcatenator:
    def __init__(self, segments_dir: Path, output_path: Path):
        self._segments_dir = segments_dir
        self._output_path = output_path

    def concat(self, playlist: Playlist) -> Path:
        local_playlist = playlist.write_local(self._segments_dir, self._segments_dir / "local.m3u8")

        command = [
            "ffmpeg",
            "-allowed_extensions", "ALL",
            "-i", str(local_playlist),
            "-c", "copy",
            "-y",
            str(self._output_path),
        ]

        result = subprocess.run(command)
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg failed with exit code {result.returncode}")

        return self._output_path
