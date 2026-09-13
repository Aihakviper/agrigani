"""
Utility helpers for the AgriGani ML service.
"""

from io import BytesIO
from pathlib import Path
from urllib.parse import unquote, urlparse

import requests
from PIL import Image


def download_image(image_url: str, timeout: int = 15) -> Image.Image:
    """Download an image URL and return it as an RGB PIL image.

    In local development Django returns localhost media URLs. If a different
    Django process owns that port during tests, we fall back to reading the
    same `/media/...` file from the backend media directory.
    """
    parsed = urlparse(image_url)

    if parsed.scheme in ("", "file"):
        return _open_local_image(unquote(parsed.path if parsed.scheme == "file" else image_url))

    try:
        response = requests.get(image_url, timeout=timeout)
        response.raise_for_status()

        content_type = response.headers.get("content-type", "")
        if content_type and not content_type.lower().startswith("image/"):
            raise ValueError(f"URL did not return an image. Content-Type: {content_type}")

        return Image.open(BytesIO(response.content)).convert("RGB")
    except requests.RequestException:
        if parsed.path.startswith("/media/"):
            media_relative_path = unquote(parsed.path.replace("/media/", "", 1))
            media_path = Path(__file__).resolve().parents[2] / "media" / media_relative_path
            if media_path.exists():
                return _open_local_image(media_path)
        raise


def _open_local_image(path) -> Image.Image:
    return Image.open(Path(path)).convert("RGB")
