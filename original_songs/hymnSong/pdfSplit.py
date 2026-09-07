import os
import sys
import argparse

try:
    from pypdf import PdfReader, PdfWriter
except Exception:
    try:
        from PyPDF2 import PdfReader, PdfWriter
    except Exception:
        print(
            "Dependency missing: install 'pypdf' (recommended) or 'PyPDF2'.\nRun: pip install pypdf"
        )
        sys.exit(1)


def split_pages(reader: PdfReader, output_folder: str) -> tuple[int, str]:
    """Split PDF into 1-page PDFs."""
    total = len(reader.pages)

    for i, page in enumerate(reader.pages, start=1):
        writer = PdfWriter()
        writer.add_page(page)
        output_path = os.path.join(output_folder, f"hymn{i}.pdf")
        with open(output_path, "wb") as f:
            writer.write(f)

    return total, output_folder


def split_two_pages(reader: PdfReader, output_folder: str) -> tuple[int, str]:
    """Split PDF into 2-page PDFs (last one may be 1 page)."""
    total = len(reader.pages)
    page_num = 1

    i = 0
    while i < total:
        writer = PdfWriter()

        # 1ページ目
        writer.add_page(reader.pages[i])

        # 2ページ目（存在すれば）
        if i + 1 < total:
            writer.add_page(reader.pages[i + 1])

        output_path = os.path.join(output_folder, f"hymn{page_num}.pdf")
        with open(output_path, "wb") as f:
            writer.write(f)

        page_num += 2
        i += 2

    return total, output_folder


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Split a PDF into 1-page or 2-page PDFs"
    )
    parser.add_argument("input", help="Path to input PDF (e.g. psalm1-49.pdf)")
    parser.add_argument("-o", "--out", help="Output folder")
    parser.add_argument(
        "--mode",
        choices=["1", "2"],
        default="1",
        help="Split mode: '1' = single page, '2' = two pages per PDF (default: 1)",
    )
    args = parser.parse_args()

    input_path = args.input
    output_folder = args.out

    try:
        if not os.path.isfile(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")

        if output_folder is None:
            output_folder = os.path.join(
                os.path.dirname(os.path.abspath(input_path)), "output_pages"
            )

        os.makedirs(output_folder, exist_ok=True)

        reader = PdfReader(input_path)

        if args.mode == "1":
            total, out = split_pages(reader, output_folder)
        else:
            total, out = split_two_pages(reader, output_folder)

        print(f"Saved {total} pages to: {out}")

    except Exception as e:
        print("Error:", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
