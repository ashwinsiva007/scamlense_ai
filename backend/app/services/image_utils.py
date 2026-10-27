"""
Image Processing & Input Validation Service
-------------------------------------------
Validates uploaded image binaries strictly in-memory using Pillow.
Strips metadata, normalizes to RGB JPEG, downscales large dimensions,
and computes a deterministic image quality heuristic.
Never writes uploads to disk and never logs image data.
"""

import io
from typing import Tuple
from PIL import Image, ImageFilter, ImageOps
from app.config import settings


class ImageValidationError(Exception):
    """Raised when an uploaded image fails validation (corrupt, unsupported format, animated, or oversize)."""
    pass


ALLOWED_FORMATS = {"JPEG", "JPG", "PNG", "WEBP", "GIF", "BMP", "TIFF", "MPO"}
MAX_IMAGE_DIMENSION = 1600


def compute_image_quality(img: Image.Image) -> str:
    """
    Computes an image_quality rating (high | medium | low) based on resolution
    and a sharpness heuristic using only Pillow and the standard library.
    """
    width, height = img.size

    # Severe low-resolution check
    if width < 250 or height < 150:
        return "low"

    # Edge variance heuristic for sharpness / blur detection
    gray = img.convert("L")
    # Subsample if image is very large for fast edge variance computation
    if width > 800 or height > 800:
      scale = 800.0 / max(width, height)
      gray = gray.resize(
          (max(1, int(width * scale)), max(1, int(height * scale))),
          Image.Resampling.BILINEAR,
      )

    edges = gray.filter(ImageFilter.FIND_EDGES)
    pixels = list(edges.getdata())
    n = len(pixels)
    if n == 0:
        return "low"

    mean = sum(pixels) / n
    variance = sum((x - mean) ** 2 for x in pixels) / n

    # Low variance indicates severe blurriness or a blank screen
    if variance < 40 or width < 350 or height < 250:
        return "low"
    elif variance < 180 or width < 600 or height < 400:
        return "medium"
    else:
        return "high"


def validate_and_process_image(
    raw_bytes: bytes,
    max_upload_mb: int = settings.MAX_UPLOAD_MB,
) -> Tuple[bytes, str]:
    """
    Validates and processes raw image bytes strictly in memory:
    1. Checks payload size against max_upload_mb.
    2. Decodes image with Pillow to ensure file integrity.
    3. Verifies format is strictly JPEG, PNG, or WebP.
    4. Rejects animated files (animated GIFs / animated WebP).
    5. Computes quality rating (high | medium | low).
    6. Strips EXIF metadata, converts to RGB, downscales longest side <= 1600 px.
    7. Re-encodes as optimized JPEG in memory.

    :param raw_bytes: Raw binary image content.
    :param max_upload_mb: Maximum allowed file size in MB.
    :return: Tuple of (processed_jpeg_bytes, image_quality_rating).
    """
    if not raw_bytes or len(raw_bytes) == 0:
        raise ImageValidationError("Uploaded image file is empty.")

    max_bytes = max_upload_mb * 1024 * 1024
    if len(raw_bytes) > max_bytes:
        raise ImageValidationError(
            f"Image payload size ({len(raw_bytes) / (1024 * 1024):.2f} MB) exceeds maximum allowed limit of {max_upload_mb} MB."
        )

    # 1. Integrity check with verify()
    try:
        verify_img = Image.open(io.BytesIO(raw_bytes))
        verify_img.verify()
    except Exception as e:
        raise ImageValidationError("Corrupt, damaged, or unreadable image file.") from e

    # 2. Re-open stream for decoding and processing
    try:
        img = Image.open(io.BytesIO(raw_bytes))
    except Exception as e:
        raise ImageValidationError("Unable to decode image content.") from e

    # 3. Format check
    detected_format = (img.format or "").upper()
    if detected_format not in ALLOWED_FORMATS:
        raise ImageValidationError(
            f"Unsupported image format '{detected_format}'. Allowed formats are JPEG, PNG, and WebP."
        )

    # 4. Check for animated images
    is_animated = getattr(img, "is_animated", False)
    n_frames = getattr(img, "n_frames", 1)
    if is_animated or n_frames > 1:
        raise ImageValidationError("Animated images (multi-frame WebP/GIF) are not supported.")

    # 5. Compute image quality before downscaling
    quality_rating = compute_image_quality(img)

    # 6. Correct EXIF orientation (handles rotated mobile camera / screenshot captures)
    try:
        oriented_img = ImageOps.exif_transpose(img) or img
    except Exception:
        oriented_img = img

    # 7. Convert to RGB (strips color profile / transparency / EXIF metadata)
    rgb_img = oriented_img.convert("RGB")

    # 8. Downscale if longest dimension exceeds 1600 px
    w, h = rgb_img.size
    if max(w, h) > MAX_IMAGE_DIMENSION:
        scale = MAX_IMAGE_DIMENSION / float(max(w, h))
        new_w = max(1, int(w * scale))
        new_h = max(1, int(h * scale))
        rgb_img = rgb_img.resize((new_w, new_h), Image.Resampling.LANCZOS)

    # 9. Re-encode as JPEG in memory
    out_buffer = io.BytesIO()
    rgb_img.save(out_buffer, format="JPEG", quality=88, optimize=True)
    processed_bytes = out_buffer.getvalue()

    return processed_bytes, quality_rating
