import fitz
from PIL import Image
from pathlib import Path

# このプログラムが置かれているフォルダ
folder = Path(__file__).parent

# JPGの画質・解像度
zoom = 2

# フォルダ内のすべてのPDFを取得
pdf_files = list(folder.glob("*.pdf"))

if not pdf_files:
    print("PDFファイルが見つかりませんでした。")
    exit()

print(f"{len(pdf_files)}個のPDFを発見しました。\n")

# PDFを1つずつ処理
for pdf_path in pdf_files:

    print(f"変換中: {pdf_path.name}")

    # PDFを開く
    pdf = fitz.open(pdf_path)

    images = []

    # 各ページを画像に変換
    for page in pdf:

        matrix = fitz.Matrix(zoom, zoom)

        pix = page.get_pixmap(
            matrix=matrix,
            alpha=False
        )

        # PyMuPDF → PIL Image
        image = Image.frombytes(
            "RGB",
            [pix.width, pix.height],
            pix.samples
        )

        images.append(image)

    pdf.close()

    # すべてのページの横幅を統一
    max_width = max(image.width for image in images)

    # すべてのページの高さを合計
    total_height = sum(image.height for image in images)

    # 縦長のキャンバスを作成
    combined = Image.new(
        "RGB",
        (max_width, total_height),
        "white"
    )

    # ページを上から順番に配置
    y = 0

    for image in images:

        # 横方向中央揃え
        x = (max_width - image.width) // 2

        combined.paste(image, (x, y))

        y += image.height

    # PDFと同じ名前でJPGを作成
    output_path = folder / f"{pdf_path.stem}.jpg"

    # JPGとして保存
    combined.save(
        output_path,
        "JPEG",
        quality=95
    )

    print(f"  → {output_path.name}\n")

print("すべてのPDFの変換が完了しました！")