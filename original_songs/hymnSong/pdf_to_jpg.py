import fitz
from PIL import Image
from pathlib import Path

# Pythonファイルがあるフォルダ
base_folder = Path(__file__).parent

# PDFが入っている1つ下のフォルダ
pdf_folder = base_folder / "hymn442-580"

# JPGの出力先
output_folder = base_folder / "jpg_output"

# jpg_outputフォルダがなければ作成
output_folder.mkdir(exist_ok=True)

# 解像度
zoom = 2

# PDFフォルダ内のすべてのPDFを取得
pdf_files = list(pdf_folder.glob("*.pdf"))

if not pdf_files:
    print(f"PDFファイルが見つかりませんでした: {pdf_folder}")
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

    # すべてのページの横幅を取得
    max_width = max(image.width for image in images)

    # すべてのページの高さを合計
    total_height = sum(image.height for image in images)

    # 縦長画像を作成
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

    # PDFと同じ名前でJPGを保存
    output_path = output_folder / f"{pdf_path.stem}.jpg"

    combined.save(
        output_path,
        "JPEG",
        quality=95
    )

    print(f"  → 保存完了: {output_path}")

print("\nすべてのPDFの変換が完了しました！")