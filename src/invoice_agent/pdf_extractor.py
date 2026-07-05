from pathlib import Path
from typing import Any

import fitz  # PyMuPDF


class PDFExtractionError(Exception):
    """Raised when the invoice PDF cannot be loaded, read, or rendered."""


def validate_pdf_path(pdf_path: str | Path) -> Path:
    """
    Validate that the provided PDF path exists and points to a PDF file.

    Why this function exists:
    - The assignment expects reasonable error handling.
    - Missing or unreadable PDF attachments should produce clear messages.
    """
    path = Path(pdf_path)

    if not path.exists():
        raise PDFExtractionError(f"PDF file not found: {path}")

    if not path.is_file():
        raise PDFExtractionError(f"PDF path is not a file: {path}")

    if path.suffix.lower() != ".pdf":
        raise PDFExtractionError(f"Attachment is not a PDF file: {path}")

    return path


def extract_pdf_text_by_page(pdf_path: str | Path) -> list[dict[str, Any]]:
    """
    Extract readable text from each page of the PDF.

    This handles the normal text layer of the invoice PDF.
    """
    path = validate_pdf_path(pdf_path)

    try:
        document = fitz.open(path)
    except Exception as exc:
        raise PDFExtractionError(f"Could not open PDF file: {path}") from exc

    pages: list[dict[str, Any]] = []

    try:
        for page_index in range(document.page_count):
            page = document.load_page(page_index)
            text = page.get_text("text")

            pages.append(
                {
                    "page_number": page_index + 1,
                    "text": text.strip(),
                }
            )
    except Exception as exc:
        raise PDFExtractionError(f"Could not extract text from PDF: {path}") from exc
    finally:
        document.close()

    return pages


def render_pdf_page_to_image(
    pdf_path: str | Path,
    page_number: int = 1,
    output_dir: str | Path = "outputs/rendered_pages",
    zoom: float = 2.0,
) -> Path:
    """
    Render one PDF page to an image file.

    Why this function exists:
    - Some invoice fields may be inside an image or visual block.
    - Rendering the PDF page lets the model inspect visual content later.
    - This directly supports the image-based extraction requirement.
    """
    path = validate_pdf_path(pdf_path)

    if page_number < 1:
        raise PDFExtractionError("Page number must be 1 or greater.")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    try:
        document = fitz.open(path)

        if page_number > document.page_count:
            raise PDFExtractionError(
                f"Page {page_number} does not exist. PDF has {document.page_count} pages."
            )

        page = document.load_page(page_number - 1)
        matrix = fitz.Matrix(zoom, zoom)
        pixmap = page.get_pixmap(matrix=matrix, alpha=False)

        image_path = output_path / f"{path.stem}_page_{page_number}.png"
        pixmap.save(image_path)

    except PDFExtractionError:
        raise
    except Exception as exc:
        raise PDFExtractionError(f"Could not render PDF page to image: {path}") from exc
    finally:
        try:
            document.close()
        except Exception:
            pass

    return image_path


def extract_pdf_content(pdf_path: str | Path) -> dict[str, Any]:
    """
    Extract text content and render the first page as an image.

    The returned dictionary is a local, deterministic extraction result.
    Later, the OpenAI agent can use this as input for structured extraction.
    """
    path = validate_pdf_path(pdf_path)

    pages = extract_pdf_text_by_page(path)
    full_text = "\n\n".join(
        f"--- Page {page['page_number']} ---\n{page['text']}"
        for page in pages
    )

    first_page_image = render_pdf_page_to_image(path, page_number=1)

    return {
        "pdf_path": str(path),
        "page_count": len(pages),
        "text_by_page": pages,
        "full_text": full_text,
        "first_page_image": str(first_page_image),
    }
