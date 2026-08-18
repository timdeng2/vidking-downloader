from __future__ import annotations

from pathlib import Path

from .concatenator import VideoConcatenator
from .downloader import SegmentDownloader
from .playlist import Playlist
from .scraper import VidkingScraper

VIDKING_EMBED_URL = "https://www.vidking.net/embed/tv/{series_id}/{season}/{episode}"
OUTPUT_ROOT = Path("output")


class VidkingPipeline:
    def __init__(self, series_id: str, season: str, episode: str, max_attempts: int = 5):
        self.video_url = VIDKING_EMBED_URL.format(series_id=series_id, season=season, episode=episode)

        series_dir = OUTPUT_ROOT / str(series_id)
        episode_name = f"S{season}E{episode}"

        self.segments_dir = series_dir / episode_name
        self.playlist_path = self.segments_dir / "playlist.m3u8"
        self.output_path = series_dir / f"{episode_name}.mp4"
        self.max_attempts = max_attempts

    # downloads segments, concats, and returns True on success
    def download(self) -> bool:
        self.segments_dir.mkdir(parents=True, exist_ok=True)

        with VidkingScraper() as scraper:
            result = scraper.fetch_playlist(self.video_url)
            playlist = Playlist(result.playlist_text, result.playlist_url)
            playlist.save(self.playlist_path)

            downloader = SegmentDownloader(
                scraper.request_context, result.headers, self.segments_dir, max_retries=self.max_attempts
            )
            success = self._download_then_retry(downloader, playlist)

        if success:
            self._concat(playlist)
        return success

    # redownloads any segments missing from a previous run, and concats on success
    def retry(self) -> bool:
        if not self.playlist_path.exists():
            raise FileNotFoundError(f"No playlist found at {self.playlist_path}; run download.py first.")

        raw_text = self.playlist_path.read_text(encoding="utf-8")
        playlist = Playlist(raw_text, self.video_url)

        if not SegmentDownloader.missing(playlist.segments, self.segments_dir):
            print("[+] All segments already present, nothing to retry.")
            self._concat(playlist)
            return True

        with VidkingScraper() as scraper:
            result = scraper.fetch_playlist(self.video_url)
            playlist = Playlist(raw_text, result.playlist_url)

            downloader = SegmentDownloader(
                scraper.request_context, result.headers, self.segments_dir, max_retries=self.max_attempts
            )
            missing = SegmentDownloader.missing(playlist.segments, self.segments_dir)
            downloader.retry_missing(missing)
            success = not SegmentDownloader.missing(playlist.segments, self.segments_dir)

        if success:
            self._concat(playlist)
        return success

    # silently download everything once, then retry whatever's still missing, one segment at a time
    def _download_then_retry(self, downloader: SegmentDownloader, playlist: Playlist) -> bool:
        missing = SegmentDownloader.missing(playlist.segments, self.segments_dir)
        downloader.download(missing)

        missing = SegmentDownloader.missing(playlist.segments, self.segments_dir)
        if missing:
            print(f"[*] Retrying {len(missing)} segment(s) individually...")
            downloader.retry_missing(missing)

        remaining = SegmentDownloader.missing(playlist.segments, self.segments_dir)
        if remaining:
            print(f"[!] {len(remaining)} segment(s) still missing after retries")

        return not remaining

    def _concat(self, playlist: Playlist) -> None:
        print("[*] Concatenating segments...")
        concatenator = VideoConcatenator(self.segments_dir, self.output_path)
        concatenator.concat(playlist)
        print(f"[+] Wrote {self.output_path}")
