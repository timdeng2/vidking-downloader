from __future__ import annotations

import time
from pathlib import Path

from .playlist import Segment

# downloads video segments from a playlist to disk
class SegmentDownloader:
    def __init__(
        self,
        request_context,
        headers: dict,
        output_dir: Path,
        timeout_ms: int = 60000,
        max_retries: int = 5,
        retry_delay: float = 2.0,
    ):
        self._request_context = request_context
        self._headers = headers
        self._output_dir = output_dir
        self._timeout_ms = timeout_ms
        self._max_retries = max_retries
        self._retry_delay = retry_delay

    @staticmethod
    def missing(segments: list[Segment], output_dir: Path) -> list[Segment]:
        return [ segment for segment in segments
            if not (output_dir / segment.filename).exists() or (output_dir / segment.filename).stat().st_size == 0 ]

    # attempt to download each segment once. Returns the segments that failed.
    def download(self, segments: list[Segment]) -> list[Segment]:
        failed = []

        for index, segment in enumerate(segments, 1):
            print(f"[{index}/{len(segments)}] {segment.filename}")
            try:
                response = self._request_context.get(segment.url, headers=self._headers, timeout=self._timeout_ms)
                if not response.ok:
                    print(f"    [!] HTTP {response.status}: {response.status_text}")
                    failed.append(segment)
                    continue

                data = response.body()
                if not data:
                    print("     [!] Empty response")
                    failed.append(segment)
                    continue

                (self._output_dir / segment.filename).write_bytes(data)
                print(f"    [+] {len(data):,} bytes")

            except Exception as e:
                print(f"    [!] {e}")
                failed.append(segment)

        return failed

    # retry each segment individually, up to max_retries attempts, before moving to the next
    def retry_missing(self, segments: list[Segment]) -> list[Segment]:
        failed = []

        for index, segment in enumerate(segments, 1):
            print(f"[{index}/{len(segments)}] {segment.filename}")
            downloaded = False

            for attempt in range(1, self._max_retries + 1):
                print(f"    Attempt {attempt}/{self._max_retries}")
                try:
                    response = self._request_context.get(
                        segment.url, headers=self._headers, timeout=self._timeout_ms
                    )
                    if response.ok:
                        data = response.body()
                        if data:
                            (self._output_dir / segment.filename).write_bytes(data)
                            print(f"    [+] {len(data):,} bytes")
                            downloaded = True
                            break
                        print("    [!] Empty response")
                    else:
                        print(f"    [!] HTTP {response.status}: {response.status_text}")

                except Exception as e:
                    print(f"    [!] {e}")

                if attempt < self._max_retries:
                    time.sleep(self._retry_delay)

            if not downloaded:
                print(f"    [FAILED] {segment.filename}")
                failed.append(segment)

        return failed
