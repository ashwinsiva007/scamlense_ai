"""
File Processing & Multi-format Input Validation Service
-------------------------------------------------------
Validates and converts uploaded files (Images & Documents) strictly in-memory.
Supported Formats:
- Images: PNG, JPG/JPEG, WEBP, GIF (first frame), BMP, TIFF, HEIC/HEIF
- Documents: PDF (text extraction & scanned page rendering), DOCX, DOC (best effort/fallback),
             TXT, RTF, EML (RFC 822/5322 saved email)

Zero-persistence guarantee: all operations use in-memory buffers; files are never written to disk.
"""

import io
import re
import zipfile
import email
import email.policy
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Set

from PIL import Image, ImageFilter
from app.config import settings
from app.services.image_utils import ImageValidationError, compute_image_quality, MAX_IMAGE_DIMENSION

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    HEIF_AVAILABLE = True
except Exception:
    HEIF_AVAILABLE = False

try:
    from pypdf import PdfReader
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False

try:
    import fitz  # PyMuPDF
    FITZ_AVAILABLE = True
except ImportError:
    FITZ_AVAILABLE = False

try:
    import docx
    from docx.opc.constants import RELATIONSHIP_TYPE as RT
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    from striprtf.striprtf import rtf_to_text
    STRIPRTF_AVAILABLE = True
except ImportError:
    STRIPRTF_AVAILABLE = False


class FileValidationError(ImageValidationError):
    """Raised when an uploaded file fails validation (corrupt, unsupported format, or mismatch)."""
    pass


@dataclass
class ProcessedFileInput:
    document_type: Optional[str] = None
    extracted_text: str = ""
    hyperlinks: List[str] = field(default_factory=list)
    images: List[Tuple[bytes, str]] = field(default_factory=list)  # (jpeg_bytes, quality)
    sender: Optional[str] = None
    subject: Optional[str] = None
    notes: List[str] = field(default_factory=list)
    detected_format: str = "UNKNOWN"


SUPPORTED_FORMATS_MSG = (
    "Supported formats are: Images (PNG, JPG/JPEG, WEBP, GIF, BMP, TIFF, HEIC/HEIF) "
    "and Documents (PDF, DOCX, DOC, TXT, RTF, EML)."
)

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tiff", ".tif", ".heic", ".heif"}
DOC_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".rtf", ".eml"}
ALL_ALLOWED_EXTENSIONS = IMAGE_EXTENSIONS | DOC_EXTENSIONS


def regex_extract_urls_from_text(text: str) -> List[str]:
    """Finds URLs and web links in plain text."""
    pattern = r'(?:https?://[^\s<>"\'\)]+|www\.[^\s<>"\'\)]+)'
    matches = re.findall(pattern, text)
    cleaned = []
    for m in matches:
        clean = m.rstrip(".,;:!?)'\"")
        if clean and clean not in cleaned:
            cleaned.append(clean)
    return cleaned


def detect_file_type_magic(raw_bytes: bytes) -> str:
    """
    Detects the true underlying file type from magic bytes header.
    Returns format code: PNG, JPEG, GIF, WEBP, BMP, TIFF, HEIC, PDF, DOCX, DOC, RTF, EML, TXT, or UNKNOWN.
    """
    if not raw_bytes or len(raw_bytes) < 4:
        return "UNKNOWN"

    header = raw_bytes[:64]

    # 1. Images
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "PNG"
    if header.startswith(b"\xff\xd8\xff"):
        return "JPEG"
    if header.startswith(b"GIF87a") or header.startswith(b"GIF89a"):
        return "GIF"
    if len(raw_bytes) >= 12 and header.startswith(b"RIFF") and raw_bytes[8:12] == b"WEBP":
        return "WEBP"
    if header.startswith(b"BM"):
        return "BMP"
    if header.startswith(b"II*\x00") or header.startswith(b"MM\x00*"):
        return "TIFF"
    if len(raw_bytes) >= 12 and raw_bytes[4:8] == b"ftyp":
        brand = raw_bytes[8:12].lower()
        if brand in (b"heic", b"heix", b"hevc", b"heim", b"heis", b"hevm", b"hevs", b"mif1", b"msf1"):
            return "HEIC"

    # 2. PDF
    if raw_bytes[:1024].lstrip().startswith(b"%PDF-"):
        return "PDF"

    # 3. RTF
    if header.startswith(b"{\\rtf"):
        return "RTF"

    # 4. Old Word (.doc - OLE2 Compound File Binary)
    if header.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"):
        return "DOC"

    # 5. ZIP containers (DOCX vs generic ZIP)
    if header.startswith(b"PK\x03\x04"):
        try:
            with zipfile.ZipFile(io.BytesIO(raw_bytes), "r") as zf:
                names = zf.namelist()
                if "[Content_Types].xml" in names and any(n.startswith("word/") for n in names):
                    return "DOCX"
        except Exception:
            pass

    # 6. EML (RFC 822/5322 text header patterns)
    try:
        sample_str = raw_bytes[:2048].decode("utf-8", errors="ignore")
        eml_headers = ("from:", "to:", "subject:", "date:", "received:", "return-path:", "mime-version:", "content-type:")
        lines = [line.strip().lower() for line in sample_str.splitlines()[:20] if line.strip()]
        if any(any(line.startswith(h) for h in eml_headers) for line in lines):
            return "EML"
    except Exception:
        pass

    # 7. Plain text (TXT)
    try:
        # Check if valid text without binary NUL bytes
        if b"\x00" not in raw_bytes[:4096]:
            raw_bytes[:4096].decode("utf-8")
            return "TXT"
    except UnicodeDecodeError:
        try:
            raw_bytes[:4096].decode("latin-1")
            return "TXT"
        except Exception:
            pass

    return "UNKNOWN"


def validate_file_integrity_and_type(raw_bytes: bytes, filename: Optional[str] = None) -> str:
    """
    Validates magic bytes, checks for extension/content mismatch, and verifies allowed format.
    """
    if not raw_bytes or len(raw_bytes) == 0:
        raise FileValidationError("Uploaded file is empty.")

    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    if len(raw_bytes) > max_bytes:
        raise FileValidationError(
            f"File size ({len(raw_bytes) / (1024 * 1024):.2f} MB) exceeds maximum allowed limit of {settings.MAX_UPLOAD_MB} MB."
        )

    detected_type = detect_file_type_magic(raw_bytes)
    ext = (filename.rsplit(".", 1)[-1].lower() if filename and "." in filename else "").strip()
    ext_with_dot = f".{ext}" if ext else ""

    if detected_type == "UNKNOWN":
        raise FileValidationError(
            f"Unsupported image format or unreadable file. {SUPPORTED_FORMATS_MSG}"
        )

    # Validate against extension mismatch if filename was provided
    if ext_with_dot:
        # Expected types for common extensions
        ext_type_map = {
            ".png": {"PNG"},
            ".jpg": {"JPEG"},
            ".jpeg": {"JPEG"},
            ".webp": {"WEBP"},
            ".gif": {"GIF"},
            ".bmp": {"BMP"},
            ".tiff": {"TIFF"},
            ".tif": {"TIFF"},
            ".heic": {"HEIC"},
            ".heif": {"HEIC"},
            ".pdf": {"PDF"},
            ".docx": {"DOCX"},
            ".doc": {"DOC"},
            ".txt": {"TXT"},
            ".rtf": {"RTF"},
            ".eml": {"EML"},
        }
        allowed_types_for_ext = ext_type_map.get(ext_with_dot)
        if allowed_types_for_ext and detected_type not in allowed_types_for_ext:
            # Tolerant for text-like extensions (.eml, .txt) if plain text
            if not (detected_type == "TXT" and ext_with_dot in (".txt", ".eml")):
                raise FileValidationError(
                    f"Corrupt or mislabelled file: File content does not match its claimed extension (detected '{detected_type}' for '{ext_with_dot}'). Please upload a valid file."
                )

    return detected_type


def process_image_to_jpeg(img: Image.Image) -> Tuple[bytes, str]:
    """
    Strips EXIF, downscales <= MAX_IMAGE_DIMENSION, converts to RGB JPEG in memory.
    """
    # If animated / multi-frame, select frame 0
    if getattr(img, "is_animated", False) or getattr(img, "n_frames", 1) > 1:
        img.seek(0)

    quality = compute_image_quality(img)

    # Convert to RGB (normalizes RGBA, CMYK, P modes)
    if img.mode != "RGB":
        rgb_img = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
            alpha = img.convert("RGBA").split()[-1]
            rgb_img.paste(img.convert("RGB"), mask=alpha)
        else:
            rgb_img.paste(img.convert("RGB"))
        img = rgb_img

    # Downscale if width or height exceeds 1600 px
    w, h = img.size
    if w > MAX_IMAGE_DIMENSION or h > MAX_IMAGE_DIMENSION:
        scale = MAX_IMAGE_DIMENSION / max(w, h)
        img = img.resize(
            (max(1, int(w * scale)), max(1, int(h * scale))),
            Image.Resampling.LANCZOS,
        )

    out_io = io.BytesIO()
    img.save(out_io, format="JPEG", quality=85, optimize=True)
    return out_io.getvalue(), quality


def process_image_file(raw_bytes: bytes, detected_type: str) -> ProcessedFileInput:
    """Processes any supported image format."""
    try:
        img = Image.open(io.BytesIO(raw_bytes))
        img.load()
    except Exception as e:
        raise FileValidationError(f"Corrupt image file or decode failure: {e}") from e

    jpeg_bytes, quality = process_image_to_jpeg(img)
    return ProcessedFileInput(
        document_type="image",
        extracted_text="",
        hyperlinks=[],
        images=[(jpeg_bytes, quality)],
        detected_format=detected_type,
    )


def process_pdf_file(raw_bytes: bytes) -> ProcessedFileInput:
    """
    Extracts text and hyperlinks page-by-page (pypdf).
    Renders scanned or low-text pages to images (PyMuPDF).
    Limits to first 5 pages and records notes if pages are skipped.
    """
    notes = []
    hyperlinks = []
    extracted_text_pages = []
    images: List[Tuple[bytes, str]] = []

    # 1. Parse with PyPDF for text & annotations
    try:
        reader = PdfReader(io.BytesIO(raw_bytes))
    except Exception as e:
        raise FileValidationError("Corrupt or damaged PDF file. Could not read document.") from e

    total_pages = len(reader.pages)
    if total_pages == 0:
        raise FileValidationError("PDF document contains 0 pages.")

    max_pages = min(total_pages, 5)
    if total_pages > 5:
        notes.append(f"Processed first 5 pages; {total_pages - 5} pages were skipped.")

    fitz_doc = None
    if FITZ_AVAILABLE:
        try:
            fitz_doc = fitz.open(stream=raw_bytes, filetype="pdf")
        except Exception:
            fitz_doc = None

    for i in range(max_pages):
        page = reader.pages[i]
        p_text = ""
        try:
            p_text = page.extract_text() or ""
        except Exception:
            p_text = ""

        # Extract URLs from annotations
        try:
            if "/Annots" in page:
                for annot in page["/Annots"]:
                    obj = annot.get_object()
                    if "/A" in obj and "/URI" in obj["/A"]:
                        uri = str(obj["/A"]["/URI"])
                        if uri and uri not in hyperlinks:
                            hyperlinks.append(uri)
        except Exception:
            pass

        # Also extract URLs from page text
        for url in regex_extract_urls_from_text(p_text):
            if url not in hyperlinks:
                hyperlinks.append(url)

        extracted_text_pages.append(p_text.strip())

        # If page has little or no text (< 30 characters), render as image (scanned page)
        if len(p_text.strip()) < 30 and fitz_doc is not None and len(images) < 5:
            try:
                fitz_page = fitz_doc.load_page(i)
                pix = fitz_page.get_pixmap(dpi=150)
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                jpeg_bytes, quality = process_image_to_jpeg(img)
                images.append((jpeg_bytes, quality))
            except Exception:
                pass

    full_text = "\n\n".join(t for t in extracted_text_pages if t).strip()

    # If entire PDF was scanned (no text extracted at all), make sure page 1 is rendered
    if not full_text and len(images) == 0 and fitz_doc is not None:
        try:
            fitz_page = fitz_doc.load_page(0)
            pix = fitz_page.get_pixmap(dpi=150)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            jpeg_bytes, quality = process_image_to_jpeg(img)
            images.append((jpeg_bytes, quality))
        except Exception:
            pass

    return ProcessedFileInput(
        document_type="pdf",
        extracted_text=full_text,
        hyperlinks=hyperlinks,
        images=images,
        notes=notes,
        detected_format="PDF",
    )


def process_docx_file(raw_bytes: bytes) -> ProcessedFileInput:
    """
    Extracts paragraph text, tables, hyperlinks, and up to 3 embedded images.
    Enforces zip-bomb protection limits.
    """
    if not DOCX_AVAILABLE:
        raise FileValidationError("DOCX processing library is not available.")

    # 1. Zip bomb protection
    try:
        with zipfile.ZipFile(io.BytesIO(raw_bytes), "r") as zf:
            infolist = zf.infolist()
            if len(infolist) > 500:
                raise FileValidationError("DOCX file rejected: entry count exceeds security limits.")
            total_uncompressed = sum(info.file_size for info in infolist)
            if total_uncompressed > 50 * 1024 * 1024:
                raise FileValidationError("DOCX file rejected: uncompressed size exceeds security limits.")
    except zipfile.BadZipFile as bzf:
        raise FileValidationError("Corrupt or invalid DOCX archive.") from bzf

    try:
        doc = docx.Document(io.BytesIO(raw_bytes))
    except Exception as e:
        raise FileValidationError(f"Could not read DOCX document: {e}") from e

    # Extract text from paragraphs
    text_parts = [p.text.strip() for p in doc.paragraphs if p.text.strip()]

    # Extract text from tables
    for table in doc.tables:
        for row in table.rows:
            row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
            if row_text:
                text_parts.append(row_text)

    full_text = "\n".join(text_parts).strip()

    # Extract hyperlinks from relationships
    hyperlinks: List[str] = []
    try:
        for rel in doc.part.rels.values():
            if getattr(rel, "reltype", None) == RT.HYPERLINK:
                target = getattr(rel, "target_ref", "")
                if target and target.startswith("http") and target not in hyperlinks:
                    hyperlinks.append(target)
    except Exception:
        pass

    for url in regex_extract_urls_from_text(full_text):
        if url not in hyperlinks:
            hyperlinks.append(url)

    # Extract up to 3 embedded images
    images: List[Tuple[bytes, str]] = []
    try:
        for part in doc.part.related_parts.values():
            if len(images) >= 3:
                break
            content_type = getattr(part, "content_type", "")
            if content_type.startswith("image/"):
                try:
                    img = Image.open(io.BytesIO(part.blob))
                    jpeg_bytes, quality = process_image_to_jpeg(img)
                    images.append((jpeg_bytes, quality))
                except Exception:
                    pass
    except Exception:
        pass

    return ProcessedFileInput(
        document_type="document",
        extracted_text=full_text,
        hyperlinks=hyperlinks,
        images=images,
        detected_format="DOCX",
    )


def process_doc_file(raw_bytes: bytes) -> ProcessedFileInput:
    """
    Best-effort text extraction for legacy Word (.doc).
    If reliable extraction fails, returns friendly advice to save as DOCX or PDF.
    """
    # Best-effort string extraction from OLE2 binary stream
    extracted_strings = []
    try:
        # Search for ASCII and UTF-16LE text runs >= 4 characters
        ascii_runs = re.findall(rb"[\x20-\x7E\r\n\t]{4,}", raw_bytes)
        for run in ascii_runs:
            decoded = run.decode("latin-1", errors="ignore").strip()
            # Filter out binary metadata words
            if len(decoded) > 10 and not any(meta in decoded for meta in ["Root Entry", "WordDocument", "SummaryInformation"]):
                extracted_strings.append(decoded)
    except Exception:
        pass

    combined_text = "\n".join(extracted_strings).strip()
    if len(combined_text) >= 50:
        urls = regex_extract_urls_from_text(combined_text)
        return ProcessedFileInput(
            document_type="document",
            extracted_text=combined_text,
            hyperlinks=urls,
            notes=["Extracted best-effort text from legacy Word (.doc) file."],
            detected_format="DOC",
        )

    # If extraction is sparse or unreliable, return user-friendly error
    raise FileValidationError(
        "Legacy Word (.doc) format could not be reliably parsed. "
        "Please save or export your document as DOCX or PDF and try uploading again."
    )


def process_txt_file(raw_bytes: bytes) -> ProcessedFileInput:
    """Reads plain text safely with multi-encoding fallback."""
    text = ""
    for enc in ("utf-8-sig", "utf-8", "utf-16", "latin-1"):
        try:
            text = raw_bytes.decode(enc)
            break
        except UnicodeDecodeError:
            continue

    if not text.strip():
        raise FileValidationError("Text file is empty or contains no readable characters.")

    urls = regex_extract_urls_from_text(text)
    return ProcessedFileInput(
        document_type="plain_text",
        extracted_text=text.strip(),
        hyperlinks=urls,
        detected_format="TXT",
    )


def process_rtf_file(raw_bytes: bytes) -> ProcessedFileInput:
    """Strips RTF control words and extracts plain text and URLs."""
    raw_str = raw_bytes.decode("latin-1", errors="ignore")
    if STRIPRTF_AVAILABLE:
        try:
            text = rtf_to_text(raw_str)
        except Exception as e:
            raise FileValidationError(f"Could not parse RTF document: {e}") from e
    else:
        # Simple regex strip fallback
        text = re.sub(r"\\[a-zA-Z0-9\-]+ ?|[{}]", "", raw_str).strip()

    urls = regex_extract_urls_from_text(text)
    return ProcessedFileInput(
        document_type="document",
        extracted_text=text.strip(),
        hyperlinks=urls,
        detected_format="RTF",
    )


def process_eml_file(raw_bytes: bytes) -> ProcessedFileInput:
    """
    Parses RFC 822 / 5322 email file:
    Extracts sender, subject, plain text / HTML body, hyperlinks, and up to 3 image attachments.
    Never evaluates executable attachments.
    """
    try:
        msg = email.message_from_bytes(raw_bytes, policy=email.policy.default)
    except Exception as e:
        raise FileValidationError(f"Could not parse email (.eml) file: {e}") from e

    sender = str(msg.get("From", "")).strip()
    subject = str(msg.get("Subject", "")).strip()
    date = str(msg.get("Date", "")).strip()

    body_parts = []
    images: List[Tuple[bytes, str]] = []
    hyperlinks: List[str] = []

    for part in msg.walk():
        content_type = part.get_content_type()
        content_disposition = str(part.get("Content-Disposition", ""))

        if content_type == "text/plain":
            payload = part.get_payload(decode=True)
            if payload:
                charset = part.get_content_charset() or "utf-8"
                body_parts.append(payload.decode(charset, errors="ignore"))
        elif content_type == "text/html" and not body_parts:
            # If no plain text was found yet, strip HTML tags for text
            payload = part.get_payload(decode=True)
            if payload:
                charset = part.get_content_charset() or "utf-8"
                html_text = payload.decode(charset, errors="ignore")
                plain = re.sub(r"<[^>]+>", " ", html_text)
                body_parts.append(" ".join(plain.split()))

        # Image attachments (max 3)
        if part.get_content_maintype() == "image" and len(images) < 3:
            payload = part.get_payload(decode=True)
            if payload:
                try:
                    img = Image.open(io.BytesIO(payload))
                    jpeg_bytes, quality = process_image_to_jpeg(img)
                    images.append((jpeg_bytes, quality))
                except Exception:
                    pass

    body_text = "\n\n".join(body_parts).strip()

    # Compose clean email message text for the pipeline
    header_summary = []
    if sender:
        header_summary.append(f"From: {sender}")
    if subject:
        header_summary.append(f"Subject: {subject}")
    if date:
        header_summary.append(f"Date: {date}")

    full_message_text = "\n".join(header_summary) + ("\n\n" + body_text if body_text else "")
    hyperlinks.extend(regex_extract_urls_from_text(full_message_text))

    return ProcessedFileInput(
        document_type="email",
        extracted_text=full_message_text.strip(),
        hyperlinks=hyperlinks,
        images=images,
        sender=sender,
        subject=subject,
        detected_format="EML",
    )


def process_uploaded_file(raw_bytes: bytes, filename: Optional[str] = None) -> ProcessedFileInput:
    """
    Main entry point for processing any uploaded file:
    1. Validates file integrity, detects magic bytes, and enforces size limit.
    2. Routes to appropriate processor (Image, PDF, DOCX, DOC, TXT, RTF, EML).
    3. Returns standardized ProcessedFileInput with images and/or extracted text.
    """
    detected_type = validate_file_integrity_and_type(raw_bytes, filename)

    if detected_type in ("PNG", "JPEG", "GIF", "WEBP", "BMP", "TIFF", "HEIC"):
        return process_image_file(raw_bytes, detected_type)
    elif detected_type == "PDF":
        return process_pdf_file(raw_bytes)
    elif detected_type == "DOCX":
        return process_docx_file(raw_bytes)
    elif detected_type == "DOC":
        return process_doc_file(raw_bytes)
    elif detected_type == "TXT":
        return process_txt_file(raw_bytes)
    elif detected_type == "RTF":
        return process_rtf_file(raw_bytes)
    elif detected_type == "EML":
        return process_eml_file(raw_bytes)
    else:
        raise FileValidationError(
            f"Unsupported file format '{detected_type}'. {SUPPORTED_FORMATS_MSG}"
        )
