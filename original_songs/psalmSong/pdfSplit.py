import os
import sys
import argparse

try:
    from pypdf import PdfReader, PdfWriter
except Exception:
    try:
        from PyPDF2 import PdfReader, PdfWriter
    except Exception:
        print("Dependency missing: install 'pypdf' (recommended) or 'PyPDF2'.\nRun: pip install pypdf")
        sys.exit(1)


def split_pdf(input_path: str, output_folder: str | None = None) -> tuple[int, str]:
    """Split the PDF at `input_path` into single-page PDFs in `output_folder`.

    Returns (total_pages, output_folder).
    """
    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    if output_folder is None:
        output_folder = os.path.join(os.path.dirname(os.path.abspath(input_path)), "output_pages")

    os.makedirs(output_folder, exist_ok=True)

    reader = PdfReader(input_path)
    total = len(reader.pages)

    for i, page in enumerate(reader.pages, start=1):
        writer = PdfWriter()
        writer.add_page(page)
        output_path = os.path.join(output_folder, f"psalm{i}.pdf")
        with open(output_path, "wb") as f:
            writer.write(f)

    return total, output_folder


def main() -> None:
    parser = argparse.ArgumentParser(description="Split a PDF into single-page PDFs")
    parser.add_argument("input", help="Path to input PDF (e.g. psalm1-49.pdf)")
    parser.add_argument("-o", "--out", help="Output folder (default: input file's folder/output_pages)")
    args = parser.parse_args()

    try:
        total, out = split_pdf(args.input, args.out)
        print(f"Saved {total} pages to: {out}")
    except Exception as e:
        print("Error:", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
