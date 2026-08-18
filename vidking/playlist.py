from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin


@dataclass(frozen=True)
class Segment:
    url: str
    filename: str


# an m3u8 playlist of video segments
class Playlist:
    def __init__(self, raw_text: str, base_url: str):
        self.raw_text = raw_text
        self.base_url = base_url
        self.segments = self._parse(raw_text, base_url)

    @staticmethod
    def _parse(raw_text: str, base_url: str) -> list[Segment]:
        segments = []
        for line in raw_text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            url = urljoin(base_url, line)
            filename = Path(url.split("?", 1)[0]).name
            segments.append(Segment(url=url, filename=filename))
        return segments

    @classmethod
    def load(cls, path: Path, base_url: str) -> "Playlist":
        return cls(path.read_text(encoding="utf-8"), base_url)

    def save(self, path: Path) -> None:
        path.write_text(self.raw_text, encoding="utf-8")

    # write a copy of this playlist pointing at local segment filenames
    def write_local(self, segments_dir: Path, path: Path) -> Path:
        lines = []
        for line in self.raw_text.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith("#"):
                lines.append(line)
                continue

            filename = Path(line.split("?", 1)[0]).name
            local_file = segments_dir / filename
            if not local_file.exists():
                raise FileNotFoundError(f"Missing segment: {local_file}")
            if local_file.stat().st_size == 0:
                raise ValueError(f"Empty segment: {local_file}")

            lines.append(filename)

        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path
