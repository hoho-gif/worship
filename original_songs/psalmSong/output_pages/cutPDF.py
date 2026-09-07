import fitz  # PyMuPDF
from PIL import Image
import io
import os

def extract_image_part_from_pdf(pdf_path, page_num=0, image_index=0, 
                                crop_box=(100, 100, 300, 300), output_path="cropped_part.png"):
    """
    PDFから指定画像の一部をくり抜いて保存する

    Parameters:
    - pdf_path: PDFファイルのパス
    - page_num: 対象ページ（0始まり）
    - image_index: そのページ内の何番目の画像か（0始まり）
    - crop_box: (x0, y0, x1, y1) でくり抜く領域（PDF座標系）
    - output_path: 保存先ファイル名
    """
    
    # PDFを開く
    doc = fitz.open(pdf_path)
    page = doc[page_num]
    
    # ページ内の画像リストを取得
    image_list = page.get_images(full=True)
    
    if image_index >= len(image_list):
        print(f"エラー: ページ {page_num} に {image_list} 個の画像しかありません。")
        print(f"指定された画像インデックス {image_index} は大きすぎます。")
        doc.close()
        return
    
    # 指定された画像のxref（参照ID）を取得
    xref = image_list[image_index][0]
    
    # 画像データを抽出
    base_image = doc.extract_image(xref)
    image_bytes = base_image["image"]
    image_ext = base_image["ext"]  # 例: "png", "jpeg"
    
    # BytesIOでPIL画像に変換
    image = Image.open(io.BytesIO(image_bytes))
    
    print(f"画像情報: {image.width}x{image.height}, 形式: {image.format}")
    
    # PDF座標系 → 画像ピクセル座標系に変換
    # 画像がページにどう埋め込まれているかを取得
    img_rect = page.get_image_bbox(image_list[image_index])
    
    if img_rect.is_empty:
        print("画像の位置情報が取得できませんでした。")
        doc.close()
        return
    
    # PDF座標 → 画像内ピクセル座標に変換
    def pdf_to_image_coord(pdf_x, pdf_y):
        img_x = (pdf_x - img_rect.x0) * image.width / img_rect.width
        img_y = (pdf_y - img_rect.y0) * image.height / img_rect.height
        return int(img_x), int(img_y)
    
    x0, y0 = pdf_to_image_coord(crop_box[0], crop_box[1])
    x1, y1 = pdf_to_image_coord(crop_box[2], crop_box[3])
    
    # 範囲チェック
    x0 = max(0, min(x0, image.width))
    y0 = max(0, min(y0, image.height))
    x1 = max(0, min(x1, image.width))
    y1 = max(0, min(y1, image.height))
    
    if x0 >= x1 or y0 >= y1:
        print("くり抜く領域が無効です。")
        doc.close()
        return
    
    # くり抜き
    cropped = image.crop((x0, y0, x1, y1))
    
    # 保存
    cropped.save(output_path)
    print(f"くり抜いた画像を保存しました: {output_path}")
    print(f"領域: PDF座標 {crop_box} → 画像内 {x0},{y0},{x1},{y1}")
    
    # 後片付け
    doc.close()

# ===================================
# 使い方例（ここを書き換えて実行！）
# ===================================
if __name__ == "__main__":
    PDF_FILE = "aa3.pdf"           # ← あなたのPDFファイル名
    PAGE_NUM = 0                      # ← 何ページ目？（0始まり）
    IMAGE_INDEX = 0                   # ← そのページの何番目の画像？
    CROP_BOX =   (30, 20, 80, 50) # ← (左, 上, 右, 下) のPDF座標
    OUTPUT_FILE = "cropped_image.png" # ← 保存先

    extract_image_part_from_pdf(
        pdf_path=PDF_FILE,
        page_num=PAGE_NUM,
        image_index=IMAGE_INDEX,
        crop_box=CROP_BOX,
        output_path=OUTPUT_FILE
    )