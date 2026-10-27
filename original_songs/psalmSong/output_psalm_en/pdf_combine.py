"""
2つのPDFを1つに結合するプログラム。

使い方（どちらでもOK）:
  1) 下の設定を書き換えて実行:
         python merge_two_pdfs.py
  2) コマンドラインでファイル名を指定して実行:
         python merge_two_pdfs.py first.pdf second.pdf merged.pdf

必要なライブラリ:
    pip install pypdf
"""

import sys
from pathlib import Path

from pypdf import PdfReader, PdfWriter

# ===== 設定（コマンドライン引数を使わない場合はここを変更） =====
PDF_1 = "psalm_150B_en.pdf"    # 先に来るPDF
PDF_2 = "psalm_150B_en2.pdf"   # 後ろに付くPDF
OUTPUT = "psalm_150B_en.pdf"  # 出力ファイル名
# ================================================================


def merge_pdfs(pdf_1: Path, pdf_2: Path, output: Path) -> None:
    writer = PdfWriter()

    for pdf_path in (pdf_1, pdf_2):
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            writer.add_page(page)

    with open(output, "wb") as f:
        writer.write(f)


def main() -> None:
    if len(sys.argv) == 4:
        pdf_1, pdf_2, output = (Path(a) for a in sys.argv[1:4])
    elif len(sys.argv) == 1:
        pdf_1, pdf_2, output = Path(PDF_1), Path(PDF_2), Path(OUTPUT)
    else:
        print("使い方: python merge_two_pdfs.py <1つ目.pdf> <2つ目.pdf> <出力.pdf>")
        sys.exit(1)

    for p in (pdf_1, pdf_2):
        if not p.is_file():
            print(f"ファイルが見つかりません: {p}")
            sys.exit(1)

    merge_pdfs(pdf_1, pdf_2, output)
    print(f"{pdf_1.name} + {pdf_2.name} → {output.name} を作成しました。")


if __name__ == "__main__":
    main()