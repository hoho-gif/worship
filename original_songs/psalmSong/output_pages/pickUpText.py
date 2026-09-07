import os
import pdfplumber
from PIL import Image
import easyocr
import io

# EasyOCR リーダーの初期化（日本語対応）
print("Loading EasyOCR model...")
reader = easyocr.Reader(['ja', 'en'], gpu=False)

def extract_region_text(pdf_path, x, y, w, h, dpi=300):
    # --- PDF ファイル存在チェック ---
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF が見つかりません: {pdf_path}")

    # --- PDF → 画像 ---
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]
        # スケール係数：DPI 300 の場合 300/72 = 4.166...
        scale = dpi / 72.0
        
        # ページ全体を画像に変換
        img = page.to_image(resolution=dpi).original

    # --- 領域を切り取る ---
    crop = img.crop((x, y, x + w, y + h))

    # 切り取り画像を保存（確認用）
    crop_path = "cropped.png"
    crop.save(crop_path)
    print(f"切り取り画像を保存しました: {crop_path}")
    print(f"切り取り画像サイズ: {crop.size}")
    
    # フルページの画像も保存（確認用）
    full_page_path = "full_page.png"
    img.save(full_page_path)
    print(f"フルページ画像を保存しました: {full_page_path}")
    print(f"フルページサイズ: {img.size}")

    # --- OCR 実行 ---
    try:
        # EasyOCR で認識
        results = reader.readtext(crop_path)
        print(f"Debug: OCR results count = {len(results)}")
        for i, item in enumerate(results):
            print(f"  [{i}] Text: '{item[1]}' (Confidence: {item[2]:.2f})")
        
        # テキストを結合
        text = "\n".join([item[1] for item in results])
        if not text.strip():
            text = "(テキストが認識されませんでした)"
    except Exception as e:
        print(f"OCR 失敗: {e}")
        text = f"(OCR 失敗: {e})"
    return text


# -----------------------------
# ★ 実行部分
# -----------------------------
if __name__ == "__main__":
    pdf_file = "psalm1.pdf"  # OCR する PDF

    # --- 抽出したい領域の座標 ---
    # 今回の「右上の 1」付近
    x, y = 1950, 135
    w, h = 380, 250  # ←幅は608じゃなく → (右端までの差分) に修正

    # OCR 実行
    result_text = extract_region_text(pdf_file, x, y, w, h)

    print("---- OCR 結果 ----")
    print(result_text)
