import os
import sys
import fitz
from PIL import Image
import pytesseract
import io
from pypdf import PdfReader, PdfWriter


def extract_hymn_number_from_page(pdf_path, page_num, crop_box=(30, 20, 80, 45)):
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


def split_hymn_pdf(input_pdf, output_folder="output_hymns", crop_box=(30, 20, 80, 45)):
    """
    聖歌集PDFを賢く分割する
    - 番号なしページは次の番号ありページに結合
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
    
    # 曲ごとにグループ化（逆方向スキャン）
    hymn_groups = []  # [(hymn_number, [page_indices])]
    
    i = 0
    while i < total_pages:
        hymn_num = hymn_numbers[i]
        
        if hymn_num is None:
            # 番号なし = 次の番号を探す
            pending_pages = [i]
            j = i + 1
            
            # 次の番号が見つかるまでページを集める
            while j < total_pages and hymn_numbers[j] is None:
                pending_pages.append(j)
                j += 1
            
            if j < total_pages and hymn_numbers[j] is not None:
                # 次の番号が見つかった
                next_hymn = hymn_numbers[j]
                # 番号ありページを先頭に、番号なしページを後ろに
                pages_in_order = [j] + pending_pages
                hymn_groups.append((next_hymn, pages_in_order))
                i = j + 1
            else:
                # 最後まで番号が見つからない
                print(f"  [警告] ページ {i + 1}～: 対応する曲番号なし（スキップ）")
                i = j
        else:
            # 番号あり = 単独ページ
            hymn_groups.append((hymn_num, [i]))
            i += 1
    
    # PDFファイル作成
    created_files = 0
    for hymn_num, page_indices in hymn_groups:
        writer = PdfWriter()
        
        # すべてのページを追加
        for page_idx in page_indices:
            writer.add_page(reader.pages[page_idx])
        
        # ファイル名を曲番号に
        output_path = os.path.join(output_folder, f"hymn_{hymn_num}.pdf")
        
        with open(output_path, "wb") as f:
            writer.write(f)
        
        # ページ情報を表示
        if len(page_indices) == 1:
            page_info = f"ページ {page_indices[0] + 1}"
        else:
            pages_str = ", ".join(str(p + 1) for p in page_indices)
            page_info = f"ページ {pages_str} ({len(page_indices)}ページ)"
        
        print(f"  ✓ 作成: hymn_{hymn_num}.pdf ({page_info})")
        created_files += 1
    
    print()
    print(f"=== 完了 ===")
    print(f"作成したファイル数: {created_files}")
    print(f"保存先: {os.path.abspath(output_folder)}")


# ===================================
# 使い方
# ===================================
if __name__ == "__main__":
    # 基本的な使い方
    INPUT_PDF = "hymn64-98.pdf"  # ここを変更
    OUTPUT_FOLDER = "output_hymns"
    
    # 曲番号の位置（必要に応じて調整）
    CROP_BOX = (30, 20, 80, 45)
    
    # コマンドライン引数対応
    if len(sys.argv) > 1:
        INPUT_PDF = sys.argv[1]
    if len(sys.argv) > 2:
        OUTPUT_FOLDER = sys.argv[2]
    
    split_hymn_pdf(INPUT_PDF, OUTPUT_FOLDER, CROP_BOX)
    
    print("\n💡 使い方:")
    print(f"  python {os.path.basename(__file__)} <入力PDF> [出力フォルダ]")
    print(f"  例: python {os.path.basename(__file__)} hymnal.pdf my_hymns")