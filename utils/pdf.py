import base64
import io
from pathlib import Path

from pydantic import BaseModel
import pymupdf

from agent import ReadFailure


class PDFFile(BaseModel):
    filename: str
    content: str

    def __init__(self, filename: str, content: io.BytesIO | str):
        if isinstance(content, str):
            content = content
        else:
            content = pdf_to_string(content)
        super().__init__(
            filename=filename,
            content=content,
        )


def pdf_to_string(pdf_path: str | io.BytesIO) -> str:
    if isinstance(pdf_path, str):
        doc = pymupdf.open(pdf_path)
    else:
        doc = pymupdf.Document(stream=pdf_path)
    text = ""
    links = ""
    for page in doc:
        # "text" parameter haalt alleen tekst, geen afbeeldingen
        text += page.get_text("text")
        for link_dict in page.links():
            if link_dict.get("uri"):
                links += f"{link_dict['uri']}\n"

    doc.close()
    text += links
    return text


def read_pdfs_from_paths(pdf_files: list[Path]) -> str:
    # Read all PDFs
    cv_texts = ""
    for pdf_file in pdf_files:
        print(f"\nReading {pdf_file.name}...")
        text = pdf_to_string(str(pdf_file))
        cv_texts += f"[BEGIN CV]\n{text}\n[END CV]\n"

    return cv_texts


def read_pdfs_from_dir(
    dir: str | Path = "input",
) -> str | ReadFailure:
    # Define input directory
    if isinstance(dir, str):
        input_dir = Path(dir)
    else:
        input_dir = dir

    # Get all PDF files from the input directory
    pdf_files = list(input_dir.glob("*.pdf"))

    if not pdf_files:
        return ReadFailure(explanation=f"No PDF files found in {input_dir}")

    cv_texts = read_pdfs_from_paths(pdf_files)

    print(f"\nSuccessfully read {len(pdf_files)} CV(s)")

    return cv_texts
