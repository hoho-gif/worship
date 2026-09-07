import os
import sys
import fitz
from PIL import Image
import pytesseract
import io
from pypdf import PdfReader, PdfWriter


def extract_hymn_number_from_page(pdf_path, page_num, crop_box=(20, 10, 60, 30)):
    """
    指定ページから曲番号を読み取る
    Returns: 曲番号(str) or None
    """
    try:
        doc = fitz.open(pdf_path)
        page = doc[page_num]
        
        image_list = page.get_images(full=True)
        if len(image_list) == 0:
            doc.close()
            return None
        
        # 最初の画像から曲番号を抽出
        xref = image_list[0][0]
        base_image = doc.extract_image(xref)
        image_bytes = base_image["image"]
        
        image = Image.open(io.BytesIO(image_bytes))
        img_rect = page.get_image_bbox(image_list[0])
        
        if img_rect.is_empty:
            doc.close()
            return None
        
        # PDF座標 → 画像ピクセル座標に変換
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
            doc.close()
            return None
        
        # くり抜き
        cropped = image.crop((x0, y0, x1, y1))
        
        # OCRで数字を読み取り
        text = pytesseract.image_to_string(
            cropped, 
            config="--psm 6 outputbase digits"
        ).strip()
        
        doc.close()
        
        # 数字が読み取れた場合のみ返す
        if text and text.isdigit():
            return text
        return None
        
    except Exception as e:
        print(f"  [警告] ページ {page_num + 1} の読み取りエラー: {e}")
        return None


def get_unique_filename(base_path):
    """
    既存ファイルがある場合、番号を付けてユニークなファイル名を生成
    例: hymn_123.pdf → hymn_123_1.pdf → hymn_123_2.pdf
    """
    if not os.path.exists(base_path):
        return base_path
    
    # ファイル名と拡張子を分離
    directory = os.path.dirname(base_path)
    filename = os.path.basename(base_path)
    name, ext = os.path.splitext(filename)
    
    # 番号を付けて試す
    counter = 1
    while True:
        new_path = os.path.join(directory, f"{name}_{counter}{ext}")
        if not os.path.exists(new_path):
            return new_path
        counter += 1


def split_hymn_pdf(input_pdf, output_folder="output_hymns", crop_box=(30, 20, 80, 45), 
                   overwrite_mode="rename"):
    """
    聖歌集PDFを賢く分割する
    
    Args:
        overwrite_mode: 上書き動作
            - "rename": 既存ファイルがある場合、番号を付ける (デフォルト)
            - "skip": 既存ファイルがある場合、スキップする
            - "overwrite": 既存ファイルを上書きする
    """
    
    if not os.path.isfile(input_pdf):
        print(f"エラー: ファイルが見つかりません: {input_pdf}")
        return
    
    # 出力フォルダ作成
    os.makedirs(output_folder, exist_ok=True)
    
    # PDFを読み込み
    reader = PdfReader(input_pdf)
    total_pages = len(reader.pages)
    
    print(f"=== 聖歌集分割開始 ===")
    print(f"入力PDF: {input_pdf}")
    print(f"総ページ数: {total_pages}")
    print(f"出力先: {output_folder}")
    print(f"上書きモード: {overwrite_mode}")
    print()
    
    # 全ページの曲番号を読み取り
    print("📖 曲番号を読み取り中...")
    hymn_numbers = []
    for i in range(total_pages):
        hymn_num = extract_hymn_number_from_page(input_pdf, i, crop_box)
        hymn_numbers.append(hymn_num)
        status = hymn_num if hymn_num else "なし"
        print(f"  ページ {i + 1}: 曲番号 {status}")
    
    print()
    print("✂️  PDF分割中...")
    
    # 賢く分割
    i = 0
    created_files = 0
    skipped_files = 0
    
    while i < total_pages:
        current_hymn = hymn_numbers[i]
        
        # 曲番号がないページはスキップ
        if current_hymn is None:
            print(f"  [スキップ] ページ {i + 1}: 曲番号なし")
            i += 1
            continue
        
        # 次のページをチェック
        is_two_page = False
        if i + 1 < total_pages:
            next_hymn = hymn_numbers[i + 1]
            # 次のページに曲番号がない = 2ページ構成
            if next_hymn is None:
                is_two_page = True
        
        # ファイル名を曲番号に
        base_output_path = os.path.join(output_folder, f"hymn_{current_hymn}.pdf")
        
        # 上書きモードに応じた処理
        if overwrite_mode == "skip" and os.path.exists(base_output_path):
            page_info = f"ページ {i + 1}-{i + 2}" if is_two_page else f"ページ {i + 1}"
            print(f"  [既存] hymn_{current_hymn}.pdf ({page_info}) - スキップ")
            skipped_files += 1
            i += 2 if is_two_page else 1
            continue
        elif overwrite_mode == "rename":
            output_path = get_unique_filename(base_output_path)
        else:  # overwrite
            output_path = base_output_path
        
        # PDF作成
        writer = PdfWriter()
        writer.add_page(reader.pages[i])
        
        if is_two_page:
            writer.add_page(reader.pages[i + 1])
            page_info = f"ページ {i + 1}-{i + 2}"
        else:
            page_info = f"ページ {i + 1}"
        
        with open(output_path, "wb") as f:
            writer.write(f)
        
        output_filename = os.path.basename(output_path)
        print(f"  ✓ 作成: {output_filename} ({page_info})")
        created_files += 1
        
        # 次のページへ
        if is_two_page:
            i += 2
        else:
            i += 1
    
    print()
    print(f"=== 完了 ===")
    print(f"作成したファイル数: {created_files}")
    if skipped_files > 0:
        print(f"スキップしたファイル数: {skipped_files}")
    print(f"保存先: {os.path.abspath(output_folder)}")


# ===================================
# 使い方
# ===================================
if __name__ == "__main__":
    # 基本的な使い方
    INPUT_PDF = "newHymn1-521.pdf"  # ここを変更
    OUTPUT_FOLDER = "output_hymns"
    
    # 曲番号の位置（必要に応じて調整）
    CROP_BOX = (20, 10, 60, 30)
    
    # 上書きモード
    # "rename" = 番号を付ける (デフォルト)
    # "skip" = 既存ファイルをスキップ
    # "overwrite" = 上書きする
    OVERWRITE_MODE = "rename"
    
    # コマンドライン引数対応
    if len(sys.argv) > 1:
        INPUT_PDF = sys.argv[1]
    if len(sys.argv) > 2:
        OUTPUT_FOLDER = sys.argv[2]
    if len(sys.argv) > 3:
        OVERWRITE_MODE = sys.argv[3]
    
    split_hymn_pdf(INPUT_PDF, OUTPUT_FOLDER, CROP_BOX, OVERWRITE_MODE)
    
    print("\n💡 使い方:")
    print(f"  python {os.path.basename(__file__)} <入力PDF> [出力フォルダ] [モード]")
    print(f"  例: python {os.path.basename(__file__)} hymnal.pdf my_hymns rename")
    print(f"  モード: rename (番号付与) / skip (スキップ) / overwrite (上書き)")