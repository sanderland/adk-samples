"""PDF processing tools for the fact checker agent."""

import PyPDF2
import requests
import tempfile
import os


def extract_pdf_text(pdf_path: str) -> dict[str, str|int|None]:
    """
    Extract text content from a PDF file or URL.

    Args:
        pdf_path: Path to the PDF file or URL

    Returns:
        Dictionary with:
        - text: Extracted text content
        - page_count: Number of pages
        - char_count: Number of characters extracted
        - error: Error message if failed
    """
    print(f"[PDF Text Extractor] Processing: {pdf_path}")

    # Check if pdf_path is a URL
    try:
        print(f"[PDF Text Extractor] Downloading PDF from URL...")
        response = requests.get(pdf_path, timeout=30)
        response.raise_for_status()

        print(f"[PDF Text Extractor] Downloaded {len(response.content)} bytes")

        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(response.content)
            temp_pdf_path = tmp_file.name

        # Extract text from downloaded PDF
        result = _extract_from_file(temp_pdf_path)

        # Clean up temporary file
        try:
            os.unlink(temp_pdf_path)
        except:
            pass

        return result

    except Exception as e:
        print(f"[PDF Text Extractor] Error downloading PDF: {str(e)}")
        return {
            "error": f"Failed to download PDF from URL: {str(e)}",
            "text": None,
            "page_count": 0,
            "char_count": 0,
        }
    else:
        # Extract text from local PDF
        return _extract_from_file(pdf_path)


def _extract_from_file(pdf_path: str):
    """Helper function to extract text from a PDF file."""
    try:
        with open(pdf_path, "rb") as file:
            return read_pdf_fh(file)
    except Exception as e:
        print(f"[PDF Text Extractor] Error opening PDF file: {str(e)}")
        return {
            "error": f"Failed to open PDF file: {str(e)}",
            "text": None,
            "page_count": 0,
            "char_count": 0,
        }



def read_pdf_fh(file) -> dict[str, str|int|None]:
    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    page_count = len(pdf_reader.pages)

    # Try to extract text from each page
    for page_num in range(page_count):
        try:
            page = pdf_reader.pages[page_num]
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        except Exception as page_error:
            print(f"[PDF Text Extractor] Error on page {page_num}: {str(page_error)}")
            continue

    # Check if we got any text
    if text.strip():
        print(f"[PDF Text Extractor] Successfully extracted {len(text)} characters from {page_count} pages")
        return {"text": text, "page_count": page_count, "char_count": len(text), "error": None}
    else:
        return {
            "error": "No text could be extracted from PDF",
            "text": None,
            "page_count": page_count,
            "char_count": 0,
        }
