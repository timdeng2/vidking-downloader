from __future__ import annotations

from dataclasses import dataclass

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

PLAYLIST_MARKER = "playlist.m3u8"
SEGMENT_MARKER = "file000.html"
SEGMENT_WAIT_TIMEOUT_MS = 30000
SETTLE_TIMEOUT_MS = 2000


@dataclass
class ScrapeResult:
    playlist_text: str
    playlist_url: str
    headers: dict


class VidkingScraper:
    def __init__(self, headless: bool = True):
        self._headless = headless
        self._playwright = None
        self._browser = None
        self._context = None

    def __enter__(self) -> "VidkingScraper":
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=self._headless)
        self._context = self._browser.new_context()
        return self

    def __exit__(self, *exc_info) -> None:
        self._browser.close()
        self._playwright.stop()

    @property
    def request_context(self):
        return self._context.request

    def fetch_playlist(self, video_url: str) -> ScrapeResult:
        page = self._context.new_page()
        print(f"[+] Scraping playlist from {video_url} ...")

        playlist_text = None
        playlist_url = None
        first_segment_request = None

        def handle_response(response):
            nonlocal playlist_text, playlist_url
            if PLAYLIST_MARKER in response.url:
                playlist_text = response.body().decode("utf-8")
                playlist_url = response.url

        def handle_request(request):
            nonlocal first_segment_request
            if SEGMENT_MARKER in request.url and first_segment_request is None:
                first_segment_request = request

        page.on("response", handle_response)
        page.on("request", handle_request)

        page.goto(video_url, wait_until="domcontentloaded")

        try:
            page.wait_for_function(
                f"""
                () => window.performance.getEntriesByType('resource')
                    .some(x => x.name.includes('{SEGMENT_MARKER}'))
                """,
                timeout=SEGMENT_WAIT_TIMEOUT_MS,
            )
        except PlaywrightTimeoutError:
            pass

        page.wait_for_timeout(SETTLE_TIMEOUT_MS)
        page.close()

        if playlist_text is None:
            raise RuntimeError("No playlist.m3u8 was captured.")
        if first_segment_request is None:
            raise RuntimeError("No segment request was captured.")

        headers = first_segment_request.headers
        headers.pop("content-length", None)
        headers.pop("host", None)

        return ScrapeResult(playlist_text=playlist_text, playlist_url=playlist_url, headers=headers)
